"""
Embedding processor for node embeddings.

This module handles the batch processing of node embeddings using OpenAI's API.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from app.models.models import Node
from app.utils.openai_utils import (
    generate_embeddings_batch,
    serialize_embedding,
    DEFAULT_BATCH_SIZE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_unprocessed_nodes(db: DbSession, batch_size: int = DEFAULT_BATCH_SIZE) -> List[Tuple[UUID, str]]:
    """
    Get a batch of nodes that don't have embeddings.
    
    Args:
        db: Database session.
        batch_size: Maximum number of nodes to fetch.
        
    Returns:
        List of (node_id, text) tuples.
    """
    logger.info(f"Fetching up to {batch_size} nodes without embeddings")
    
    query = select(Node.id, Node.text).where(Node.embedding.is_(None)).limit(batch_size)
    results = db.execute(query).fetchall()
    
    logger.info(f"Found {len(results)} nodes without embeddings")
    return [(node_id, text) for node_id, text in results]


def update_node_embedding(db: DbSession, node_id: UUID, embedding: List[float]) -> bool:
    """
    Update a node's embedding in the database.
    
    Args:
        db: Database session.
        node_id: ID of the node to update.
        embedding: Embedding vector as a list of floats.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        serialized_embedding = serialize_embedding(embedding)
        
        # Update just the embedding - leave is_processed flag untouched
        # is_processed should only be set to true by the edge processor
        stmt = update(Node).where(Node.id == node_id).values(
            embedding=serialized_embedding
        )
        db.execute(stmt)
        
        return True
    except Exception as e:
        logger.error(f"Error updating embedding for node {node_id}: {e}", exc_info=True)
        return False


def process_embeddings_batch(
    db: DbSession, batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict[str, Any]:
    """
    Process a batch of nodes to generate and store embeddings.
    
    Args:
        db: Database session.
        batch_size: Maximum number of nodes to process.
        
    Returns:
        Dictionary with processing statistics.
    """
    logger.info(f"Starting batch embedding processing with batch size {batch_size}")
    
    # Get nodes without embeddings
    node_data = get_unprocessed_nodes(db, batch_size)
    
    if not node_data:
        logger.info("No nodes found without embeddings")
        return {
            "processed": 0,
            "success": 0,
            "error": 0,
            "message": "No nodes found without embeddings"
        }
    
    # Extract node IDs and texts
    node_ids, texts = zip(*node_data)
    
    # Generate embeddings for all texts in batch
    embeddings = generate_embeddings_batch(texts)
    
    # Process results
    success_count = 0
    error_count = 0
    
    # Update embeddings in the database
    for i, (node_id, embedding) in enumerate(zip(node_ids, embeddings)):
        if embedding:
            success = update_node_embedding(db, node_id, embedding)
            if success:
                success_count += 1
            else:
                error_count += 1
        else:
            logger.error(f"No embedding generated for node {node_id}")
            error_count += 1
    
    # Commit changes
    db.commit()
    
    logger.info(f"Batch processing complete: {success_count} successful, {error_count} failed")
    return {
        "processed": len(node_data),
        "success": success_count,
        "error": error_count,
        "message": f"Processed {len(node_data)} nodes: {success_count} successful, {error_count} failed"
    }