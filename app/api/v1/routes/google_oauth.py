"""
Google OAuth API routes for authentication integration.
Implements secure OAuth 2.0 flow with proper state management and token validation.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.utils.google_oauth import GoogleOAuthHandler
from app.services.google_user_service import find_or_create_google_user
from app.utils.jwt_utils import generate_access_token, generate_refresh_token

logger = logging.getLogger(__name__)

# Initialize router and OAuth handler
router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])
oauth_handler = GoogleOAuthHandler()


@router.get("/login")
async def google_login(request: Request, response: Response):
    """
    Initiate Google OAuth login flow.
    Generates authorization URL and stores state in session for CSRF protection.
    """
    try:
        # Check if Google OAuth is configured
        if not oauth_handler.validate_configuration():
            logger.warning("Google OAuth attempted with incomplete configuration")
            return RedirectResponse(url="/login?error=google_oauth_unavailable", status_code=302)
        
        # Generate authorization URL with secure state
        authorization_url, state = oauth_handler.get_authorization_url(request)
        
        # Store state in session for CSRF protection
        request.session["google_oauth_state"] = state
        
        # Enhanced logging for debugging
        logger.info(f"[OAUTH DEBUG] Generated Google OAuth authorization URL")
        logger.info(f"[OAUTH DEBUG] Generated state: {state}")
        logger.info(f"[OAUTH DEBUG] Stored in session: {request.session.get('google_oauth_state')}")
        logger.info(f"[OAUTH DEBUG] Session ID: {request.session.get('session_id', 'no-session-id')}")
        logger.info(f"[OAUTH DEBUG] Redirect URI will be auto-detected based on environment")
        logger.info(f"[OAUTH DEBUG] Client ID: {oauth_handler.client_id[:20]}...")
        logger.info(f"[OAUTH DEBUG] Full authorization URL: {authorization_url}")
        
        return RedirectResponse(url=authorization_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate Google OAuth: {e}")
        return RedirectResponse(url="/login?error=oauth_init_failed", status_code=302)


@router.get("/callback")
async def google_callback(
    request: Request, 
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Validates state, exchanges code for user info, and creates/links user account.
    """
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"Google OAuth error: {error}")
            logger.error(f"Full callback URL: {request.url}")
            return RedirectResponse(url=f"/login?error=google_oauth_error&details={error}", status_code=302)
        
        # Validate required parameters
        if not code or not state:
            logger.warning("Google OAuth callback with missing parameters")
            return RedirectResponse(url="/login?error=oauth_invalid_response", status_code=302)
        
        # Validate state parameter (CSRF protection)
        stored_state = request.session.get("google_oauth_state")
        logger.info(f"[OAUTH DEBUG] Callback - received state: {state}")
        logger.info(f"[OAUTH DEBUG] Callback - stored state: {stored_state}")
        logger.info(f"[OAUTH DEBUG] Callback - session keys: {list(request.session.keys())}")
        logger.info(f"[OAUTH DEBUG] Callback - session ID: {request.session.get('session_id', 'no-session-id')}")
        
        if not stored_state or stored_state != state:
            logger.warning(f"[OAUTH DEBUG] Google OAuth state mismatch. Expected: {stored_state}, Got: {state}")
            logger.warning(f"[OAUTH DEBUG] Session contents: {dict(request.session)}")
            return RedirectResponse(url="/login?error=oauth_security_failed", status_code=302)
        
        # Clear state from session
        request.session.pop("google_oauth_state", None)
        
        # Exchange code for validated user information
        logger.info("Exchanging Google OAuth code for user information")
        google_user_info = oauth_handler.exchange_code_for_user_info(code, state, request)
        
        # Validate that we received user info
        if not google_user_info:
            logger.error("Failed to retrieve user information from Google OAuth")
            return RedirectResponse(url="/login?error=oauth_user_info_failed", status_code=302)
        
        if not google_user_info.get('email'):
            logger.error("Google OAuth returned user info without email")
            return RedirectResponse(url="/login?error=oauth_email_missing", status_code=302)
        
        # Find or create user account
        user = await find_or_create_google_user(google_user_info, db, request)
        
        # Generate JWT tokens
        access_token = generate_access_token(str(user.id), str(user.email))
        refresh_token = generate_refresh_token(str(user.id))
        
        # For popup OAuth flow, redirect to a success page that closes the popup
        response = RedirectResponse(url="/oauth-success", status_code=302)
        
        # Access token (shorter expiry)
        response.set_cookie(
            key="smriti_access_token",
            value=access_token,
            max_age=3600,  # 1 hour
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        # Refresh token (longer expiry)
        response.set_cookie(
            key="smriti_refresh_token", 
            value=refresh_token,
            max_age=7 * 24 * 3600,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        logger.info(f"Successfully authenticated user via Google OAuth: {user.email}")
        
        return response
        
    except HTTPException as e:
        # Handle known HTTP exceptions from OAuth handler
        logger.warning(f"Google OAuth validation failed: {e.detail}")
        return RedirectResponse(url="/login?error=oauth_validation_failed", status_code=302)
        
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth callback: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return RedirectResponse(url="/login?error=oauth_unexpected_error", status_code=302)


@router.get("/status")
async def google_oauth_status():
    """
    Check Google OAuth configuration status.
    Useful for debugging and health checks.
    """
    try:
        is_configured = oauth_handler.validate_configuration()
        
        return {
            "google_oauth_configured": is_configured,
            "configuration_status": "ready" if is_configured else "incomplete",
            "message": "Google OAuth is properly configured" if is_configured 
                      else "Google OAuth requires GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables"
        }
        
    except Exception as e:
        logger.error(f"Error checking Google OAuth status: {e}")
        return {
            "google_oauth_configured": False,
            "configuration_status": "error", 
            "message": f"Error checking configuration: {str(e)}"
        }


@router.get("/stats")
async def google_oauth_stats(db: Session = Depends(get_db)):
    """
    Get Google OAuth usage statistics.
    Requires authentication in production.
    """
    try:
        from app.services.google_user_service import get_google_oauth_stats
        stats = get_google_oauth_stats(db)
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting Google OAuth stats: {e}")
        raise HTTPException(500, "Unable to retrieve OAuth statistics")