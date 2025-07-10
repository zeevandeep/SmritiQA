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
    # Log API route entry with fingerprint
    import logging, hashlib
    logger = logging.getLogger(__name__)
    
    # Create fingerprint of incoming session data
    session_data_str = str(session.model_dump())
    incoming_hash = hashlib.sha256(session_data_str.encode()).hexdigest()
    
    logger.info(f"[API ENTRY] create_session called")
    logger.info(f"[API FINGERPRINT] Incoming session hash: {incoming_hash}")
    logger.info(f"Creating session with data: {session.model_dump()}")
    
    # Verify user has access to create sessions for this user ID
    verify_user_access(str(session.user_id), current_user_id)
    
    # Verify that the user exists
    user = user_repository.get_user(db, user_id=session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create the session and return it - ONLY ONCE
    logger.info(f"[API CALL] About to call session_repository.create_session() - ONCE ONLY")
    created_session = session_repository.create_session(db=db, session=session)
    logger.info(f"[API EXIT] Session created with ID: {created_session.id}, duration: {created_session.duration_seconds}")
    
    # ChatGPT's post-creation fingerprint check
    import hashlib
    post_creation_hash = hashlib.sha256((created_session.raw_transcript or '').encode()).hexdigest()
    logger.warning(f"[POST API] FINAL SESSION RAW_TRANSCRIPT: {(created_session.raw_transcript or '')[:50]}...")
    logger.warning(f"[POST API] FINAL SESSION Hash: {post_creation_hash}")
    logger.warning(f"[POST API] FINAL SESSION Length: {len(created_session.raw_transcript or '')}")
    
    return created_session


@router.get("/user/{user_id}", response_model=List[SessionSchema])
def read_user_sessions(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Get sessions for a user.
    
    Args:
        user_id: ID of the user.
        skip: Number of sessions to skip.
        limit: Maximum number of sessions to return.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        List[Session]: List of sessions.
        
    Raises:
        HTTPException: If the user does not exist or access is denied.
    """
    # Verify user has access to view sessions for this user ID
    verify_user_access(str(user_id), current_user_id)
    
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
def read_session(
    session_id: UUID, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Get a session by ID.
    
    Args:
        session_id: ID of the session to retrieve.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        Session: Session data.
        
    Raises:
        HTTPException: If the session is not found or access is denied.
    """
    db_session = session_repository.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user has access to this session
    verify_user_access(str(db_session.user_id), current_user_id)
    
    return db_session


@router.put("/{session_id}/transcript", response_model=SessionSchema)
def update_session_transcript(
    session_id: UUID,
    transcript_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Update a session's transcript.
    
    Args:
        session_id: ID of the session.
        transcript_data: Dict containing the transcript text.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        Session: Updated session data.
        
    Raises:
        HTTPException: If the session is not found or access is denied.
    """
    # First get the session to check ownership
    existing_session = session_repository.get_session(db, session_id=session_id)
    if existing_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user has access to this session
    verify_user_access(str(existing_session.user_id), current_user_id)
    
    # Update the session transcript
    db_session = session_repository.update_session_transcript(
        db, session_id=session_id, transcript=transcript_data["transcript"]
    )
    return db_session


@router.put("/{session_id}/process", response_model=SessionSchema)
def mark_session_processed(
    session_id: UUID, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Mark a session as processed.
    
    Args:
        session_id: ID of the session to mark as processed.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        Session: Updated session data.
        
    Raises:
        HTTPException: If the session is not found or access is denied.
    """
    # First get the session to check ownership
    existing_session = session_repository.get_session(db, session_id=session_id)
    if existing_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user has access to this session
    verify_user_access(str(existing_session.user_id), current_user_id)
    
    # Mark the session as processed
    db_session = session_repository.mark_session_processed(db, session_id=session_id)
    return db_session