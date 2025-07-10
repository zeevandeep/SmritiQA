"""
User management routes for API v1.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User
from app.repositories import user_repository
from app.schemas.schemas import (
    User as UserSchema,
    UserCreate,
    UserAuthenticate,
    UserProfile as UserProfileSchema,
    UserProfileCreate,
    UserProfileUpdate
)
from app.utils.api_auth import get_current_user_from_jwt, verify_user_access

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    
    Args:
        user: User data.
        db: Database session.
        
    Returns:
        User: Created user data.
        
    Raises:
        HTTPException: If a user with the same email already exists.
    """
    db_user = user_repository.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return user_repository.create_user(db=db, user=user)


@router.post("/authenticate", response_model=UserSchema)
def authenticate_user(credentials: UserAuthenticate, db: Session = Depends(get_db)):
    """
    Authenticate a user.
    
    Args:
        credentials: User authentication credentials.
        db: Database session.
        
    Returns:
        User: Authenticated user data.
        
    Raises:
        HTTPException: If authentication fails.
    """
    db_user = user_repository.authenticate_user(db, user_auth=credentials)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return db_user


@router.get("/", response_model=List[UserSchema])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Get a list of users.
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        List[User]: List of users.
    """
    # This endpoint should be restricted to admin users only
    # For now, we'll disable this endpoint by raising a 403 error
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative access required"
    )


@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Get a user by ID.
    
    Args:
        user_id: ID of the user to retrieve.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        User: User data.
        
    Raises:
        HTTPException: If the user is not found or access is denied.
    """
    # Verify user has access to view this user's data
    verify_user_access(str(user_id), current_user_id)
    
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.get("/{user_id}/profile", response_model=UserProfileSchema)
def read_user_profile(user_id: UUID, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_from_jwt)):
    """
    Get a user's profile.
    
    Args:
        user_id: ID of the user.
        db: Database session.
        current_user_id: Current authenticated user ID from JWT.
        
    Returns:
        UserProfile: User profile data.
        
    Raises:
        HTTPException: If the user or profile is not found or access is denied.
    """
    # Verify user has access to view this user's profile
    verify_user_access(str(user_id), current_user_id)
    
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_profile = user_repository.get_user_profile(db, user_id=user_id)
    if db_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return db_profile


@router.post("/{user_id}/profile", response_model=UserProfileSchema, status_code=status.HTTP_201_CREATED)
def create_user_profile(
    user_id: UUID,
    profile: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a user profile.
    
    Args:
        user_id: ID of the user.
        profile: Profile data.
        db: Database session.
        
    Returns:
        UserProfile: Created profile data.
        
    Raises:
        HTTPException: If the user is not found or the profile already exists.
    """
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_profile = user_repository.get_user_profile(db, user_id=user_id)
    if db_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists"
        )
    
    return user_repository.create_user_profile(db=db, profile=profile, user_id=user_id)


@router.put("/{user_id}/profile", response_model=UserProfileSchema)
def update_user_profile(
    user_id: UUID,
    profile: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a user profile.
    
    Args:
        user_id: ID of the user.
        profile: Profile data to update.
        db: Database session.
        
    Returns:
        UserProfile: Updated profile data.
        
    Raises:
        HTTPException: If the user or profile is not found.
    """
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_profile = user_repository.update_user_profile(db=db, profile=profile, user_id=user_id)
    if db_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return db_profile