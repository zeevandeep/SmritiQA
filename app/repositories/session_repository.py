"""
Session repository for database operations related to user sessions.
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Session, MigrationError
from app.schemas.schemas import SessionCreate
from app.utils.encryption import encrypt_data, decrypt_data, EncryptionError

logger = logging.getLogger(__name__)


def get_session(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Get a session by ID with automatic decryption.
    
    Args:
        db: Database session.
        session_id: ID of the session to retrieve.
        
    Returns:
        Session object if found, None otherwise.
    """
    db_session = db.query(Session).filter(Session.id == session_id).first()
    
    if db_session and db_session.is_encrypted and db_session.raw_transcript:
        try:
            user_id = str(db_session.user_id)
            db_session.raw_transcript = decrypt_data(db_session.raw_transcript, user_id)
        except EncryptionError as e:
            logger.error(f"Failed to decrypt session {session_id} for user {user_id}: {e}")
            _log_migration_error(db, db_session.user_id, session_id, "decryption_failed", str(e))
            # Return None to indicate the session is corrupted
            return None
    
    return db_session


def get_user_sessions(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Session]:
    """
    Get sessions for a user with automatic decryption.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of sessions to skip.
        limit: Maximum number of sessions to return.
        
    Returns:
        List of Session objects.
    """
    sessions = db.query(Session)\
        .filter(Session.user_id == user_id)\
        .order_by(Session.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Decrypt encrypted sessions
    decrypted_sessions = []
    for session in sessions:
        if session.is_encrypted and session.raw_transcript:
            try:
                session.raw_transcript = decrypt_data(session.raw_transcript, str(user_id))
                decrypted_sessions.append(session)
            except EncryptionError as e:
                logger.error(f"Failed to decrypt session {session.id} for user {user_id}: {e}")
                _log_migration_error(db, user_id, session.id, "decryption_failed", str(e))
                # Skip corrupted sessions
                continue
        else:
            decrypted_sessions.append(session)
    
    return decrypted_sessions


def create_session(db: DbSession, session: SessionCreate) -> Session:
    """
    Create a new session with encryption support.
    
    Args:
        db: Database session.
        session: Session data.
        
    Returns:
        Created Session object.
    """
    session_data = session.model_dump()
    
    # Encrypt raw_transcript if it exists
    if session_data.get('raw_transcript') and session_data.get('user_id'):
        try:
            user_id = str(session_data['user_id'])
            original_transcript = session_data['raw_transcript']
            
            # Encrypt the transcript
            encrypted_transcript = encrypt_data(original_transcript, user_id)
            session_data['raw_transcript'] = encrypted_transcript
            session_data['is_encrypted'] = True
            
            logger.info(f"Session transcript encrypted for user {user_id}")
            
        except EncryptionError as e:
            logger.error(f"Failed to encrypt session transcript for user {user_id}: {e}")
            # For now, store as plain text if encryption fails
            session_data['is_encrypted'] = False
            
            # Log the error to migration_errors table
            _log_migration_error(db, session_data.get('user_id'), None, "encryption_failed", str(e))
    else:
        session_data['is_encrypted'] = False
    
    db_session = Session(**session_data)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_session_transcript(db: DbSession, session_id: UUID, transcript: str) -> Optional[Session]:
    """
    Update a session's transcript.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        transcript: Transcript text.
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    db_session = get_session(db, session_id)
    if db_session is None:
        return None
    
    db_session.raw_transcript = transcript
    db.commit()
    db.refresh(db_session)
    return db_session


def mark_session_processed(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Mark a session as processed.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    db_session = get_session(db, session_id)
    if db_session is None:
        return None
    
    db_session.is_processed = True
    db.commit()
    db.refresh(db_session)
    return db_session


def _log_migration_error(db: DbSession, user_id: UUID, session_id: UUID, error_type: str, error_message: str):
    """
    Log a migration error to the migration_errors table.
    
    Args:
        db: Database session.
        user_id: User ID associated with the error.
        session_id: Session ID associated with the error (can be None).
        error_type: Type of error (e.g., 'encryption_failed', 'decryption_failed').
        error_message: Detailed error message.
    """
    try:
        migration_error = MigrationError(
            user_id=user_id,
            session_id=session_id,
            error_type=error_type,
            error_message=error_message
        )
        db.add(migration_error)
        db.commit()
        logger.info(f"Migration error logged: {error_type} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to log migration error: {e}")
        db.rollback()