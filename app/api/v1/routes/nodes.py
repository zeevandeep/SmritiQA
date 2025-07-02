"""
Node management routes for API v1.
"""
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import node_repository, session_repository
from app.services.transcript_processor import process_transcript
from app.services.embedding_processor import process_embeddings_batch
from app.schemas.schemas import Node as NodeSchema, NodeCreate
from app.utils.api_auth import get_current_user_from_jwt, verify_user_access

router = APIRouter()


@router.get("/", response_model=List[NodeSchema])
def read_nodes(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_from_jwt)
):
    """
    Get nodes for a user.
    
    Args:
        user_id: ID of the user.
        skip: Number of nodes to skip.
        limit: Maximum number of nodes to return.
        db: Database session.
        
    Returns:
        List[Node]: List of nodes.
    """
    return node_repository.get_user_nodes(db, user_id=user_id, skip=skip, limit=limit)


@router.get("/session/{session_id}", response_model=List[NodeSchema])
def read_session_nodes(session_id: UUID, db: Session = Depends(get_db)):
    """
    Get nodes for a session.
    
    Args:
        session_id: ID of the session.
        db: Database session.
        
    Returns:
        List[Node]: List of nodes.
        
    Raises:
        HTTPException: If the session is not found.
    """
    # Verify that the session exists
    db_session = session_repository.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return node_repository.get_session_nodes(db, session_id=session_id)


@router.post("/session/{session_id}/process", response_model=List[NodeSchema])
def process_session_transcript(session_id: UUID, db: Session = Depends(get_db)):
    """
    Process a session's transcript to extract nodes.
    
    Args:
        session_id: ID of the session.
        db: Database session.
        
    Returns:
        List[Node]: List of created nodes.
        
    Raises:
        HTTPException: If the session is not found or processing fails.
    """
    # Verify that the session exists
    db_session = session_repository.get_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if the session has a transcript
    if not db_session.raw_transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no transcript"
        )
    
    # Check if the session is already processed
    if db_session.is_processed:
        # Just return the existing nodes
        return node_repository.get_session_nodes(db, session_id=session_id)
    
    # Process the transcript
    success = process_transcript(db, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process transcript"
        )
    
    # Return the created nodes
    return node_repository.get_session_nodes(db, session_id=session_id)


@router.get("/{node_id}", response_model=NodeSchema)
def read_node(node_id: UUID, db: Session = Depends(get_db)):
    """
    Get a node by ID.
    
    Args:
        node_id: ID of the node to retrieve.
        db: Database session.
        
    Returns:
        Node: Node data.
        
    Raises:
        HTTPException: If the node is not found.
    """
    db_node = node_repository.get_node(db, node_id=node_id)
    if db_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return db_node


@router.post("/", response_model=NodeSchema, status_code=status.HTTP_201_CREATED)
def create_node(node: NodeCreate, db: Session = Depends(get_db)):
    """
    Create a new node manually.
    
    This endpoint is primarily for testing/admin purposes.
    In normal operation, nodes are created through session transcript processing.
    
    Args:
        node: Node data.
        db: Database session.
        
    Returns:
        Node: Created node data.
    """
    return node_repository.create_node(db=db, node=node)


@router.post("/embeddings/process", response_model=Dict[str, Any])
def process_node_embeddings(
    batch_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Process a batch of nodes to generate and store embeddings.
    
    This endpoint finds nodes without embeddings and processes them in batches.
    It uses OpenAI's text-embedding-ada-002 model to generate the embeddings.
    
    Args:
        batch_size: Maximum number of nodes to process in this batch.
        db: Database session.
        
    Returns:
        Dict: Processing statistics.
    """
    return process_embeddings_batch(db, batch_size)