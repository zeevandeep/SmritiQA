"""
Authentication endpoints for JWT token management.

This module provides endpoints for token refresh and authentication operations.
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.utils.jwt_utils import verify_refresh_token, generate_access_token, revoke_refresh_token
from app.repositories import user_repository
from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter()

@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Refresh an access token using a valid refresh token.
    
    This endpoint allows clients to get a new access token
    without requiring the user to log in again.
    """
    # Extract refresh token from HTTP-only cookie
    refresh_token = request.cookies.get('smriti_refresh_token')
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify the refresh token
    user_id = verify_refresh_token(refresh_token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user information
    db: Session = next(get_db())
    try:
        user = user_repository.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate new access token
        new_access_token = generate_access_token(user_id, user.email)
        
        # Create response with new access token cookie
        response = JSONResponse({
            "message": "Token refreshed successfully",
            "access_token": new_access_token  # Also return in body for client-side use
        })
        
        # Set new access token cookie
        response.set_cookie(
            'smriti_access_token',
            new_access_token,
            max_age=1800,  # 30 minutes
            httponly=True,
            secure=True,
            samesite='lax'
        )
        
        return response
        
    except Exception as e:
        print(f"Error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
    finally:
        db.close()

@router.post("/logout")
async def logout(request: Request):
    """
    Log out the user by revoking their refresh token.
    
    This endpoint invalidates the current refresh token
    and clears authentication cookies.
    """
    # Extract refresh token from cookie
    refresh_token = request.cookies.get('smriti_refresh_token')
    
    if refresh_token:
        # Revoke the refresh token
        revoke_refresh_token(refresh_token)
    
    # Create response and clear cookies
    response = JSONResponse({"message": "Logged out successfully"})
    
    # Clear authentication cookies
    response.set_cookie('smriti_access_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    response.set_cookie('smriti_refresh_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    
    return response

@router.post("/logout-all")
async def logout_all_devices(request: Request):
    """
    Log out the user from all devices by revoking all refresh tokens.
    
    This endpoint invalidates all refresh tokens for the user,
    effectively logging them out from all devices.
    """
    # Extract refresh token to identify the user
    refresh_token = request.cookies.get('smriti_refresh_token')
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get user ID from refresh token
    user_id = verify_refresh_token(refresh_token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Import the revoke function
    from app.utils.jwt_utils import revoke_all_user_tokens
    
    # Revoke all tokens for this user
    success = revoke_all_user_tokens(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke tokens"
        )
    
    # Create response and clear cookies
    response = JSONResponse({"message": "Logged out from all devices successfully"})
    
    # Clear authentication cookies
    response.set_cookie('smriti_access_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    response.set_cookie('smriti_refresh_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
    
    return response