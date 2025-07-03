"""
User repository for database operations.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.models import User, UserProfile
from app.schemas.schemas import UserCreate
from app.utils.auth import get_password_hash


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users."""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user with password hashing."""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_oauth(db: Session, email: str, **kwargs) -> User:
    """Create a new user via OAuth (no password required)."""
    db_user = User(email=email, **kwargs)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_profile(db: Session, user_id: UUID) -> Optional[UserProfile]:
    """Get a user profile."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def create_user_profile(db: Session, user_id: UUID, **profile_data) -> UserProfile:
    """Create a user profile."""
    db_profile = UserProfile(user_id=user_id, **profile_data)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_user_profile(db: Session, user_id: UUID, **profile_data) -> Optional[UserProfile]:
    """Update a user profile."""
    db_profile = get_user_profile(db, user_id)
    if db_profile:
        for key, value in profile_data.items():
            if hasattr(db_profile, key) and value is not None:
                setattr(db_profile, key, value)
        db.commit()
        db.refresh(db_profile)
    return db_profile