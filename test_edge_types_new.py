"""
Test to verify that the edge type constraint has been removed.

This test script creates a new edge with a type from the original prompt.
"""
import os
import sys
import requests
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://127.0.0.1:8000/api/v1"


def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user for edge type testing."""
    url = f"{BASE_URL}/users"
    payload = {
        "username": f"test_edge_type_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to create test user: {e}")
        return None


def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session for the user."""
    url = f"{BASE_URL}/sessions"
    payload = {
        "user_id": user_id,
        "duration_seconds": 60,
        "raw_transcript": "This is a test transcript for edge type testing."
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to create test session: {e}")
        return None


def create_test_nodes(user_id: str, session_id: str) -> List[Dict[str, Any]]:
    """Create two test nodes for edge type testing."""
    url = f"{BASE_URL}/nodes"
    
    node1_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "text": "First test node for edge type testing",
        "emotion": "joy",
        "theme": "testing",
        "cognition_type": "analytical"
    }
    
    node2_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "text": "Second test node for edge type testing",
        "emotion": "curiosity",
        "theme": "testing",
        "cognition_type": "questioning"
    }
    
    try:
        nodes = []
        response1 = requests.post(url, json=node1_payload)
        response1.raise_for_status()
        nodes.append(response1.json())
        
        response2 = requests.post(url, json=node2_payload)
        response2.raise_for_status()
        nodes.append(response2.json())
        
        return nodes
    except Exception as e:
        logger.error(f"Failed to create test nodes: {e}")
        return []


def create_edge_with_custom_type(
    from_node_id: str, 
    to_node_id: str, 
    user_id: str,
    edge_type: str
) -> Optional[Dict[str, Any]]:
    """Create an edge with a custom edge type."""
    url = f"{BASE_URL}/edges"
    payload = {
        "from_node": from_node_id,
        "to_node": to_node_id,
        "user_id": user_id,
        "edge_type": edge_type,
        "match_strength": 0.85,
        "session_relation": "intra_session",
        "explanation": "Testing custom edge type"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to create edge: {e}")
        return None


def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    url = f"{BASE_URL}/edges/user/{user_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get user edges: {e}")
        return None


def test_original_edge_types():
    """Test creation of edges using original edge types."""
    # Create test user
    logger.info("Creating test user...")
    user = create_test_user()
    if not user:
        logger.error("Failed to create test user.")
        return

    user_id = user["id"]
    logger.info(f"Created test user with ID: {user_id}")

    # Create session
    logger.info("Creating test session...")
    session = create_test_session(user_id)
    if not session:
        logger.error("Failed to create test session.")
        return

    session_id = session["id"]
    logger.info(f"Created test session with ID: {session_id}")

    # Create nodes
    logger.info("Creating test nodes...")
    nodes = create_test_nodes(user_id, session_id)
    if not nodes or len(nodes) < 2:
        logger.error("Failed to create test nodes.")
        return

    from_node_id = nodes[0]["id"]
    to_node_id = nodes[1]["id"]
    logger.info(f"Created nodes with IDs: {from_node_id} and {to_node_id}")

    # Test original edge types
    original_edge_types = [
        "theme_repetition",
        "identity_drift",
        "emotional_contradiction",
        "belief_contradiction",
        "unresolved_loop"
    ]

    for edge_type in original_edge_types:
        logger.info(f"Testing edge type: {edge_type}")
        edge = create_edge_with_custom_type(from_node_id, to_node_id, user_id, edge_type)
        
        if edge:
            logger.info(f"Successfully created edge with type: {edge_type}")
            logger.info(f"Edge ID: {edge['id']}")
            logger.info(json.dumps(edge, indent=2))
        else:
            logger.error(f"Failed to create edge with type: {edge_type}")

    # Get all user edges and verify
    logger.info("Retrieving all user edges...")
    edges = get_user_edges(user_id)
    
    if edges:
        logger.info(f"Found {len(edges)} edges for user.")
        
        # Count edge types
        edge_type_counts = {}
        for edge in edges:
            edge_type = edge["edge_type"]
            if edge_type not in edge_type_counts:
                edge_type_counts[edge_type] = 0
            edge_type_counts[edge_type] += 1
            
        logger.info("Edge type distribution:")
        for edge_type, count in edge_type_counts.items():
            logger.info(f"  - {edge_type}: {count}")
    else:
        logger.error("Failed to retrieve user edges.")


if __name__ == "__main__":
    test_original_edge_types()