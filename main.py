"""
Main entry point for the Smriti FastAPI application.
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import API routes
try:
    from app.api.v1.routes import sessions, users, auth, google_oauth, health
except ImportError as e:
    print(f"Warning: Could not import API routes: {e}")
    sessions = users = auth = google_oauth = health = None

# Create FastAPI app
app = FastAPI(
    title="Smriti",
    description="AI-powered emotional intelligence journaling assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes if available
if health:
    app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
if auth:
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
if users:
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
if sessions:
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
if google_oauth:
    app.include_router(google_oauth.router, prefix="/api/v1/auth/google", tags=["google-auth"])

@app.get("/")
async def root():
    """Root endpoint returning basic info."""
    return {"message": "Smriti API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Smriti API is operational"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )