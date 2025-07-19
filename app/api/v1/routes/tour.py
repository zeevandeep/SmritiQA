"""
Tour completion API endpoints.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.user_repository import mark_tour_completed, get_user_tour_status
from app.utils.api_auth import get_current_user_from_jwt

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/complete/{user_id}")
def complete_tour(user_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Mark the app tour as completed for a user.
    
    Args:
        user_id: ID of the user.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT token.
        
    Returns:
        Success status.
    """
    # Verify user can only mark their own tour as completed
    if str(current_user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = mark_tour_completed(db, user_id)
    if success:
        logger.info(f"Tour marked as completed for user {user_id}")
        return {"success": True, "message": "Tour marked as completed"}
    else:
        raise HTTPException(status_code=500, detail="Failed to mark tour as completed")


@router.get("/status/{user_id}")
def get_tour_status(user_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Get the tour completion status for a user.
    
    Args:
        user_id: ID of the user.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT token.
        
    Returns:
        Tour completion status.
    """
    # Verify user can only check their own tour status
    if str(current_user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    tour_completed = get_user_tour_status(db, user_id)
    return {"tour_completed": tour_completed}