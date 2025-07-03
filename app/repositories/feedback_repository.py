"""
Repository for handling user feedback operations.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.models import Feedback
from app.schemas.schemas import UserFeedbackCreate


def create_feedback(db: Session, feedback_data: UserFeedbackCreate, user_id: UUID) -> Feedback:
    """Create a new feedback entry."""
    db_feedback = Feedback(
        user_id=user_id,
        feedback_type=feedback_data.feedback_type,
        subject=feedback_data.subject,
        message=feedback_data.message,
        rating=feedback_data.rating,
        contact_email=feedback_data.contact_email,
        status="new"
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_by_id(db: Session, feedback_id: UUID) -> Optional[Feedback]:
    """Get feedback by ID."""
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_user_feedback(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Feedback]:
    """Get all feedback for a specific user."""
    return db.query(Feedback).filter(
        Feedback.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_all_feedback(db: Session, skip: int = 0, limit: int = 100) -> List[Feedback]:
    """Get all feedback (for admin use)."""
    return db.query(Feedback).offset(skip).limit(limit).all()


def update_feedback_status(db: Session, feedback_id: UUID, status: str) -> Optional[Feedback]:
    """Update feedback status (for admin use)."""
    db.query(Feedback).filter(Feedback.id == feedback_id).update({"status": status})
    db.commit()
    return get_feedback_by_id(db, feedback_id)


def get_feedback_by_type(db: Session, feedback_type: str, skip: int = 0, limit: int = 100) -> List[Feedback]:
    """Get feedback by type (suggestion, bug, compliment)."""
    return db.query(Feedback).filter(
        Feedback.feedback_type == feedback_type
    ).offset(skip).limit(limit).all()


def get_feedback_count_by_user(db: Session, user_id: UUID) -> int:
    """Get total feedback count for a user."""
    return db.query(Feedback).filter(Feedback.user_id == user_id).count()