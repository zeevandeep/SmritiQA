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
            # Check if this looks like encrypted data (base64, longer than original)
            if len(db_session.raw_transcript) > 100 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=-_" for c in db_session.raw_transcript):
                db_session.raw_transcript = decrypt_data(db_session.raw_transcript, user_id)
            else:
                # This looks like plain text, fix the encryption flag
                logger.warning(f"Session {session_id} marked as encrypted but contains plain text, fixing flag")
                db_session.is_encrypted = False
                db.commit()
        except EncryptionError as e:
            logger.error(f"Failed to decrypt session {session_id} for user {user_id}: {e}")
            _log_migration_error(db, db_session.user_id, session_id, "decryption_failed", str(e))
            # Treat as plain text if decryption fails
            logger.warning(f"Treating session {session_id} as plain text due to decryption failure")
            db_session.is_encrypted = False
            db.commit()
    
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
                # Check if this looks like encrypted data (base64, longer than original)
                if len(session.raw_transcript) > 100 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=-_" for c in session.raw_transcript):
                    session.raw_transcript = decrypt_data(session.raw_transcript, str(user_id))
                else:
                    # This looks like plain text, fix the encryption flag
                    logger.warning(f"Session {session.id} marked as encrypted but contains plain text, fixing flag")
                    session.is_encrypted = False
                    db.commit()
                decrypted_sessions.append(session)
            except EncryptionError as e:
                logger.error(f"Failed to decrypt session {session.id} for user {user_id}: {e}")
                _log_migration_error(db, user_id, session.id, "decryption_failed", str(e))
                # Treat as plain text if decryption fails
                logger.warning(f"Treating session {session.id} as plain text due to decryption failure")
                session.is_encrypted = False
                db.commit()
                decrypted_sessions.append(session)
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
    
    print(f"[REPOSITORY] create_session called with session data: {session_data}")
    print(f"[REPOSITORY] Checking encryption conditions...")
    print(f"[REPOSITORY] session_data.get('raw_transcript'): {bool(session_data.get('raw_transcript'))}")
    print(f"[REPOSITORY] session_data.get('user_id'): {bool(session_data.get('user_id'))}")
    logger.info(f"[REPOSITORY] create_session called with session data: {session_data}")
    logger.info(f"[REPOSITORY] Checking encryption conditions...")
    logger.info(f"[REPOSITORY] session_data.get('raw_transcript'): {bool(session_data.get('raw_transcript'))}")
    logger.info(f"[REPOSITORY] session_data.get('user_id'): {bool(session_data.get('user_id'))}")
    
    # Encrypt raw_transcript if it exists
    if session_data.get('raw_transcript') and session_data.get('user_id'):
        try:
            user_id = str(session_data['user_id'])
            original_transcript = session_data['raw_transcript']
            
            logger.info(f"[ENCRYPTION DEBUG] Starting encryption for user {user_id}")
            logger.info(f"[ENCRYPTION DEBUG] Original transcript length: {len(original_transcript)}")
            logger.info(f"[ENCRYPTION DEBUG] Original transcript: {original_transcript[:50]}...")
            
            # Encrypt the transcript
            encrypted_transcript = encrypt_data(original_transcript, user_id)
            
            logger.info(f"[ENCRYPTION DEBUG] Encryption successful, length: {len(encrypted_transcript)}")
            logger.info(f"[ENCRYPTION DEBUG] Encrypted transcript: {encrypted_transcript[:50]}...")
            
            session_data['raw_transcript'] = encrypted_transcript
            session_data['is_encrypted'] = True
            
            logger.info(f"Session transcript encrypted for user {user_id}")
            
        except Exception as e:  # Catch all exceptions, not just EncryptionError
            logger.error(f"[ENCRYPTION DEBUG] Exception during encryption: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[ENCRYPTION DEBUG] Traceback: {traceback.format_exc()}")
            
            # For now, store as plain text if encryption fails
            session_data['is_encrypted'] = False
            
            # Log the error to migration_errors table
            _log_migration_error(db, session_data.get('user_id'), None, "encryption_failed", str(e))
    else:
        session_data['is_encrypted'] = False
    
    logger.info(f"[ENCRYPTION DEBUG] Final session_data raw_transcript length: {len(session_data.get('raw_transcript', ''))}")
    logger.info(f"[ENCRYPTION DEBUG] Final is_encrypted flag: {session_data.get('is_encrypted')}")
    
    # Create the Session object
    db_session = Session(**session_data)
    logger.info(f"[ENCRYPTION DEBUG] Session object created, transcript length: {len(db_session.raw_transcript)}")
    logger.info(f"[ENCRYPTION DEBUG] Session object encrypted flag: {db_session.is_encrypted}")
    logger.info(f"[ENCRYPTION DEBUG] Session object transcript starts with: {db_session.raw_transcript[:50]}...")
    
    # Add to database
    db.add(db_session)
    logger.info(f"[ENCRYPTION DEBUG] After db.add(), transcript length: {len(db_session.raw_transcript)}")
    logger.info(f"[ENCRYPTION DEBUG] After db.add(), transcript starts with: {db_session.raw_transcript[:50]}...")
    
    # Commit to database
    db.commit()
    logger.info(f"[ENCRYPTION DEBUG] After db.commit(), transcript length: {len(db_session.raw_transcript)}")
    logger.info(f"[ENCRYPTION DEBUG] After db.commit(), transcript starts with: {db_session.raw_transcript[:50]}...")
    
    # Check what's actually in the database
    db_check = db.query(Session).filter(Session.id == db_session.id).first()
    logger.info(f"[ENCRYPTION DEBUG] Database reality check - length: {len(db_check.raw_transcript)}")
    logger.info(f"[ENCRYPTION DEBUG] Database reality check - starts with: {db_check.raw_transcript[:50]}...")
    logger.info(f"[ENCRYPTION DEBUG] Database reality check - is_encrypted: {db_check.is_encrypted}")
    
    # Refresh from database
    db.refresh(db_session)
    logger.info(f"[ENCRYPTION DEBUG] After db.refresh(), transcript length: {len(db_session.raw_transcript)}")
    logger.info(f"[ENCRYPTION DEBUG] After db.refresh(), transcript starts with: {db_session.raw_transcript[:50]}...")
    logger.info(f"[ENCRYPTION DEBUG] After db.refresh(), is_encrypted: {db_session.is_encrypted}")
    
    return db_session


def update_session_transcript(db: DbSession, session_id: UUID, transcript: str) -> Optional[Session]:
    """
    Update a session's transcript with encryption support.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        transcript: Transcript text (plain text).
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        return None
    
    # If the session is marked as encrypted, encrypt the new transcript
    if db_session.is_encrypted:
        try:
            user_id = str(db_session.user_id)
            logger.info(f"[UPDATE TRANSCRIPT] Encrypting updated transcript for user {user_id}")
            encrypted_transcript = encrypt_data(transcript, user_id)
            db_session.raw_transcript = encrypted_transcript
            logger.info(f"[UPDATE TRANSCRIPT] Transcript encrypted successfully")
        except Exception as e:
            logger.error(f"[UPDATE TRANSCRIPT] Failed to encrypt updated transcript: {e}")
            # If encryption fails, store as plain text and mark as unencrypted
            db_session.raw_transcript = transcript
            db_session.is_encrypted = False
            _log_migration_error(db, db_session.user_id, session_id, "encryption_failed", str(e))
    else:
        # Session is not encrypted, store as plain text
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