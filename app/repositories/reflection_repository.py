"""
Reflection repository for database operations related to AI-generated reflections.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.models import Reflection, Node, Edge
from app.schemas.schemas import ReflectionCreate


def create_reflection(db: DbSession, reflection: ReflectionCreate) -> Reflection:
    """
    Create a new reflection.
    
    Args:
        db: Database session.
        reflection: Data for the new reflection.
        
    Returns:
        Created Reflection object.
    """
    db_reflection = Reflection(
        user_id=reflection.user_id,
        node_ids=reflection.node_ids,
        edge_ids=reflection.edge_ids,
        generated_text=reflection.generated_text,
        confidence_score=reflection.confidence_score,
        is_reflected=False
    )
    db.add(db_reflection)
    db.commit()
    db.refresh(db_reflection)
    return db_reflection


def get_reflection(db: DbSession, reflection_id: UUID) -> Optional[Reflection]:
    """
    Get a reflection by ID.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to retrieve.
        
    Returns:
        Reflection object if found, None otherwise.
    """
    return db.query(Reflection).filter(Reflection.id == reflection_id).first()


def get_user_reflections(
    db: DbSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_viewed: bool = True
) -> List[Reflection]:
    """
    Get reflections for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of reflections to skip.
        limit: Maximum number of reflections to return.
        include_viewed: Whether to include reflections that have been viewed.
        
    Returns:
        List of Reflection objects.
    """
    query = db.query(Reflection).filter(Reflection.user_id == user_id)
    
    if not include_viewed:
        query = query.filter(Reflection.is_reflected == False)
    
    return query.order_by(Reflection.generated_at.desc()).offset(skip).limit(limit).all()


def get_user_reflection_count(db: DbSession, user_id: UUID) -> int:
    """
    Get the total count of reflections for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        
    Returns:
        Total count of reflections for the user.
    """
    return db.query(Reflection).filter(Reflection.user_id == user_id).count()


def get_reflections(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    include_viewed: bool = True
) -> List[Reflection]:
    """
    Get all reflections across users.
    
    Args:
        db: Database session.
        skip: Number of reflections to skip.
        limit: Maximum number of reflections to return.
        include_viewed: Whether to include reflections that have been viewed.
        
    Returns:
        List of Reflection objects.
    """
    query = db.query(Reflection)
    
    if not include_viewed:
        query = query.filter(Reflection.is_reflected == False)
    
    return query.order_by(Reflection.generated_at.desc()).offset(skip).limit(limit).all()


def mark_reflection_viewed(db: DbSession, reflection_id: UUID) -> Optional[Reflection]:
    """
    Mark a reflection as having been viewed by the user.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to mark.
        
    Returns:
        Updated Reflection object if found, None otherwise.
    """
    db_reflection = get_reflection(db, reflection_id)
    if db_reflection:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(db_reflection, 'is_reflected', True)
        db.commit()
        db.refresh(db_reflection)
    return db_reflection


def add_reflection_feedback(db: DbSession, reflection_id: UUID, feedback: int) -> Optional[Reflection]:
    """
    Add user feedback to a reflection.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to update.
        feedback: Integer feedback value (1 for thumbs up, -1 for thumbs down).
        
    Returns:
        Updated Reflection object if found, None otherwise.
    """
    # Ensure feedback is a valid value
    if feedback not in [-1, 1]:
        raise ValueError("Feedback must be 1 (thumbs up) or -1 (thumbs down)")
        
    db_reflection = get_reflection(db, reflection_id)
    if db_reflection:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(db_reflection, 'feedback', feedback)
        db.commit()
        db.refresh(db_reflection)
    return db_reflection


def get_node_details(db: DbSession, node_ids: List[UUID]) -> List[Dict[str, Any]]:
    """
    Get details for a list of nodes.
    
    Args:
        db: Database session.
        node_ids: List of node IDs to retrieve.
        
    Returns:
        List of node details as dictionaries.
    """
    nodes = db.query(Node).filter(Node.id.in_(node_ids)).all()
    return [
        {
            "user_id": str(node.user_id),
            "text": node.text,
            "theme": node.theme,
            "cognition_type": node.cognition_type,
            "emotion": node.emotion,
            "created_at": node.created_at.isoformat()
        }
        for node in nodes
    ]


def get_edge_details(db: DbSession, edge_ids: List[UUID]) -> List[Dict[str, Any]]:
    """
    Get details for a list of edges.
    
    Args:
        db: Database session.
        edge_ids: List of edge IDs to retrieve.
        
    Returns:
        List of edge details as dictionaries.
    """
    edges = db.query(Edge).filter(Edge.id.in_(edge_ids)).all()
    return [
        {
            "edge_type": edge.edge_type,
            "match_strength": edge.match_strength,
            "explanation": edge.explanation
        }
        for edge in edges
    ]


def mark_edges_processed(db: DbSession, edge_ids: List[UUID]) -> int:
    """
    Mark edges as processed.
    
    Args:
        db: Database session.
        edge_ids: List of edge IDs to mark as processed.
        
    Returns:
        Number of edges marked as processed.
    """
    result = db.query(Edge).filter(Edge.id.in_(edge_ids)).update(
        {"is_processed": True},
        synchronize_session=False
    )
    db.commit()
    return result