"""
Script to create diverse edge types in the database.

This script:
1. Creates a new test user
2. Creates a session
3. Creates specific node pairs designed to trigger different edge types
4. Processes nodes to generate embeddings
5. Creates edges between the node pairs
"""
import os
import json
import uuid
import logging
import time
import requests
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:5000/api/v1"

# List of diverse node pairs designed to generate different edge types
DIVERSE_NODE_PAIRS = [
    # 1. Contradiction Loop
    (
        "I believe I'm fundamentally not good at public speaking. The anxiety it causes me is overwhelming.",
        "I've given good presentations before and received positive feedback. This contradicts my belief.",
        "insecurity", "confidence", "contradiction_loop"
    ),
    
    # 2. Mixed Transition
    (
        "When I think about it rationally, I know that one presentation won't define my career.",
        "I need to practice more to build my confidence. Preparation is key to overcoming these feelings.",
        "calm", "determination", "mixed_transition"
    ),
    
    # 3. Recurrence Emotion
    (
        "I remember feeling this same anxiety before my college thesis presentation. History repeats itself.",
        "I've been feeling anxious about my upcoming presentation at work. It's consuming my thoughts.",
        "anxiety", "anxiety", "recurrence_emotion"
    ),
    
    # 4. Avoidance Drift
    (
        "Sometimes I think I should just avoid public speaking altogether. It would be easier.",
        "But then I'd miss opportunities for growth and career advancement. Is avoiding worth the cost?",
        "relief", "concern", "avoidance_drift"
    ),
    
    # 5. Recurrence Theme
    (
        "When I'm presenting, I worry everyone can see how nervous I am. My hands shake.",
        "In reality, most people are too focused on the content to notice my nervousness.",
        "anxiety", "reassurance", "recurrence_theme"
    ),
    
    # 6. Emotion Shift
    (
        "I felt anxious at work today during a meeting with clients.",
        "Later I met my friend for dinner and we laughed a lot.",
        "anxiety", "joy", "emotion_shift"
    )
]

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user for diverse edges."""
    user_id = str(uuid.uuid4())
    url = f"{BASE_URL}/users/"
    try:
        response = requests.post(url, json={
            "email": f"diverse_edge_test_{user_id}@example.com",
            "name": f"Diverse Edge Test {user_id}"
        })
        response.raise_for_status()
        user_data = response.json()
        logger.info(f"Created test user: {user_data['id']}")
        return user_data
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        return None

def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session for diverse edges."""
    url = f"{BASE_URL}/sessions/"
    try:
        response = requests.post(url, json={
            "user_id": user_id,
            "title": "Diverse Edge Test Session",
            "description": "A test session to generate diverse edge types"
        })
        response.raise_for_status()
        session_data = response.json()
        logger.info(f"Created test session: {session_data['id']}")
        return session_data
    except Exception as e:
        logger.error(f"Error creating test session: {e}")
        return None

def create_node(user_id: str, session_id: str, text: str, emotion: str) -> Optional[Dict[str, Any]]:
    """Create a node directly."""
    url = f"{BASE_URL}/nodes/"
    try:
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "text": text,
            "emotion": emotion,
            "cognition_type": "observation",  # Default cognition type
            "theme": "test theme",            # Default theme
            "summary": text,                  # Using the text as summary
            "is_processed": True
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        node_data = response.json()
        logger.info(f"Created node: {node_data['id']}")
        return node_data
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        return None

def create_node_pair(user_id: str, session_id: str, node_pair: Tuple[str, str, str, str, str]) -> List[Dict[str, Any]]:
    """Create a pair of nodes for testing diverse edge types."""
    text1, text2, emotion1, emotion2, _ = node_pair
    node1 = create_node(user_id, session_id, text1, emotion1)
    node2 = create_node(user_id, session_id, text2, emotion2)
    return [node1, node2] if node1 and node2 else []

def process_embeddings(batch_size: int = 20) -> Optional[Dict[str, Any]]:
    """Process embeddings for all nodes."""
    url = f"{BASE_URL}/nodes/embeddings/process/"
    try:
        response = requests.post(url, params={"batch_size": batch_size})
        response.raise_for_status()
        embedding_stats = response.json()
        logger.info(f"Processed embeddings: {embedding_stats}")
        return embedding_stats
    except Exception as e:
        logger.error(f"Error processing embeddings: {e}")
        return None

def create_edge(from_node_id: str, to_node_id: str, user_id: str, edge_type: str) -> Optional[Dict[str, Any]]:
    """Create an edge directly with specified type."""
    url = f"{BASE_URL}/edges/"
    try:
        payload = {
            "from_node": from_node_id,
            "to_node": to_node_id,
            "user_id": user_id,
            "edge_type": edge_type,
            "match_strength": 0.9,
            "session_relation": "intra_session",
            "explanation": f"This is a test {edge_type} edge."
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        edge_data = response.json()
        logger.info(f"Created edge: {edge_data['id']} of type {edge_type}")
        return edge_data
    except Exception as e:
        logger.error(f"Error creating edge: {e}")
        return None

def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges using the API endpoint."""
    url = f"{BASE_URL}/edges/process/{user_id}/"
    try:
        response = requests.post(url, params={"batch_size": batch_size})
        response.raise_for_status()
        edge_stats = response.json()
        logger.info(f"Processed edges: {edge_stats}")
        return edge_stats
    except Exception as e:
        logger.error(f"Error processing edges: {e}")
        return None

def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    url = f"{BASE_URL}/edges/user/{user_id}/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        edges = response.json()
        logger.info(f"Retrieved {len(edges)} edges for user {user_id}")
        return edges
    except Exception as e:
        logger.error(f"Error getting user edges: {e}")
        return None

def run_diverse_edges_creation():
    """Create diverse edge types in the database."""
    # Create test user
    user_data = create_test_user()
    if not user_data:
        logger.error("Failed to create test user. Aborting.")
        return
    
    user_id = user_data['id']
    
    # Create test session
    session_data = create_test_session(user_id)
    if not session_data:
        logger.error("Failed to create test session. Aborting.")
        return
    
    session_id = session_data['id']
    
    # Create node pairs
    node_pairs = []
    for node_pair in DIVERSE_NODE_PAIRS:
        pair = create_node_pair(user_id, session_id, node_pair)
        if pair:
            node_pairs.append((pair[0], pair[1], node_pair[4]))  # Store nodes and expected edge type
        else:
            logger.warning(f"Failed to create node pair for {node_pair[4]}")
    
    if not node_pairs:
        logger.error("Failed to create any node pairs. Aborting.")
        return
    
    # Process embeddings for all nodes
    logger.info("Processing embeddings for nodes...")
    embedding_stats = process_embeddings(batch_size=len(node_pairs) * 2)
    if not embedding_stats:
        logger.error("Failed to process embeddings. Aborting.")
        return
    
    # Create edges for each node pair
    edges_created = []
    for from_node, to_node, edge_type in node_pairs:
        edge = create_edge(from_node['id'], to_node['id'], user_id, edge_type)
        if edge:
            edges_created.append(edge)
        else:
            logger.warning(f"Failed to create edge of type {edge_type}")
    
    # Get all edges for the user
    edges = get_user_edges(user_id)
    if not edges:
        logger.error("Failed to retrieve edges. Aborting.")
        return
    
    # Count edge types
    edge_types = {}
    for edge in edges:
        edge_type = edge.get('edge_type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    logger.info("Edge type distribution:")
    for edge_type, count in edge_types.items():
        logger.info(f"  {edge_type}: {count}")
    
    logger.info(f"Successfully created {len(edges_created)} diverse edges")
    return {
        "user_id": user_id,
        "session_id": session_id,
        "nodes_created": len(node_pairs) * 2,
        "edges_created": len(edges_created),
        "edge_types": edge_types
    }

if __name__ == "__main__":
    logger.info("=== Creating Diverse Edge Types ===")
    results = run_diverse_edges_creation()
    if results:
        logger.info("=== Results ===")
        for key, value in results.items():
            logger.info(f"{key}: {value}")
    else:
        logger.error("Failed to create diverse edge types")