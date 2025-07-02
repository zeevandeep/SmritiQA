"""
Edge chain processor service.

This module provides functions for processing chains of connected edges.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.repositories.edge_repository import mark_chain_linked_edges

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_chain_linked_edges(
    db: DbSession, 
    user_id: Optional[UUID] = None, 
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Process edges to identify and mark those that form potential chains.
    
    An edge is considered part of a chain if its to_node is also
    the from_node of another edge. This is Phase 3.25 of the Smriti project.
    
    Args:
        db: Database session.
        user_id: Optional user ID to limit processing to a specific user.
        batch_size: Maximum number of edges to process in this batch.
        
    Returns:
        Dict with processing statistics.
    """
    logger.info(f"Processing chain-linked edges for user_id={user_id}, batch_size={batch_size}")
    
    # Call the repository function to mark edges
    processed_count = mark_chain_linked_edges(db, user_id, batch_size)
    
    logger.info(f"Processed {processed_count} chain-linked edges")
    
    return {
        "processed_count": processed_count,
        "status": "success"
    }