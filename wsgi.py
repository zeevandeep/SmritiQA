"""
WSGI wrapper for FastAPI application to work with Gunicorn.

This creates a WSGI-compatible interface for our FastAPI application.
"""
import os
import sys
import uvicorn
import socket
import threading
from app.main import app as fastapi_app

# This is needed for Gunicorn to find the app
app = fastapi_app

if __name__ == "__main__":
    # Run uvicorn directly
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )