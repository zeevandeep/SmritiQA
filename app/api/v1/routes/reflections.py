"""
Reflection management routes for API v1.
"""
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import reflection_repository, user_repository
from app.services.reflection_processor import process_unprocessed_edges_for_reflection, generate_single_reflection_for_user
from app.schemas.schemas import Reflection as ReflectionSchema, FeedbackRequest
from app.models.models import Reflection, Edge, User
from app.utils.api_auth import get_current_user_from_jwt, verify_user_access

router = APIRouter()


@router.get("/user/{user_id}", response_model=List[ReflectionSchema])
def read_user_reflections(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_viewed: bool = True,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Get reflections for a user.
    
    Args:
        user_id: ID of the user.
        skip: Number of reflections to skip.
        limit: Maximum number of reflections to return.
        include_viewed: Whether to include reflections that have been viewed.
        db: Database session.
        current_user_id: Authenticated user ID from JWT.
        
    Returns:
        List[Reflection]: List of reflections.
        
    Raises:
        HTTPException: If the user is not found or access is denied.
    """
    # Verify user has access to this data
    verify_user_access(str(user_id), current_user_id)
    
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return reflection_repository.get_user_reflections(
        db, 
        user_id=user_id, 
        skip=skip, 
        limit=limit,
        include_viewed=include_viewed
    )


@router.post("/generate-batch", response_model=Dict[str, Any])
def generate_reflections(
    batch_size_per_user: int = Query(default=5, ge=1, le=20),
    overall_batch_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Generate reflections for all users from unprocessed edges.
    
    This endpoint processes edges where is_processed=False to build chains
    of connected nodes and generate reflections based on these chains.
    
    Args:
        batch_size_per_user: Maximum number of unprocessed edges to process per user.
        overall_batch_size: Maximum total number of unprocessed edges to process.
        db: Database session.
        
    Returns:
        Dict: Processing statistics.
    """
    return process_unprocessed_edges_for_reflection(
        db,
        batch_size_per_user=batch_size_per_user,
        overall_batch_size=overall_batch_size
    )


@router.get("/stats", response_model=Dict[str, Any])
def get_reflection_stats(db: Session = Depends(get_db)):
    """
    Get statistics about reflections and edges.
    
    Returns:
        Dict: Statistics about reflections and edges.
    """
    # Get total number of reflections
    reflection_count = db.query(Reflection).count()
    
    # Get total number of edges
    edge_count = db.query(Edge).count()
    
    # Get number of processed edges
    processed_edge_count = db.query(Edge).filter(Edge.is_processed == True).count()
    
    # Get number of unprocessed edges
    unprocessed_edge_count = db.query(Edge).filter(Edge.is_processed == False).count()
    
    # Get user count with reflections
    users_with_reflections = db.query(Reflection.user_id).distinct().count()
    
    # Get total user count
    total_users = db.query(User).count()
    
    return {
        "reflection_count": reflection_count,
        "edge_count": edge_count,
        "processed_edge_count": processed_edge_count,
        "unprocessed_edge_count": unprocessed_edge_count,
        "users_with_reflections": users_with_reflections,
        "total_users": total_users,
        "statistics_generated_at": datetime.now().isoformat()
    }


@router.post("/generate", response_model=Dict[str, Any])
def generate_session_reflection(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Generate a single reflection for the current authenticated user.
    
    This endpoint processes the strongest unprocessed edge for the authenticated user
    to build a chain of connected nodes and generate one reflection.
    
    Args:
        request: FastAPI request object.
        db: Database session.
        current_user_id: Authenticated user ID from JWT.
        
    Returns:
        Dict: Structured response with reflection data or error information.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Use the authenticated user ID from JWT
    user_id = current_user_id
    
    try:
        # Convert to UUID
        user_uuid = UUID(user_id)
        
        # Verify that the user exists
        db_user = user_repository.get_user(db, user_id=user_uuid)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate reflection
        result = generate_single_reflection_for_user(db, user_uuid)
        
        # Structure the response
        if result.get('reflections_created', 0) > 0:
            reflection_data = result.get('reflection')
            if reflection_data:
                return {
                    "success": True,
                    "reflection_text": reflection_data['generated_text'],
                    "reflection_id": reflection_data['id'],
                    "generated_at": reflection_data['generated_at']
                }
            else:
                return {
                    "success": False,
                    "error_code": "no_reflection_data",
                    "message": "Reflection was created but data could not be retrieved"
                }
        else:
            return {
                "success": False,
                "error_code": "no_patterns",
                "message": "No new patterns found. Try journaling more."
            }
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        return {
            "success": False,
            "error_code": "system_error",
            "message": "There is some issue, please try again later"
        }


@router.post("/user/{user_id}/generate", response_model=Dict[str, Any])
def generate_reflections_for_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Generate a single reflection for a specific user from their strongest unprocessed edge.
    
    This endpoint processes the strongest unprocessed edge for a user to build a chain
    of connected nodes and generate one reflection.
    
    Args:
        user_id: ID of the user to generate a reflection for.
        db: Database session.
        
    Returns:
        Dict: Processing statistics including 'reflections_created' count.
        
    Raises:
        HTTPException: If the user is not found.
    """
    # Verify that the user exists
    db_user = user_repository.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return generate_single_reflection_for_user(db, user_id)


@router.post("/{reflection_id}/feedback", response_model=ReflectionSchema)
def add_reflection_feedback(
    reflection_id: UUID,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Provide feedback on a reflection.
    
    Args:
        reflection_id: ID of the reflection to update.
        feedback: Feedback data.
        db: Database session.
        current_user_id: Authenticated user ID from JWT.
        
    Returns:
        Reflection: Updated reflection.
        
    Raises:
        HTTPException: If the reflection is not found or access is denied.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[FEEDBACK] Starting feedback submission for reflection {reflection_id}, value: {feedback.feedback}")
        
        # First get the reflection to verify ownership
        db_reflection = reflection_repository.get_reflection(db, reflection_id)
        
        if db_reflection is None:
            logger.error(f"[FEEDBACK] Reflection {reflection_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reflection not found"
            )
        
        logger.info(f"[FEEDBACK] Found reflection {reflection_id}, user: {db_reflection.user_id}")
        
        # Verify user has access to this reflection
        verify_user_access(str(db_reflection.user_id), current_user_id)
        logger.info(f"[FEEDBACK] User access verified for {current_user_id}")
        
        # Add the feedback
        updated_reflection = reflection_repository.add_reflection_feedback(
            db, 
            reflection_id=reflection_id, 
            feedback=feedback.feedback
        )
        
        logger.info(f"[FEEDBACK] Successfully added feedback {feedback.feedback} to reflection {reflection_id}")
        return updated_reflection
        
    except Exception as e:
        logger.error(f"[FEEDBACK ERROR] Failed to add feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add feedback: {str(e)}"
        )


@router.post("/{reflection_id}/mark-reflected", response_model=ReflectionSchema)
def mark_reflection_viewed(
    reflection_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Mark a reflection as having been reflected upon by the user.
    
    Args:
        reflection_id: ID of the reflection to mark.
        db: Database session.
        
    Returns:
        Reflection: Updated reflection.
        
    Raises:
        HTTPException: If the reflection is not found.
    """
    db_reflection = reflection_repository.mark_reflection_viewed(db, reflection_id=reflection_id)
    
    if db_reflection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found"
        )
    
    return db_reflection


@router.patch("/{reflection_id}/mark-viewed", response_model=ReflectionSchema)
def mark_reflection_as_viewed(
    reflection_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Mark a reflection as viewed (for UI purposes).
    
    Args:
        reflection_id: ID of the reflection to mark as viewed.
        db: Database session.
        
    Returns:
        Reflection: Updated reflection.
        
    Raises:
        HTTPException: If the reflection is not found.
    """
    db_reflection = reflection_repository.mark_reflection_viewed(db, reflection_id=reflection_id)
    
    if db_reflection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found"
        )
    
    return db_reflection