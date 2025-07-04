"""
User repository for database operations related to users.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.models import User, UserProfile
from app.schemas.schemas import UserCreate, UserProfileCreate, UserProfileUpdate, UserAuthenticate


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session.
        user_id: ID of the user to retrieve.
        
    Returns:
        User object if found, None otherwise.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session.
        email: Email of the user to retrieve.
        
    Returns:
        User object if found, None otherwise.
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, user_auth: UserAuthenticate) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session.
        user_auth: User authentication data.
        
    Returns:
        User object if authentication is successful, None otherwise.
    """
    print(f"DEBUG: Repository authenticate_user called for {user_auth.email}")
    
    # Retrieve the user by email
    user = get_user_by_email(db, email=user_auth.email)
    print(f"DEBUG: User found: {user is not None}")
    
    # Check if user exists
    if user is None:
        print(f"DEBUG: User {user_auth.email} not found in database")
        return None
    
    # Get the password hash as a string
    password_hash = getattr(user, 'password_hash', None)
    print(f"DEBUG: Password hash exists: {password_hash is not None}")
    print(f"DEBUG: Password hash length: {len(password_hash) if password_hash else 0}")
    
    # Check if user has a password hash
    if password_hash is None or password_hash == '':
        print(f"DEBUG: No password hash for user {user_auth.email}")
        return None
    
    # Use check_password_hash with string values
    print(f"DEBUG: Checking password for {user_auth.email}")
    password_check_result = check_password_hash(str(password_hash), user_auth.password)
    print(f"DEBUG: Password check result: {password_check_result}")
    
    if not password_check_result:
        print(f"DEBUG: Password verification failed for {user_auth.email}")
        return None
    
    print(f"DEBUG: Authentication successful for {user_auth.email}")
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users.
    
    Args:
        db: Database session.
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        
    Returns:
        List of User objects.
    """
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session.
        user: User data.
        
    Returns:
        Created User object.
    """
    # Hash the password before storing
    hashed_password = generate_password_hash(user.password)
    
    db_user = User(email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_profile(db: Session, user_id: UUID) -> Optional[UserProfile]:
    """
    Get a user profile.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        
    Returns:
        UserProfile object if found, None otherwise.
    """
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def create_user_profile(db: Session, profile: UserProfileCreate, user_id: UUID) -> UserProfile:
    """
    Create a new user profile.
    
    Args:
        db: Database session.
        profile: User profile data.
        user_id: ID of the user.
        
    Returns:
        Created UserProfile object.
    """
    db_profile = UserProfile(**profile.model_dump(), user_id=user_id)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_user_profile(db: Session, profile: UserProfileUpdate, user_id: UUID) -> Optional[UserProfile]:
    """
    Update a user profile.
    
    Args:
        db: Database session.
        profile: User profile data to update.
        user_id: ID of the user.
        
    Returns:
        Updated UserProfile object if found, None otherwise.
    """
    db_profile = get_user_profile(db, user_id)
    if db_profile is None:
        return None
    
    profile_data = profile.model_dump(exclude_unset=True)
    for key, value in profile_data.items():
        setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile


def update_display_name(db: Session, user_id: UUID, display_name: str) -> bool:
    """
    Update the display name for a user profile.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        display_name: New display name.
        
    Returns:
        True if update was successful, False otherwise.
    """
    try:
        db_profile = get_user_profile(db, user_id)
        if db_profile is None:
            return False
        
        setattr(db_profile, 'display_name', display_name)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def delete_user_completely(db: Session, user_id: UUID) -> bool:
    """
    Delete a user and all their associated data from all tables.
    
    Args:
        db: Database session.
        user_id: ID of the user to delete.
        
    Returns:
        True if deletion was successful, False otherwise.
    """
    from app.models.models import User, UserProfile, Session as JournalSession, Node, Edge, Reflection, Feedback
    
    try:
        # Delete all related data in the correct order (respecting foreign key constraints)
        
        # 1. Delete feedback
        db.query(Feedback).filter(Feedback.user_id == user_id).delete()
        
        # 2. Delete reflections
        db.query(Reflection).filter(Reflection.user_id == user_id).delete()
        
        # 3. Delete edges
        db.query(Edge).filter(Edge.user_id == user_id).delete()
        
        # 4. Delete nodes
        db.query(Node).filter(Node.user_id == user_id).delete()
        
        # 5. Delete journal sessions
        db.query(JournalSession).filter(JournalSession.user_id == user_id).delete()
        
        # 6. Delete user profile
        db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
        
        # 7. Finally delete the user
        db.query(User).filter(User.id == user_id).delete()
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False