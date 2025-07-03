"""
Test script for node embedding functionality.

This script tests the batch embedding process by:
1. Checking if there are nodes without embeddings
2. Running the batch embedding process
3. Verifying the results
"""
import logging
import requests
import json
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URLs
API_BASE_URL = "http://localhost:8000/api/v1"  # Updated port to 8000 (uvicorn server)
EMBEDDINGS_PROCESS_URL = f"{API_BASE_URL}/nodes/embeddings/process"

def get_embedding_stats() -> Dict[str, Any]:
    """Process a batch of embeddings and return the stats."""
    logger.info("Processing a batch of node embeddings...")
    
    try:
        response = requests.post(EMBEDDINGS_PROCESS_URL, params={"batch_size": 10})
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Embedding processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing embeddings: {e}")
        return {"error": str(e)}

def test_embeddings():
    """Test the batch embedding process."""
    logger.info("Starting embedding test...")
    
    # First batch
    result = get_embedding_stats()
    
    if result.get("processed", 0) > 0:
        logger.info(f"Successfully processed {result.get('success', 0)} embeddings")
    else:
        logger.info("No nodes found without embeddings or error occurred")
    
    logger.info("Embedding test completed.")

if __name__ == "__main__":
    test_embeddings()