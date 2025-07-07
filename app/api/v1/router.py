"""
API v1 router for the Smriti application.

This module defines the main router for the v1 API and includes all route modules.
"""
from fastapi import APIRouter

from app.api.v1.routes import users, sessions, health, nodes, edges, reflections, audio, auth, google_oauth

# Create main v1 router with custom JSON response for proper timezone handling
router = APIRouter()

# Include route modules
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(google_oauth.router)
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
router.include_router(edges.router, prefix="/edges", tags=["edges"])
router.include_router(reflections.router, prefix="/reflections", tags=["reflections"])
router.include_router(audio.router, prefix="/audio", tags=["audio"])
router.include_router(health.router, prefix="/health", tags=["health"])