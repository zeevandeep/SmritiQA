"""
Test script for edge creation functionality.

This script tests the batch edge processing by:
1. Getting a user ID
2. Running the batch edge processing
3. Verifying the results
"""
import logging
import requests
import json
import time
from typing import Dict, Any
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URLs
API_BASE_URL = "http://localhost:5000/api/v1"
EDGES_PROCESS_URL = f"{API_BASE_URL}/edges/process"  # This will be appended with /{user_id}
USERS_URL = f"{API_BASE_URL}/users"
USER_EDGES_URL = f"{API_BASE_URL}/edges"

# Default user ID (can be replaced with an actual user ID from your database)
# This is just a placeholder and will be replaced by a real user ID
DEFAULT_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


def get_test_user_id() -> str:
    """Get an existing user ID for testing."""
    logger.info("Getting a user ID for testing...")
    
    try:
        # Get list of users
        response = requests.get(USERS_URL)
        response.raise_for_status()
        
        users = response.json()
        
        if users:
            # Use the first user
            user_id = users[0]["id"]
            logger.info(f"Using existing user with ID: {user_id}")
            return user_id
        else:
            # Create a new user if none exist
            logger.info("No existing users found, creating a new one...")
            user_data = {
                "email": f"test_user_{uuid.uuid4()}@example.com"
            }
            
            response = requests.post(USERS_URL, json=user_data)
            response.raise_for_status()
            
            new_user = response.json()
            logger.info(f"Created new user with ID: {new_user['id']}")
            return new_user["id"]
    except Exception as e:
        logger.error(f"Error getting user ID: {e}")
        # Fall back to default ID
        logger.warning(f"Using default user ID: {DEFAULT_USER_ID}")
        return DEFAULT_USER_ID


def process_edges(user_id: str, batch_size: int = 1) -> Dict[str, Any]:
    """Process a batch of edges and return the stats."""
    logger.info(f"Processing edges for user {user_id} with batch size {batch_size}...")
    
    try:
        # Path parameter for user_id, query parameter for batch_size
        response = requests.post(
            f"{EDGES_PROCESS_URL}/{user_id}?batch_size={batch_size}"
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Edge processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing edges: {e}")
        return {"error": str(e)}


def get_user_edges(user_id: str) -> Dict[str, Any]:
    """Get edges for a user."""
    logger.info(f"Getting edges for user {user_id}...")
    
    try:
        # First try the direct path parameter method
        try:
            logger.info(f"Trying direct path method...")
            response = requests.get(f"{USER_EDGES_URL}/user/{user_id}")
            response.raise_for_status()
            edges = response.json()
            logger.info(f"Found {len(edges)} edges for user {user_id} using direct path method")
            return {"count": len(edges), "edges": edges}
        except Exception as e:
            logger.warning(f"Direct path method failed: {e}, trying query parameter method")
        
        # Fall back to query parameter method
        response = requests.get(f"{USER_EDGES_URL}?user_id={user_id}")
        response.raise_for_status()
        
        edges = response.json()
        logger.info(f"Found {len(edges)} edges for user {user_id} using query parameter method")
        return {"count": len(edges), "edges": edges}
    except Exception as e:
        logger.error(f"Error getting user edges: {e}")
        return {"error": str(e)}


def test_edges():
    """Test the batch edge processing."""
    logger.info("Starting edge processing test...")
    
    # Get a user ID for testing
    user_id = get_test_user_id()
    
    # Check existing edges
    before_edges = get_user_edges(user_id)
    before_count = before_edges.get("count", 0)
    logger.info(f"User has {before_count} edges before processing")
    
    # Process a batch of edges (1 source node)
    result = process_edges(user_id, batch_size=1)
    
    # Check if processing was successful
    if "error" in result:
        logger.error(f"Edge processing failed: {result['error']}")
        return
    
    # Check updated edges
    after_edges = get_user_edges(user_id)
    after_count = after_edges.get("count", 0)
    logger.info(f"User has {after_count} edges after processing")
    
    # Calculate created edges
    created_edges = after_count - before_count
    
    if created_edges > 0:
        logger.info(f"Successfully created {created_edges} new edges")
        
        # Print details of a few new edges
        edges = after_edges.get("edges", [])
        if edges:
            logger.info("\nDetails of new edges:")
            for i, edge in enumerate(edges[:3]):  # Show up to 3 edges
                logger.info(f"Edge {i+1}:")
                logger.info(f"  Type: {edge.get('edge_type')}")
                logger.info(f"  Match Strength: {edge.get('match_strength')}")
                logger.info(f"  Session Relation: {edge.get('session_relation')}")
                logger.info(f"  Explanation: {edge.get('explanation')[:100]}...")
    else:
        logger.info("No new edges created. This could be because:")
        logger.info("- All nodes already have the maximum number of edges")
        logger.info("- No nodes with suitable similarity were found")
        logger.info("- There are no nodes with embeddings in the database")
    
    logger.info("Edge processing test completed.")


if __name__ == "__main__":
    test_edges()