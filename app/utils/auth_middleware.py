"""
JWT authentication middleware and decorators for Smriti.

This module provides decorators and utilities for protecting routes
with JWT authentication and handling token validation.
"""

from functools import wraps
from flask import request, jsonify, redirect, url_for, make_response
from typing import Optional, Callable, Any
from .jwt_utils import verify_access_token, verify_refresh_token, generate_access_token
import requests

def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Get user information by ID from the API.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        User data dictionary or None if not found
    """
    try:
        # Use the existing API endpoint
        response = requests.get(f"http://localhost:8000/api/v1/users/{user_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def extract_jwt_from_cookies() -> tuple[Optional[str], Optional[str]]:
    """
    Extract access and refresh tokens from HTTP-only cookies.
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = request.cookies.get('smriti_access_token')
    refresh_token = request.cookies.get('smriti_refresh_token')
    return access_token, refresh_token

def handle_auth_error(message: str, status_code: int = 401):
    """
    Handle authentication errors based on request type.
    
    Args:
        message: Error message to display
        status_code: HTTP status code
        
    Returns:
        JSON response for AJAX requests, redirect for page requests
    """
    # Check if this is an AJAX request
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'error': message, 'code': 'AUTH_ERROR'}), status_code
    else:
        # For page requests, redirect to login
        return redirect(url_for('login'))

def set_jwt_cookies(response, access_token: str, refresh_token: str):
    """
    Set secure JWT cookies on the response.
    
    Args:
        response: Flask response object
        access_token: JWT access token
        refresh_token: Refresh token
    """
    # Set access token cookie (shorter expiry)
    response.set_cookie(
        'smriti_access_token',
        access_token,
        max_age=1800,  # 30 minutes
        httponly=True,
        secure=True,  # Use HTTPS in production
        samesite='Lax'
    )
    
    # Set refresh token cookie (longer expiry)
    response.set_cookie(
        'smriti_refresh_token', 
        refresh_token,
        max_age=1209600,  # 14 days
        httponly=True,
        secure=True,
        samesite='Lax'
    )

def clear_jwt_cookies(response):
    """
    Clear JWT cookies from the response.
    
    Args:
        response: Flask response object
    """
    response.set_cookie('smriti_access_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    response.set_cookie('smriti_refresh_token', '', expires=0, httponly=True, secure=True, samesite='Lax')

def jwt_required(f: Callable) -> Callable:
    """
    Decorator to protect routes with JWT authentication.
    
    This decorator checks for valid JWT tokens and handles
    automatic token refresh when access tokens expire.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Any:
        access_token, refresh_token = extract_jwt_from_cookies()
        
        # Check if access token is valid
        if access_token:
            user_data = verify_access_token(access_token)
            if user_data:
                # Valid access token - proceed with request
                request.current_user_id = user_data['sub']
                request.current_user_email = user_data['email']
                return f(*args, **kwargs)
        
        # Access token invalid/expired - try refresh
        if refresh_token:
            user_id = verify_refresh_token(refresh_token)
            if user_id:
                # Valid refresh token - get user info and generate new access token
                user = get_user_by_id(user_id)
                if user:
                    new_access_token = generate_access_token(user_id, user['email'])
                    
                    # Set the current user for this request
                    request.current_user_id = user_id
                    request.current_user_email = user['email']
                    
                    # Execute the protected function
                    response = make_response(f(*args, **kwargs))
                    
                    # Set the new access token in the response
                    response.set_cookie(
                        'smriti_access_token',
                        new_access_token,
                        max_age=1800,
                        httponly=True,
                        secure=True,
                        samesite='Lax'
                    )
                    
                    return response
        
        # No valid tokens - authentication required
        return handle_auth_error("Authentication required")
    
    return decorated_function

def get_current_user_id() -> Optional[str]:
    """
    Get the current user ID from the request context.
    
    Returns:
        User ID if authenticated, None otherwise
    """
    return getattr(request, 'current_user_id', None)

def get_current_user_email() -> Optional[str]:
    """
    Get the current user email from the request context.
    
    Returns:
        User email if authenticated, None otherwise
    """
    return getattr(request, 'current_user_email', None)

def optional_jwt_auth(f: Callable) -> Callable:
    """
    Decorator for routes that work with optional authentication.
    
    Sets user context if valid JWT is present, but doesn't require it.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Any:
        access_token, refresh_token = extract_jwt_from_cookies()
        
        # Try to authenticate but don't require it
        if access_token:
            user_data = verify_access_token(access_token)
            if user_data:
                request.current_user_id = user_data['sub']
                request.current_user_email = user_data['email']
                return f(*args, **kwargs)
        
        # Try refresh token if access token failed
        if refresh_token:
            user_id = verify_refresh_token(refresh_token)
            if user_id:
                user = get_user_by_id(user_id)
                if user:
                    request.current_user_id = user_id
                    request.current_user_email = user['email']
        
        # Proceed without authentication
        return f(*args, **kwargs)
    
    return decorated_function