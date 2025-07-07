"""
Unified FastAPI application for Smriti.

This module combines both the web interface and API functionality.
"""
import os
import uuid
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.db.database import init_db, get_db
from app.repositories import user_repository
from app.utils.jwt_utils import verify_access_token, verify_refresh_token, generate_access_token


class UTCJSONResponse(JSONResponse):
    """Custom JSON response that properly serializes datetime objects with UTC timezone."""
    
    def render(self, content: Any) -> bytes:
        import json
        from datetime import datetime
        
        def default(obj):
            if isinstance(obj, datetime):
                # Ensure the datetime is timezone-aware UTC
                if obj.tzinfo is None:
                    # Assume naive datetime is UTC
                    obj = obj.replace(tzinfo=timezone.utc)
                else:
                    # Convert to UTC if it has timezone info
                    obj = obj.astimezone(timezone.utc)
                # Return ISO format with 'Z' suffix for proper timezone handling
                return obj.isoformat().replace('+00:00', 'Z')
            return str(obj)
        
        return json.dumps(content, default=default, ensure_ascii=False).encode("utf-8")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered emotional and cognitive journaling assistant",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
)

# Configure session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET", "fallback-secret-key")
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Flash message helpers
def flash(request: Request, category: str, message: str):
    """Add a flash message to the session."""
    request.session.setdefault("_flashes", []).append((category, message))

def pop_flashes(request: Request) -> List[tuple]:
    """Get and clear all flash messages from the session."""
    return request.session.pop("_flashes", [])

# JWT Authentication helpers
def get_current_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from JWT tokens in cookies.
    
    Returns user ID if valid token exists, None otherwise.
    """
    # Try access token first
    access_token = request.cookies.get('smriti_access_token')
    print(f"DEBUG: Access token present: {bool(access_token)}")
    if access_token:
        user_data = verify_access_token(access_token)
        print(f"DEBUG: Access token verification result: {bool(user_data)}")
        if user_data:
            print(f"DEBUG: Extracted user ID from access token: {user_data['sub']}")
            return user_data['sub']
    
    # Try refresh token if access token failed
    refresh_token = request.cookies.get('smriti_refresh_token')
    print(f"DEBUG: Refresh token present: {bool(refresh_token)}")
    if refresh_token:
        user_id = verify_refresh_token(refresh_token)
        print(f"DEBUG: Refresh token verification result: {bool(user_id)}")
        if user_id:
            print(f"DEBUG: Extracted user ID from refresh token: {user_id}")
            return user_id
    
    print("DEBUG: No valid JWT tokens found")
    return None

def require_auth(request: Request) -> str:
    """
    Require authentication and return user ID.
    
    Returns user ID if authenticated, raises redirect to login if not.
    """
    user_id = get_current_user_id(request)
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        raise HTTPException(status_code=307, detail="Authentication required", headers={"Location": "/login"})
    return user_id

# Helper function to get user profile
def get_user_profile_data(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Get user profile information."""
    try:
        from app.repositories import user_repository
        from uuid import UUID
        
        user_profile = user_repository.get_user_profile(db, UUID(user_id))
        if user_profile:
            return {
                "user_id": str(user_profile.user_id),
                "display_name": user_profile.display_name,
                "language_preference": user_profile.language_preference
            }
    except Exception as e:
        print(f"Error getting user profile: {e}")
    return None

# Helper function to get user sessions
def get_user_sessions_data(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """Get user sessions."""
    try:
        from app.repositories import session_repository
        from uuid import UUID
        
        sessions = session_repository.get_user_sessions(db, UUID(user_id))
        return [
            {
                "id": str(session.id),
                "user_id": str(session.user_id),
                "raw_transcript": session.raw_transcript,
                "duration_seconds": session.duration_seconds,
                "created_at": session.created_at.isoformat(),
                "is_processed": session.is_processed
            }
            for session in sessions
        ]
    except Exception as e:
        print(f"Error getting user sessions: {e}")
    return []

# Helper function to get user reflections
def get_user_reflections_data(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """Get user reflections."""
    try:
        from app.repositories import reflection_repository
        from uuid import UUID
        
        reflections = reflection_repository.get_user_reflections(db, UUID(user_id))
        return [
            {
                "id": str(reflection.id),
                "user_id": str(reflection.user_id),
                "generated_text": reflection.generated_text,
                "generated_at": reflection.generated_at,
                "feedback": reflection.feedback,
                "is_viewed": reflection.is_viewed
            }
            for reflection in reflections
        ]
    except Exception as e:
        print(f"Error fetching reflections: {e}")
    return []

# Helper function to check unprocessed edges
def check_unprocessed_edges(user_id: str, db: Session) -> bool:
    """Check if user has unprocessed edges."""
    try:
        from app.repositories import edge_repository
        from uuid import UUID
        
        edges = edge_repository.get_unprocessed_edges(db, UUID(user_id))
        return len(edges) > 0
    except Exception as e:
        print(f"Error checking unprocessed edges: {e}")
    return False

# HTML Routes (defined before API mounting)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Render homepage with login/signup or redirect to journal if logged in."""
    # Check if user is already logged in via JWT or session
    user_id = get_current_user_id(request)
    if not user_id:
        # Fallback to session-based check
        user_id = request.session.get("user_id")
    
    if user_id:
        # User is logged in, redirect to journal
        return RedirectResponse(url="/journal", status_code=303)
    
    flashes = pop_flashes(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "flashes": flashes
    })

@app.get("/journal", response_class=HTMLResponse)
async def journal_page(request: Request, db: Session = Depends(get_db)):
    """Render the voice journal interface."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access the journal')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    # Check if user is returning (has previous sessions)
    sessions = get_user_sessions_data(user_id, db)
    is_returning_user = len(sessions) > 0
    
    return templates.TemplateResponse("journal.html", {
        "request": request,
        "user_id": user_id,
        "display_name": display_name,
        "is_returning_user": is_returning_user
    })

@app.get("/entries", response_class=HTMLResponse)
async def entries_page(request: Request, db: Session = Depends(get_db)):
    """Render the journal entries page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to view your entries')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    return templates.TemplateResponse("entries.html", {
        "request": request,
        "user_id": user_id,
        "display_name": display_name
    })

@app.get("/reflections", response_class=HTMLResponse)
async def reflections_page(request: Request, db: Session = Depends(get_db)):
    """Render the clean reflections page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to view your reflections')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    # Get reflections
    reflections = get_user_reflections_data(user_id, db)
    
    return templates.TemplateResponse("clean_reflections.html", {
        "request": request,
        "user_id": user_id,
        "display_name": display_name,
        "reflections": reflections
    })

@app.get("/oauth-success", response_class=HTMLResponse)
async def oauth_success(request: Request):
    """OAuth success page that closes popup and refreshes parent window."""
    return templates.TemplateResponse("oauth_success.html", {
        "request": request
    })

@app.get("/generate-reflection", response_class=HTMLResponse)
async def generate_reflection_page(request: Request, db: Session = Depends(get_db)):
    """Show the manual reflection generation page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to generate reflections')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    # Check if user has unprocessed edges
    has_edges = check_unprocessed_edges(user_id, db)
    
    return templates.TemplateResponse("generate_reflection_page.html", {
        "request": request,
        "user_id": user_id,
        "display_name": display_name,
        "has_unprocessed_edges": has_edges
    })

# @app.post("/generate-reflection/process", response_class=HTMLResponse)
# async def process_reflection_generation(request: Request, db: Session = Depends(get_db)):
#     """OLD ENDPOINT - REPLACED BY SINGLE-PAGE AJAX SOLUTION
#     
#     This endpoint was used for the old two-page reflection generation flow.
#     Now replaced by the single-page solution using /api/v1/reflections/generate
#     """
#     pass

@app.get("/simple-reflections", response_class=HTMLResponse)
async def simple_reflections_page(request: Request, db: Session = Depends(get_db)):
    """Render a simplified reflections page with direct database access."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to view your reflections')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    return templates.TemplateResponse("reflections.html", {
        "request": request,
        "user_id": user_id,
        "display_name": display_name
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    flashes = pop_flashes(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "flashes": flashes
    })

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Handle user login with JWT authentication."""
    print(f"DEBUG: Login attempt for email: {email}")
    
    if not email or not password:
        flash(request, 'error', 'Email and password are required.')
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        from app.repositories import user_repository
        from app.schemas.schemas import UserAuthenticate
        from app.utils.jwt_utils import generate_access_token, generate_refresh_token
        
        # Authenticate using existing repository method
        user_auth = UserAuthenticate(email=email, password=password)
        print(f"DEBUG: Attempting authentication for {email}")
        print(f"DEBUG: Database session: {db}")
        print(f"DEBUG: UserAuthenticate object: {user_auth}")
        
        user = user_repository.authenticate_user(db, user_auth)
        print(f"DEBUG: Authentication result: {user}")
        
        if user:
            print(f"DEBUG: Authentication successful for user {user.id}")
            
            # Generate JWT tokens
            access_token = generate_access_token(str(user.id), str(user.email))
            refresh_token = generate_refresh_token(str(user.id))
            print(f"DEBUG: JWT tokens generated successfully")
            
            # Create response and set secure cookies
            response = RedirectResponse(url="/journal", status_code=303)
            
            # Set access token cookie (30 minutes) - secure=False for localhost
            response.set_cookie(
                'smriti_access_token',
                access_token,
                max_age=1800,  # 30 minutes
                httponly=True,
                secure=False,  # False for localhost development
                samesite='lax'
            )
            
            # Set refresh token cookie (90 days) - secure=False for localhost
            response.set_cookie(
                'smriti_refresh_token',
                refresh_token,
                max_age=7776000,  # 90 days
                httponly=True,
                secure=False,  # False for localhost development
                samesite='lax'
            )
            
            print(f"DEBUG: Cookies set, redirecting to journal")
            flash(request, 'success', f'Welcome, {user.email}!')
            return response
        else:
            print(f"DEBUG: Authentication failed for {email}")
            flash(request, 'error', 'Invalid email or password.')
            
    except Exception as e:
        print(f"DEBUG: Login error: {e}")
        import traceback
        traceback.print_exc()
        flash(request, 'error', 'An error occurred during login. Please try again.')
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Show signup page."""
    flashes = pop_flashes(request)
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "flashes": flashes
    })

@app.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    confirm_password: str = Form(...),
    display_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user signup."""
    if not email or not password or not confirm_password or not display_name:
        flash(request, 'error', 'All fields are required.')
        return RedirectResponse(url="/signup", status_code=303)
    
    # Validate password confirmation
    if password != confirm_password:
        flash(request, 'error', 'Passwords do not match.')
        return RedirectResponse(url="/signup", status_code=303)
    
    # Validate password length
    if len(password) < 8:
        flash(request, 'error', 'Password must be at least 8 characters long.')
        return RedirectResponse(url="/signup", status_code=303)
    
    try:
        from app.repositories import user_repository
        from app.schemas.schemas import UserCreate, UserProfileCreate
        from app.utils.auth import hash_password
        from app.utils.jwt_utils import generate_access_token, generate_refresh_token
        
        # Check if user already exists
        existing_user = user_repository.get_user_by_email(db, email)
        if existing_user:
            flash(request, 'error', 'Email already registered. Please use a different email or login.')
            return RedirectResponse(url="/signup", status_code=303)
        
        # Create user with hashed password
        user_create = UserCreate(
            email=email,
            password=password  # The repository will handle hashing
        )
        
        user = user_repository.create_user(db, user_create)
        
        # Create user profile
        profile_create = UserProfileCreate(
            display_name=display_name,
            language="en"
        )
        
        from uuid import UUID
        user_repository.create_user_profile(db, profile_create, UUID(str(user.id)))
        
        # Generate JWT tokens for immediate authentication
        access_token = generate_access_token(str(user.id), str(user.email))
        refresh_token = generate_refresh_token(str(user.id))
        
        # Create response and set secure cookies (matching login flow exactly)
        response = RedirectResponse(url="/journal", status_code=303)
        
        # Set access token cookie (30 minutes) - secure=False for localhost
        response.set_cookie(
            'smriti_access_token',
            access_token,
            max_age=1800,  # 30 minutes
            httponly=True,
            secure=False,  # False for localhost development
            samesite='lax'
        )
        
        # Set refresh token cookie (90 days) - secure=False for localhost
        response.set_cookie(
            'smriti_refresh_token',
            refresh_token,
            max_age=7776000,  # 90 days
            httponly=True,
            secure=False,  # False for localhost development
            samesite='lax'
        )
        
        # Also set session for backward compatibility
        request.session["user_id"] = str(user.id)
        flash(request, 'success', f'Welcome to Smriti, {display_name}!')
        return response
            
    except Exception as e:
        print(f"Signup error: {e}")
        flash(request, 'error', 'An error occurred during registration. Please try again.')
    
    return RedirectResponse(url="/signup", status_code=303)

@app.get("/how-to-use", response_class=HTMLResponse)
async def how_to_use_page(request: Request):
    """Render the how to use page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("how_to_use.html", {
        "request": request
    })

@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request, db: Session = Depends(get_db)):
    """Render the feedback page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user profile info to avoid displaying user ID
    user_profile = get_user_profile_data(user_id, db)
    display_name = user_profile.get('display_name') if user_profile else None
    
    flashes = pop_flashes(request)
    return templates.TemplateResponse("feedback.html", {
        "request": request,
        "flashes": flashes,
        "display_name": display_name,
        "user_id": user_id
    })

@app.post("/feedback", response_class=HTMLResponse)
async def feedback_post(
    request: Request, 
    feedback_type: str = Form(None),
    subject: str = Form(""),
    message: str = Form(""),
    rating: str = Form(None),
    db: Session = Depends(get_db)
):
    """Handle feedback form submission."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    # Debug logging
    print(f"DEBUG: feedback_type='{feedback_type}', subject='{subject}', message='{message}', rating='{rating}'")
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        return RedirectResponse(url="/login", status_code=303)
    
    # Smart validation logic
    has_rating = rating and rating.strip() != ""
    has_feedback_content = (subject and subject.strip()) or (message and message.strip())
    has_feedback_type = feedback_type and feedback_type.strip() != ""
    
    # Case 1: User provided rating - everything else is optional
    if has_rating:
        pass  # Rating submission is valid on its own
    
    # Case 2: User providing feedback - must have type and either subject or message
    elif has_feedback_content:
        if not has_feedback_type:
            flash(request, 'error', 'Please select a feedback type when providing feedback.')
            return RedirectResponse(url="/feedback", status_code=303)
    
    # Case 3: No rating and no feedback content
    else:
        flash(request, 'error', 'Please either provide a rating or share your feedback with us.')
        return RedirectResponse(url="/feedback", status_code=303)
    
    try:
        from app.repositories import feedback_repository, user_repository
        from app.schemas.schemas import UserFeedbackCreate
        from uuid import UUID
        
        # Get user's email from their account
        user = user_repository.get_user(db, UUID(user_id))
        user_email = user.email if user else None
        
        # Convert rating to integer if provided
        rating_int = None
        if rating and rating.strip():
            try:
                rating_int = int(rating)
            except ValueError:
                pass
        
        # Create feedback data with user's email from account
        # For rating-only submissions, use a default feedback type
        final_feedback_type = feedback_type if feedback_type and feedback_type.strip() else "rating_only"
        
        feedback_data = UserFeedbackCreate(
            feedback_type=final_feedback_type,
            subject=subject.strip() if subject.strip() else "",
            message=message.strip() if message.strip() else "",
            rating=rating_int,
            contact_email=user_email
        )
        
        # Save feedback to database
        feedback_repository.create_feedback(db, feedback_data, UUID(user_id))
        
        flash(request, 'success', 'Thank you for your feedback! We appreciate your input.')
        
    except Exception as e:
        print(f"Feedback submission error: {e}")
        flash(request, 'error', 'An error occurred while submitting your feedback. Please try again.')
    
    return RedirectResponse(url="/feedback", status_code=303)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    """Render the settings page."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        return RedirectResponse(url="/login", status_code=303)
    
    # Get user info for the settings page
    user_profile = get_user_profile_data(user_id, db)
    
    flashes = pop_flashes(request)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user_profile,
        "flashes": flashes
    })

@app.post("/settings", response_class=HTMLResponse)
async def settings_post(
    request: Request, 
    action: str = Form(...),
    display_name: str = Form(""),
    db: Session = Depends(get_db)
):
    """Handle settings form submission."""
    # Check JWT authentication first, then fallback to session
    user_id = get_current_user_id(request)
    if not user_id:
        user_id = request.session.get('user_id')
    
    if not user_id:
        flash(request, 'warning', 'Please log in to access this page')
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        from app.repositories import user_repository
        from uuid import UUID
        
        # Convert user_id to UUID
        user_uuid = UUID(user_id)
        
        if action == "delete":
            # Delete user account and all data
            success = user_repository.delete_user_completely(db, user_uuid)
            
            if success:
                # Clear all cookies and session data
                response = RedirectResponse(url="/", status_code=303)
                response.delete_cookie("smriti_access_token")
                response.delete_cookie("smriti_refresh_token")
                request.session.clear()
                return response
            else:
                flash(request, 'error', 'Failed to delete account. Please try again.')
                return RedirectResponse(url="/settings", status_code=303)
        
        elif action == "update":
            # Update display name in user_profile table
            success = user_repository.update_display_name(db, user_uuid, display_name.strip())
            
            if success:
                flash(request, 'success', 'Display name updated successfully!')
            else:
                flash(request, 'error', 'Failed to update display name. Please try again.')
                
    except Exception as e:
        flash(request, 'error', f'Error updating settings: {str(e)}')
    
    return RedirectResponse(url="/settings", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    """Log the user out."""
    # Clear session
    request.session.clear()
    
    # Create redirect response
    response = RedirectResponse(url="/", status_code=303)
    
    # Clear JWT cookies
    response.delete_cookie('smriti_access_token')
    response.delete_cookie('smriti_refresh_token')
    
    flash(request, 'info', 'You have been signed out successfully.')
    return response

# Health check endpoint
@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

# Configure API router to use custom JSON response for proper timezone handling
from fastapi.routing import APIRoute

# Apply custom JSON response to all API routes for timezone-aware serialization
for route in api_v1_router.routes:
    if isinstance(route, APIRoute):
        route.response_class = UTCJSONResponse

# Include API routers (after HTML routes)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Initialize database tables at startup
@app.on_event("startup")
async def startup_event():
    """Initialize application at startup."""
    init_db()