"""
Test script specifically designed to create and test diverse edge types.

This script will:
1. Create a user
2. Create a session with transcript designed to elicit diverse edge types
3. Process nodes, embeddings, and edges
4. Check the resulting edge types
"""
import os
import json
import uuid
import logging
import time
import requests
from typing import Dict, Any, List, Optional
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:5000/api/v1"

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user."""
    url = f"{BASE_URL}/users"
    try:
        response = requests.post(url, json={"name": f"Test User {uuid.uuid4()}"})
        response.raise_for_status()
        user_data = response.json()
        logger.info(f"Created test user: {user_data['id']}")
        return user_data
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        return None

def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session for the user."""
    url = f"{BASE_URL}/sessions"
    try:
        response = requests.post(url, json={
            "user_id": user_id,
            "title": "Diverse Edge Test Session",
            "description": "A test session with diverse thought patterns to generate different edge types."
        })
        response.raise_for_status()
        session_data = response.json()
        logger.info(f"Created test session: {session_data['id']}")
        return session_data
    except Exception as e:
        logger.error(f"Error creating test session: {e}")
        return None

def update_session_transcript(session_id: str, transcript: str) -> bool:
    """Update session with diverse transcript."""
    url = f"{BASE_URL}/sessions/{session_id}"
    try:
        response = requests.put(url, json={"transcript": transcript})
        response.raise_for_status()
        logger.info(f"Updated session {session_id} with diverse transcript")
        return True
    except Exception as e:
        logger.error(f"Error updating session transcript: {e}")
        return False

def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Process session to extract diverse nodes."""
    url = f"{BASE_URL}/nodes/process-session/{session_id}"
    try:
        response = requests.post(url)
        response.raise_for_status()
        nodes_data = response.json()
        logger.info(f"Processed session into {len(nodes_data)} nodes")
        return nodes_data
    except Exception as e:
        logger.error(f"Error processing session: {e}")
        return None

def process_embeddings(batch_size: int = 20) -> Optional[Dict[str, Any]]:
    """Process embeddings for all nodes."""
    url = f"{BASE_URL}/nodes/process-embeddings"
    try:
        response = requests.post(url, params={"batch_size": batch_size})
        response.raise_for_status()
        embedding_stats = response.json()
        logger.info(f"Processed embeddings: {embedding_stats}")
        return embedding_stats
    except Exception as e:
        logger.error(f"Error processing embeddings: {e}")
        return None

def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges to generate diverse edge types."""
    url = f"{BASE_URL}/edges/process-edges/{user_id}"
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
    url = f"{BASE_URL}/edges/user/{user_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        edges = response.json()
        logger.info(f"Retrieved {len(edges)} edges for user {user_id}")
        return edges
    except Exception as e:
        logger.error(f"Error getting user edges: {e}")
        return None

def analyze_edge_types(edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the distribution of edge types."""
    edge_type_counts = {}
    for edge in edges:
        edge_type = edge.get('edge_type', 'unknown')
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
    
    return edge_type_counts

def run_diverse_edges_test():
    """Run the diverse edges test end-to-end."""
    # Create test user
    user_data = create_test_user()
    if not user_data:
        logger.error("Failed to create test user. Aborting test.")
        return
    
    user_id = user_data['id']
    
    # Create test session
    session_data = create_test_session(user_id)
    if not session_data:
        logger.error("Failed to create test session. Aborting test.")
        return
    
    session_id = session_data['id']
    
    # This transcript is designed with diverse thought patterns to elicit different edge types
    transcript = """
    I believe I'm fundamentally not good at public speaking. The anxiety it causes me is overwhelming.
    But I've given good presentations before and received positive feedback. This contradicts my belief.
    My colleagues seem to present so effortlessly. I feel envious of their natural abilities.
    Perhaps I should focus on my strengths instead of comparing myself to others. That seems like a healthier approach.
    When I think about it rationally, I know that one presentation won't define my career. It's just a small part.
    I need to practice more to build my confidence. Preparation is key to overcoming these feelings.
    I remember feeling this same anxiety before my college thesis presentation. History repeats itself.
    I've been feeling anxious about my upcoming presentation at work. It's consuming my thoughts.
    Sometimes I think I should just avoid public speaking altogether. It would be easier.
    But then I'd miss opportunities for growth and career advancement. Is avoiding worth the cost?
    When I'm presenting, I worry everyone can see how nervous I am. My hands shake.
    In reality, most people are too focused on the content to notice my nervousness.
    I should treat each presentation as a learning opportunity rather than a test of my worth.
    I noticed I keep coming back to these same thoughts about presentations. It's a recurring theme.
    I wonder if this pattern of anxiety followed by avoidance has affected other areas of my life too.
    """
    
    # Update session with diverse transcript
    if not update_session_transcript(session_id, transcript):
        logger.error("Failed to update session with transcript. Aborting test.")
        return
    
    # Process session to extract nodes
    nodes = process_session_to_nodes(session_id)
    if not nodes:
        logger.error("Failed to process session into nodes. Aborting test.")
        return
    
    logger.info(f"Created {len(nodes)} nodes with diverse thoughts")
    
    # Wait a bit to ensure nodes are properly saved
    time.sleep(2)
    
    # Process embeddings for all nodes
    embedding_stats = process_embeddings(batch_size=len(nodes))
    if not embedding_stats:
        logger.error("Failed to process embeddings. Aborting test.")
        return
    
    logger.info(f"Processed embeddings for {embedding_stats.get('processed_nodes', 0)} nodes")
    
    # Wait a bit to ensure embeddings are properly saved
    time.sleep(2)
    
    # Process edges
    edge_stats = process_edges(user_id, batch_size=len(nodes))
    if not edge_stats:
        logger.error("Failed to process edges. Aborting test.")
        return
    
    logger.info(f"Created {edge_stats.get('created_edges', 0)} edges")
    
    # Wait a bit to ensure edges are properly saved
    time.sleep(2)
    
    # Get all edges for the user
    edges = get_user_edges(user_id)
    if not edges:
        logger.error("Failed to retrieve edges. Aborting test.")
        return
    
    # Analyze edge type distribution
    edge_type_counts = analyze_edge_types(edges)
    logger.info("Edge type distribution:")
    for edge_type, count in edge_type_counts.items():
        logger.info(f"  {edge_type}: {count}")
    
    # Print a sample of edges with different types
    edge_type_samples = {}
    for edge in edges:
        edge_type = edge.get('edge_type', 'unknown')
        if edge_type not in edge_type_samples:
            edge_type_samples[edge_type] = edge
    
    logger.info("\nEdge type samples:")
    for edge_type, edge in edge_type_samples.items():
        logger.info(f"\nType: {edge_type}")
        logger.info(f"Explanation: {edge.get('explanation', 'No explanation')}")
    
    logger.info("\nTest complete!")
    return {
        "user_id": user_id,
        "session_id": session_id,
        "created_nodes": len(nodes),
        "created_edges": len(edges),
        "edge_types": edge_type_counts
    }

if __name__ == "__main__":
    logger.info("=== Starting Diverse Edges Test ===")
    results = run_diverse_edges_test()
    if results:
        logger.info("\n=== Test Results ===")
        pprint(results)
    else:
        logger.error("Test failed or was aborted.")