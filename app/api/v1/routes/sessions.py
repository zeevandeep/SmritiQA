"""
Session management routes for API v1.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import session_repository, user_repository
from app.schemas.schemas import (
    Session as SessionSchema,
    SessionCreate
)
from app.utils.api_auth import get_current_user_from_jwt, verify_user_access

router = APIRouter()


@router.post("/", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Create a new session.
    
    Args:
        session: Session data.
        db: Database session.
        
    Returns:
        Session: Created session data.
        
    Raises:
        HTTPException: If the user does not exist or access is denied.
    """
    # Verify user has access to create sessions for this user ID
    verify_user_access(str(session.user_id), current_user_id)
    
    # Log received session data for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating session with data: {session.model_dump()}")
    
    # Verify that the user exists
    user = user_repository.get_user(db, user_id=session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create the session and return it
    created_session = session_repository.create_session(db=db, session=session)
    logger.info(f"Session created with ID: {created_session.id}, duration: {created_session.duration_seconds}")
    return created_session


@router.get("/user/{user_id}", response_model=List[SessionSchema])
def read_user_sessions(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get sessions for a user.
    
    Args:
        user_id: ID of the user.
        skip: Number of sessions to skip.
        limit: Maximum number of sessions to return.
        db: Database session.
        
    Returns:
        List[Session]: List of sessions.
        
    Raises:
        HTTPException: If the user does not exist.
    """
    # Verify that the user exists
    user = user_repository.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get the user's sessions
    return session_repository.get_user_sessions(db, user_id=user_id, skip=skip, limit=limit)


@router.get("/{session_id}", response_model=SessionSchema)
def read_session(session_id: UUID, db: Session = Depends(get_db)):
    """
    Get a session by ID.
    
    Args:
        session_id: ID of the session to retrieve.
        db: Database session.
        
    Returns:
        Session: Session data.
        
    Raises:
        HTTPException: If the session is not found.
    """
    db_session = session_repository.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return db_session


@router.put("/{session_id}/transcript", response_model=SessionSchema)
def update_session_transcript(
    session_id: UUID,
    transcript_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update a session's transcript.
    
    Args:
        session_id: ID of the session.
        transcript_data: Dict containing the transcript text.
        db: Database session.
        
    Returns:
        Session: Updated session data.
        
    Raises:
        HTTPException: If the session is not found.
    """
    db_session = session_repository.update_session_transcript(
        db, session_id=session_id, transcript=transcript_data["transcript"]
    )
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return db_session


@router.put("/{session_id}/process", response_model=SessionSchema)
def mark_session_processed(session_id: UUID, db: Session = Depends(get_db)):
    """
    Mark a session as processed.
    
    Args:
        session_id: ID of the session.
        db: Database session.
        
    Returns:
        Session: Updated session data.
        
    Raises:
        HTTPException: If the session is not found.
    """
    db_session = session_repository.mark_session_processed(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return db_session