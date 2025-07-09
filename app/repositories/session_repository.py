"""
Session repository for database operations related to user sessions.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Session
from app.schemas.schemas import SessionCreate
from app.utils.encryption import get_encryption


def get_session(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Get a session by ID.
    
    Args:
        db: Database session.
        session_id: ID of the session to retrieve.
        
    Returns:
        Session object if found, None otherwise.
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if session and session.raw_transcript:
        # Decrypt transcript when reading from database
        session.raw_transcript = get_encryption().decrypt_transcript(session.raw_transcript)
    return session


def get_user_sessions(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Session]:
    """
    Get sessions for a user.
    
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
    
    # Decrypt transcripts for all sessions
    for session in sessions:
        if session.raw_transcript:
            session.raw_transcript = get_encryption().decrypt_transcript(session.raw_transcript)
    
    return sessions


def create_session(db: DbSession, session: SessionCreate) -> Session:
    """
    Create a new session.
    
    Args:
        db: Database session.
        session: Session data.
        
    Returns:
        Created Session object.
    """
    session_data = session.model_dump()
    
    # Encrypt transcript before storing
    if session_data.get('raw_transcript'):
        session_data['raw_transcript'] = get_encryption().encrypt_transcript(session_data['raw_transcript'])
    
    db_session = Session(**session_data)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Decrypt transcript for return value
    if db_session.raw_transcript:
        db_session.raw_transcript = get_encryption().decrypt_transcript(db_session.raw_transcript)
    
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
    # Get session without decryption (direct database query)
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if db_session is None:
        return None
    
    # Encrypt transcript before storing
    db_session.raw_transcript = get_encryption().encrypt_transcript(transcript)
    db.commit()
    db.refresh(db_session)
    
    # Decrypt transcript for return value
    if db_session.raw_transcript:
        db_session.raw_transcript = get_encryption().decrypt_transcript(db_session.raw_transcript)
    
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