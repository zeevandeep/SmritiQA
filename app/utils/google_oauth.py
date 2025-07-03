"""
Google OAuth utilities for secure authentication integration.
Implements secure ID token validation as per OAuth 2.0 best practices.
"""
import os
import logging
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

import google.auth.transport.requests
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException

# Setup logging
logger = logging.getLogger(__name__)

class GoogleOAuthHandler:
    """Handles Google OAuth 2.0 authentication flow with secure ID token validation."""
    
    def __init__(self):
        """Initialize Google OAuth handler with environment configuration."""
        self.client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '__PLACEHOLDER__')
        self.client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '__PLACEHOLDER__')
        
        # Validate configuration
        if '__PLACEHOLDER__' in self.client_id or '__PLACEHOLDER__' in self.client_secret:
            logger.warning("Google OAuth credentials not properly configured - using placeholders")
    
    def _resolve_redirect_uri(self, request) -> str:
        """
        Resolve the appropriate redirect URI based on environment and request context.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            str: The appropriate redirect URI for the current environment
            
        Raises:
            RuntimeError: If redirect URI cannot be determined
        """
        # Priority order:
        # 1. Explicit ENV variable (development/production)
        # 2. Domain-based auto-detection
        # 3. Fallback to error with helpful message
        
        env = os.getenv("ENV", None)
        if env == "production":
            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI_PROD")
            if redirect_uri:
                logger.info(f"[OAUTH] Using production redirect URI from ENV: {redirect_uri}")
                return redirect_uri
        elif env == "development":
            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI_DEV")
            if redirect_uri:
                logger.info(f"[OAUTH] Using development redirect URI from ENV: {redirect_uri}")
                return redirect_uri
        
        # Fallback to domain-based detection
        host = request.headers.get("host", "")
        logger.info(f"[OAUTH] Auto-detecting environment based on host: {host}")
        
        if "localhost" in host or ".replit.dev" in host or "--dev" in host:
            # Development environment
            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI_DEV")
            if redirect_uri:
                logger.info(f"[OAUTH] Auto-detected development environment, using: {redirect_uri}")
                return redirect_uri
            else:
                logger.warning("[OAUTH] Development environment detected but GOOGLE_REDIRECT_URI_DEV not set")
        else:
            # Production environment
            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI_PROD")
            if redirect_uri:
                logger.info(f"[OAUTH] Auto-detected production environment, using: {redirect_uri}")
                return redirect_uri
            else:
                logger.warning("[OAUTH] Production environment detected but GOOGLE_REDIRECT_URI_PROD not set")
        
        # If we get here, configuration is incomplete
        raise RuntimeError(
            "OAuth redirect URI could not be determined.\n"
            "Set ENV=production or ENV=development in your Replit secrets, "
            "and ensure GOOGLE_REDIRECT_URI_DEV / GOOGLE_REDIRECT_URI_PROD are set accordingly."
        )
    
    def validate_configuration(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return (
            bool(self.client_id) and '__PLACEHOLDER__' not in self.client_id and
            bool(self.client_secret) and '__PLACEHOLDER__' not in self.client_secret
        )
    
    def get_authorization_url(self, request) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL with secure state parameter.
        
        Args:
            request: FastAPI Request object for environment detection
        
        Returns:
            Tuple of (authorization_url, state_parameter)
            
        Raises:
            RuntimeError: If OAuth credentials are not configured
        """
        if not self.validate_configuration():
            raise RuntimeError("Google OAuth environment variables not set properly")
        
        try:
            # Resolve the appropriate redirect URI for current environment
            redirect_uri = self._resolve_redirect_uri(request)
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=[
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile'
                ]
            )
            flow.redirect_uri = redirect_uri
            
            # Generate secure state parameter
            state = secrets.token_urlsafe(32)
            
            # Get authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state
            )
            
            logger.info(f"[OAUTH DEBUG] Authorization URL redirect_uri: {redirect_uri}")
            logger.info(f"[OAUTH DEBUG] Client ID: {self.client_id[:20]}...")
            logger.info(f"[OAUTH DEBUG] Full authorization URL: {authorization_url[:200]}...")
            logger.info("Generated Google OAuth authorization URL")
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate Google OAuth URL: {e}")
            raise
    
    def exchange_code_for_user_info(self, code: str, state: str, request) -> Dict[str, Any]:
        """
        Exchange authorization code for validated user information.
        
        Args:
            code: Authorization code from Google
            state: State parameter for CSRF protection
            request: FastAPI Request object for environment detection
            
        Returns:
            Dictionary containing validated user information
            
        Raises:
            HTTPException: On validation failures or security issues
        """
        if not self.validate_configuration():
            raise HTTPException(403, "Google OAuth not properly configured")
        
        try:
            # Resolve the appropriate redirect URI for current environment
            redirect_uri = self._resolve_redirect_uri(request)
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=[
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile'
                ],
                state=state
            )
            flow.redirect_uri = redirect_uri
            
            # Exchange code for tokens
            logger.info("Exchanging authorization code for tokens")
            flow.fetch_token(code=code)
            
            # Get ID token from credentials
            credentials = flow.credentials
            id_token = getattr(credentials, 'id_token', None)
            
            if not id_token:
                logger.error("No ID token received from Google")
                raise HTTPException(403, "Invalid Google OAuth response")
            
            # Validate ID token - CRITICAL SECURITY STEP
            logger.info("Validating Google ID token")
            id_info = google.oauth2.id_token.verify_oauth2_token(
                id_token,
                google.auth.transport.requests.Request(),
                self.client_id
            )
            
            # Verify email is verified by Google
            if not id_info.get("email_verified", False):
                logger.warning(f"Google account email not verified: {id_info.get('email')}")
                raise HTTPException(403, "Google account email not verified")
            
            # Verify issuer
            if id_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"Invalid issuer in ID token: {id_info.get('iss')}")
                raise HTTPException(403, "Invalid token issuer")
            
            # Extract validated user information
            user_info = {
                'email': id_info.get('email'),
                'name': id_info.get('name'),
                'picture': id_info.get('picture'),
                'given_name': id_info.get('given_name'),
                'family_name': id_info.get('family_name'),
                'verified_email': id_info.get('email_verified', False),
                'google_id': id_info.get('sub')  # Google's unique user ID
            }
            
            # Validate required fields
            if not user_info['email']:
                logger.error("No email address in validated ID token")
                raise HTTPException(403, "Email address required for authentication")
            
            logger.info(f"Successfully validated Google OAuth for user: {user_info['email']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Google OAuth exchange failed: {e}")
            if "ValueError" in str(type(e)):
                logger.warning(f"Google token verification failed: {e}")
                raise HTTPException(403, "Invalid Google authentication token")
            elif "google.auth" in str(type(e)):
                logger.warning(f"Google auth library error: {e}")
                raise HTTPException(403, "Google authentication failed")
            else:
                logger.error(f"Unexpected Google OAuth error: {e}")
                raise HTTPException(500, "Google authentication temporarily unavailable")


def log_oauth_event(email: str, request, had_existing_password: bool = False):
    """
    Log OAuth authentication events for security audit.
    
    Args:
        email: User email address
        request: FastAPI request object
        had_existing_password: Whether user had existing password-based account
    """
    try:
        # Extract request information
        ip_address = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create audit log entry
        log_entry = (
            f"[SECURITY] Google OAuth account link detected:\n"
            f"Email: {email}\n"
            f"Timestamp: {timestamp}\n"
            f"IP: {ip_address}\n"
            f"User-Agent: {user_agent}\n"
            f"Existing password: {had_existing_password}\n"
        )
        
        # Log to application logger
        logger.info(log_entry.replace('\n', ' | '))
        
        # TODO: In production, also write to separate audit log file
        # with log rotation (logs/auth_audit.log)
        
    except Exception as e:
        logger.error(f"Failed to log OAuth event: {e}")


# Configuration validation for startup
def validate_google_oauth_config() -> bool:
    """Validate Google OAuth configuration at application startup."""
    handler = GoogleOAuthHandler()
    return handler.validate_configuration()