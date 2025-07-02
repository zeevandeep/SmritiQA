"""
JWT utilities for secure authentication in Smriti.

This module provides functions for generating, validating, and managing
JWT access and refresh tokens with configurable expiry times.
"""

import jwt
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import psycopg2

# Environment-based configuration
ACCESS_TOKEN_EXPIRY = int(os.getenv("ACCESS_TOKEN_EXPIRY_SECONDS", 1800))  # 30 minutes
REFRESH_TOKEN_EXPIRY = int(os.getenv("REFRESH_TOKEN_EXPIRY_SECONDS", 1209600))  # 14 days
JWT_SECRET = os.environ.get("SESSION_SECRET")
JWT_ALGORITHM = "HS256"

if not JWT_SECRET:
    raise ValueError("SESSION_SECRET environment variable is required for JWT authentication")

def generate_access_token(user_id: str, email: str) -> str:
    """
    Generate a short-lived access token for API authentication.
    
    Args:
        user_id: The user's UUID
        email: The user's email address
        
    Returns:
        JWT access token string
    """
    now = datetime.utcnow()
    payload = {
        'sub': user_id,
        'email': email,
        'iat': now,
        'exp': now + timedelta(seconds=ACCESS_TOKEN_EXPIRY),
        'type': 'access'
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_refresh_token(user_id: str) -> str:
    """
    Generate a long-lived refresh token and store it in the database.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        Refresh token string
    """
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Store in database
    try:
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Clean up expired tokens for this user
        cursor.execute("""
            DELETE FROM refresh_tokens 
            WHERE user_id = %s AND (expires_at < CURRENT_TIMESTAMP OR is_valid = FALSE)
        """, (user_id,))
        
        # Insert new refresh token
        expires_at = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRY)
        cursor.execute("""
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (user_id, token, expires_at))
        
        conn.commit()
        return token
        
    except Exception as e:
        print(f"Error storing refresh token: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode an access token.
    
    Args:
        token: The JWT access token to verify
        
    Returns:
        Dictionary containing user data if valid, None if invalid
    """
    try:
        # Add leeway for clock skew (ChatGPT recommendation)
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=[JWT_ALGORITHM],
            leeway=timedelta(minutes=1)
        )
        
        # Verify it's an access token
        if payload.get('type') != 'access':
            return None
            
        # Handle backward compatibility for old tokens with 'user_id' 
        user_id = payload.get('sub') or payload.get('user_id')
        return {
            'sub': user_id,
            'email': payload['email'],
            'expires_at': payload['exp']
        }
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return the associated user_id.
    
    Args:
        token: The refresh token to verify
        
    Returns:
        User ID if valid, None if invalid
    """
    try:
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if token exists and is valid
        cursor.execute("""
            SELECT user_id FROM refresh_tokens 
            WHERE token = %s 
            AND expires_at > CURRENT_TIMESTAMP 
            AND is_valid = TRUE
        """, (token,))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        print(f"Error verifying refresh token: {e}")
        return None
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def revoke_refresh_token(token: str) -> bool:
    """
    Revoke a refresh token (mark as invalid).
    
    Args:
        token: The refresh token to revoke
        
    Returns:
        True if successful, False otherwise
    """
    try:
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE refresh_tokens 
            SET is_valid = FALSE 
            WHERE token = %s
        """, (token,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Error revoking refresh token: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def revoke_all_user_tokens(user_id: str) -> bool:
    """
    Revoke all refresh tokens for a user (useful for logout from all devices).
    
    Args:
        user_id: The user's UUID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE refresh_tokens 
            SET is_valid = FALSE 
            WHERE user_id = %s
        """, (user_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error revoking user tokens: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def cleanup_expired_tokens() -> int:
    """
    Clean up expired refresh tokens from the database.
    
    Returns:
        Number of tokens cleaned up
    """
    try:
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM refresh_tokens 
            WHERE expires_at < CURRENT_TIMESTAMP OR is_valid = FALSE
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
        
    except Exception as e:
        print(f"Error cleaning up tokens: {e}")
        return 0
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()