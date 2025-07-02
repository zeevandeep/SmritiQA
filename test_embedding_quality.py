"""
Test script for verifying embedding quality.

This script tests the quality of the generated embeddings by:
1. Retrieving nodes with embeddings from the database
2. Verifying embedding dimensionality
3. Testing semantic similarity between nodes
"""
import logging
import numpy as np
import requests
import json
import time
from typing import Dict, Any, List, Tuple
import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

# Add the project root to the Python path
sys.path.append(os.path.abspath('.'))

from app.models.models import Node
from app.utils.openai_utils import deserialize_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    
    a_array = np.array(a)
    b_array = np.array(b)
    
    dot_product = np.dot(a_array, b_array)
    norm_a = np.linalg.norm(a_array)
    norm_b = np.linalg.norm(b_array)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def get_nodes_with_embeddings(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get nodes with embeddings from the database."""
    logger.info(f"Fetching up to {limit} nodes with embeddings")
    
    query = select(Node).where(Node.embedding.is_not(None)).limit(limit)
    results = db.execute(query).scalars().all()
    
    logger.info(f"Found {len(results)} nodes with embeddings")
    
    # Convert to dictionaries and deserialize embeddings
    nodes = []
    for node in results:
        node_dict = {
            "id": node.id,
            "text": node.text,
            "emotion": node.emotion,
            "theme": node.theme,
            "embedding": deserialize_embedding(node.embedding)
        }
        nodes.append(node_dict)
    
    return nodes


def test_embedding_dimensions(nodes: List[Dict[str, Any]]) -> bool:
    """Test if embeddings have the expected dimensions."""
    expected_dim = 1536  # OpenAI ada-002 embeddings are 1536-dimensional
    
    for i, node in enumerate(nodes):
        embedding = node["embedding"]
        if embedding is None:
            logger.error(f"Node {i+1}: Embedding is None")
            return False
        
        dim = len(embedding)
        if dim != expected_dim:
            logger.error(f"Node {i+1}: Expected {expected_dim} dimensions, got {dim}")
            return False
        
        logger.info(f"Node {i+1}: Embedding has correct dimension ({dim})")
    
    return True


def test_semantic_similarity(nodes: List[Dict[str, Any]]) -> List[Tuple[str, str, float]]:
    """Test semantic similarity between nodes."""
    if len(nodes) < 2:
        logger.warning("Need at least 2 nodes to test similarity")
        return []
    
    # Calculate similarities between all pairs
    similarities = []
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            node1 = nodes[i]
            node2 = nodes[j]
            
            sim = cosine_similarity(node1["embedding"], node2["embedding"])
            
            # Store text snippets (truncated) and similarity
            text1 = node1["text"][:50] + "..." if len(node1["text"]) > 50 else node1["text"]
            text2 = node2["text"][:50] + "..." if len(node2["text"]) > 50 else node2["text"]
            
            similarities.append((text1, text2, sim))
            
            logger.info(f"Similarity between '{text1}' and '{text2}': {sim:.4f}")
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[2], reverse=True)
    return similarities


def test_embeddings():
    """Test the quality of generated embeddings."""
    logger.info("Starting embedding quality test...")
    
    with SessionLocal() as db:
        # Get nodes with embeddings
        nodes = get_nodes_with_embeddings(db)
        
        if not nodes:
            logger.error("No nodes with embeddings found")
            return
        
        # Test embedding dimensions
        dims_ok = test_embedding_dimensions(nodes)
        if not dims_ok:
            logger.error("Embedding dimension test failed")
            return
        
        # Test semantic similarity
        similarities = test_semantic_similarity(nodes)
        
        if similarities:
            logger.info("\nTop similar node pairs:")
            for i, (text1, text2, sim) in enumerate(similarities[:3]):
                logger.info(f"{i+1}. Similarity: {sim:.4f}")
                logger.info(f"   Text 1: {text1}")
                logger.info(f"   Text 2: {text2}")
                
            logger.info("\nLeast similar node pairs:")
            for i, (text1, text2, sim) in enumerate(similarities[-3:]):
                logger.info(f"{i+1}. Similarity: {sim:.4f}")
                logger.info(f"   Text 1: {text1}")
                logger.info(f"   Text 2: {text2}")
    
    logger.info("Embedding quality test completed.")


if __name__ == "__main__":
    test_embeddings()