"""
Session management API routes.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.schemas.schemas import Session, SessionCreate
from app.models.models import Session as SessionModel, User
from app.api.v1.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[Session])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all sessions for the current user."""
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return sessions


@router.post("/", response_model=Session)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Create a new journal session."""
    # Ensure the session is created for the current user
    db_session = SessionModel(
        user_id=current_user.id,
        duration_seconds=session_data.duration_seconds,
        raw_transcript=session_data.raw_transcript
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get a specific session by ID."""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.put("/{session_id}", response_model=Session)
async def update_session(
    session_id: UUID,
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Update a session."""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Update session fields
    if session_data.duration_seconds is not None:
        session.duration_seconds = session_data.duration_seconds
    if session_data.raw_transcript is not None:
        session.raw_transcript = session_data.raw_transcript
    
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Delete a session."""
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}