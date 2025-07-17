"""
Google OAuth user management service.
Handles user creation, account linking, and profile updates for Google OAuth authentication.
"""
import logging
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import User, UserProfile
from app.repositories import user_repository
from app.utils.google_oauth import log_oauth_event

logger = logging.getLogger(__name__)


async def find_or_create_google_user(google_user_info: Dict[str, Any], db: Session, request) -> tuple[User, bool]:
    """
    Find existing user or create new one from Google OAuth data.
    Implements secure account linking by email address.
    
    Args:
        google_user_info: Validated user information from Google ID token
        db: Database session
        request: FastAPI request object for audit logging
        
    Returns:
        Tuple of (User object, is_new_user boolean)
    """
    # Validate input data
    if not google_user_info:
        logger.error("Google user info is None or empty")
        raise ValueError("Google user information is required")
    
    email = google_user_info.get('email')
    if not email:
        logger.error("Email not found in Google user info")
        raise ValueError("Email address is required from Google OAuth")
    
    logger.info(f"Processing Google OAuth for email: {email}")
    
    # Check if user exists by email
    existing_user = user_repository.get_user_by_email(db, email)
    
    if existing_user:
        logger.info(f"Found existing user for email: {email}")
        
        # Log security event for account linking
        had_password = existing_user.password_hash is not None
        log_oauth_event(email, request, had_existing_password=had_password)
        
        # Update profile with Google data if needed
        await update_user_profile_from_google(existing_user, google_user_info, db)
        
        return existing_user, False  # Existing user, not new
    
    # Create new user
    logger.info(f"Creating new user for Google OAuth: {email}")
    new_user = User(
        id=uuid4(),
        email=email,
        password_hash=None,  # Google OAuth users don't have passwords
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create user profile with Google data
    await create_user_profile_from_google(new_user, google_user_info, db)
    
    # Log new user creation
    log_oauth_event(email, request, had_existing_password=False)
    
    logger.info(f"Successfully created new user: {new_user.id}")
    return new_user, True  # New user created


async def create_user_profile_from_google(user: User, google_data: Dict[str, Any], db: Session) -> UserProfile:
    """
    Create user profile with Google OAuth information.
    
    Args:
        user: User object
        google_data: Validated Google user information
        db: Database session
        
    Returns:
        Created UserProfile object
    """
    try:
        profile_data = {
            'user_id': user.id,
            'display_name': google_data.get('name', '').strip() or None,
            'profile_image_url': google_data.get('picture'),
            'language': 'en',  # Default language
            'language_preference': 'en',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Create profile
        profile = UserProfile(**profile_data)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Created profile for user {user.id} with Google data")
        return profile
        
    except Exception as e:
        logger.error(f"Failed to create user profile from Google data: {e}")
        db.rollback()
        raise


async def update_user_profile_from_google(user: User, google_data: Dict[str, Any], db: Session) -> Optional[UserProfile]:
    """
    Update existing user profile with Google OAuth information.
    Only updates fields that are empty or None to preserve user customizations.
    
    Args:
        user: User object
        google_data: Validated Google user information
        db: Database session
        
    Returns:
        Updated UserProfile object or None if no profile exists
    """
    try:
        # Get existing profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        
        if not profile:
            # Create new profile if none exists
            logger.info(f"No profile found for user {user.id}, creating from Google data")
            return await create_user_profile_from_google(user, google_data, db)
        
        # Update only empty fields to preserve user customizations
        updates = {}
        
        # Update display name if not set
        if not profile.display_name and google_data.get('name'):
            updates['display_name'] = google_data['name'].strip()
        
        # Update profile image if not set or if Google has a newer one
        google_picture = google_data.get('picture')
        if google_picture and (not profile.profile_image_url or profile.profile_image_url != google_picture):
            updates['profile_image_url'] = google_picture
        
        # Apply updates if any
        if updates:
            updates['updated_at'] = datetime.utcnow()
            for key, value in updates.items():
                setattr(profile, key, value)
            
            db.commit()
            db.refresh(profile)
            
            logger.info(f"Updated profile for user {user.id} with Google data: {list(updates.keys())}")
        else:
            logger.info(f"No profile updates needed for user {user.id}")
        
        return profile
        
    except Exception as e:
        logger.error(f"Failed to update user profile from Google data: {e}")
        db.rollback()
        return None


def get_google_oauth_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about Google OAuth usage.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with OAuth statistics
    """
    try:
        # Count users with Google OAuth (no password)
        google_only_users = db.query(User).filter(User.password_hash.is_(None)).count()
        
        # Count users with both password and Google (linked accounts)
        linked_accounts = db.query(User).filter(User.password_hash.isnot(None)).count()
        
        # Count profiles with Google profile images
        google_profiles = db.query(UserProfile).filter(UserProfile.profile_image_url.isnot(None)).count()
        
        return {
            'google_only_users': google_only_users,
            'linked_accounts': linked_accounts,
            'total_users': google_only_users + linked_accounts,
            'profiles_with_google_images': google_profiles
        }
        
    except Exception as e:
        logger.error(f"Failed to get Google OAuth stats: {e}")
        return {
            'google_only_users': 0,
            'linked_accounts': 0,
            'total_users': 0,
            'profiles_with_google_images': 0
        }