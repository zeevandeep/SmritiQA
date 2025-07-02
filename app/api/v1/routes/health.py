"""
Health check routes for API v1.
"""
from fastapi import APIRouter

from app.schemas.schemas import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
def health_check():
    """
    Check API health status.
    
    Returns:
        HealthCheck: API health status information
    """
    return {
        "status": "healthy",
        "version": "1.0.0"
    }