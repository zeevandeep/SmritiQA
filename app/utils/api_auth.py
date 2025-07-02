"""
JWT Authentication utilities for API endpoints.

This module provides authentication dependencies for FastAPI routes
that verify JWT tokens from cookies and extract user information.
"""
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.utils.jwt_utils import verify_access_token
from app.repositories import user_repository


def get_current_user_from_jwt(request: Request, db: Session = Depends(get_db)) -> str:
    """
    Extract and verify user ID from JWT access token in cookies.
    
    Args:
        request: FastAPI request object containing cookies
        db: Database session
        
    Returns:
        str: User ID from verified JWT token
        
    Raises:
        HTTPException: If authentication fails or token is invalid
    """
    # Get access token from cookies
    access_token = request.cookies.get("smriti_access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Verify the access token
    payload = verify_access_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Extract user ID from payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify user exists in database
    user = user_repository.get_user(db, user_id=UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user_id


def verify_user_access(user_id: str, current_user_id: str) -> None:
    """
    Verify that the current user has access to the requested user's data.
    
    Args:
        user_id: The user ID being accessed
        current_user_id: The authenticated user's ID
        
    Raises:
        HTTPException: If user doesn't have access to the requested data
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access another user's data"
        )


def get_current_user_optional(request: Request) -> Optional[str]:
    """
    Extract user ID from JWT token without raising exceptions.
    
    Args:
        request: FastAPI request object containing cookies
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
    """
    try:
        access_token = request.cookies.get("smriti_access_token")
        if not access_token:
            return None
            
        payload = verify_access_token(access_token)
        if not payload:
            return None
            
        return payload.get("sub")
    except Exception:
        return None