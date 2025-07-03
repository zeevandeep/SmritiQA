"""
Authentication utilities for password hashing and verification.
"""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Hash a password for storing in the database.
    
    Args:
        password: Plain text password to hash.
        
    Returns:
        Hashed password string.
    """
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify.
        password_hash: Stored password hash.
        
    Returns:
        True if password matches hash, False otherwise.
    """
    return check_password_hash(password_hash, password)