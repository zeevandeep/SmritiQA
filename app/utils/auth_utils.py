"""
Authentication utility functions for cookie management and environment detection.
"""
from app.config import AUTH_CONFIG, IS_PRODUCTION
from fastapi.responses import JSONResponse


def set_auth_cookies(response: JSONResponse, access_token: str, refresh_token: str = None):
    """
    Set authentication cookies with environment-appropriate security settings.
    
    Args:
        response: FastAPI response object
        access_token: JWT access token
        refresh_token: JWT refresh token (optional)
    """
    # Set access token cookie
    response.set_cookie(
        key="smriti_access_token",
        value=access_token,
        max_age=AUTH_CONFIG["ACCESS_TOKEN_MAX_AGE"],
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="Lax"
    )
    
    # Set refresh token cookie if provided
    if refresh_token:
        response.set_cookie(
            key="smriti_refresh_token", 
            value=refresh_token,
            max_age=AUTH_CONFIG["REFRESH_TOKEN_MAX_AGE"],
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="Lax"
        )


def clear_auth_cookies(response: JSONResponse):
    """
    Clear authentication cookies by setting them to expire immediately.
    
    Args:
        response: FastAPI response object
    """
    response.set_cookie(
        key="smriti_access_token",
        value="",
        expires=0,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="Lax"
    )
    
    response.set_cookie(
        key="smriti_refresh_token",
        value="",
        expires=0,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="Lax"
    )