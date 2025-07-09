"""
Session repository for database operations related to user sessions.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Session
from app.schemas.schemas import SessionCreate


def get_session(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Get a session by ID.
    
    Args:
        db: Database session.
        session_id: ID of the session to retrieve.
        
    Returns:
        Session object if found, None otherwise.
    """
    return db.query(Session).filter(Session.id == session_id).first()


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
    return db.query(Session)\
        .filter(Session.user_id == user_id)\
        .order_by(Session.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def create_session(db: DbSession, session: SessionCreate) -> Session:
    """
    Create a new session.
    
    Args:
        db: Database session.
        session: Session data.
        
    Returns:
        Created Session object.
    """
    db_session = Session(**session.model_dump())
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