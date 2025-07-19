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
    Get a batch of nodes that don't have embeddings with decrypted text for OpenAI processing.
    
    Args:
        db: Database session.
        batch_size: Maximum number of nodes to fetch.
        
    Returns:
        List of (node_id, decrypted_text) tuples.
    """
    logger.info(f"Fetching up to {batch_size} nodes without embeddings")
    
    # Get node IDs without embeddings
    query = select(Node.id).where(Node.embedding.is_(None)).limit(batch_size)
    node_ids = [row[0] for row in db.execute(query).fetchall()]
    
    logger.info(f"Found {len(node_ids)} nodes without embeddings")
    
    # Get each node with decrypted text for OpenAI processing
    from app.repositories import node_repository
    result_tuples = []
    for node_id in node_ids:
        node = node_repository.get_node(db, node_id, decrypt_for_processing=True)
        if node and node.text:
            result_tuples.append((node_id, node.text))
    
    logger.info(f"Successfully retrieved {len(result_tuples)} nodes with decrypted text for embedding generation")
    return result_tuples


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
    import time
    start_time = time.time()
    logger.info(f"[EMBEDDING-DEBUG] Starting batch embedding processing with batch size {batch_size} at {time.strftime('%H:%M:%S')}")
    
    # Get nodes without embeddings
    node_data = get_unprocessed_nodes(db, batch_size)
    fetch_time = time.time() - start_time
    logger.info(f"[EMBEDDING-DEBUG] Fetched nodes in {fetch_time:.2f}s")
    
    if not node_data:
        total_time = time.time() - start_time
        logger.info(f"[EMBEDDING-DEBUG] No nodes found without embeddings (completed in {total_time:.2f}s)")
        return {
            "processed": 0,
            "success": 0,
            "error": 0,
            "message": "No nodes found without embeddings"
        }
    
    # Extract node IDs and texts
    node_ids, texts = zip(*node_data)
    logger.info(f"[EMBEDDING-DEBUG] Processing {len(node_ids)} nodes: {[str(nid)[:8] for nid in node_ids]}")
    
    # Generate embeddings for all texts in batch
    embedding_start = time.time()
    embeddings = generate_embeddings_batch(texts)
    embedding_time = time.time() - embedding_start
    logger.info(f"[EMBEDDING-DEBUG] OpenAI embedding generation completed in {embedding_time:.2f}s")
    
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
    commit_start = time.time()
    db.commit()
    commit_time = time.time() - commit_start
    
    total_time = time.time() - start_time
    logger.info(f"[EMBEDDING-DEBUG] Batch processing complete in {total_time:.2f}s: {success_count} successful, {error_count} failed (commit: {commit_time:.2f}s)")
    return {
        "processed": len(node_data),
        "success": success_count,
        "error": error_count,
        "message": f"Processed {len(node_data)} nodes: {success_count} successful, {error_count} failed",
        "timing": {
            "total_time": total_time,
            "fetch_time": fetch_time,
            "embedding_time": embedding_time,
            "commit_time": commit_time
        }
    }