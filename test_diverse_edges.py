"""
Test script for creating diverse types of edges.

This script creates a test user, a session, and a transcript with diverse thought patterns
to generate various edge types (not just emotion_shift).
"""
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:5000/api/v1"

# Timeout for requests
TIMEOUT = 30

# Sample transcript with diverse thought patterns
DIVERSE_TRANSCRIPT = """
I've been feeling anxious about my upcoming presentation at work. 
I keep thinking I'll mess up and everyone will judge me harshly.
Actually, I've given good presentations before and received positive feedback.
No, that's not true - I remember stumbling over my words last time and seeing people look confused.
I believe I'm fundamentally not good at public speaking.
My colleagues seem to present so effortlessly, while I struggle with every slide.
Perhaps I should focus on my strengths instead of comparing myself to others.
When I think about it rationally, I know that one presentation won't define my career.
I've been spending hours preparing, which should help me feel more confident.
I remember feeling this same anxiety before my college thesis presentation, and that went well.
I need to practice more to build my confidence.
Actually, excessive practice might make me sound too rehearsed and unnatural.
I wonder if taking a public speaking course would help me in the long run.
"""

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user for diverse edges testing."""
    email = f"test_diverse_edges_{uuid.uuid4()}@example.com"
    logger.info(f"Creating test user with email: {email}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json={"email": email},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        user = response.json()
        logger.info(f"Created user with ID: {user['id']}")
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session for the user."""
    logger.info(f"Creating session for user: {user_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/",
            json={"user_id": user_id, "session_type": "journal"},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        session = response.json()
        logger.info(f"Created session with ID: {session['id']}")
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None

def update_session_transcript(session_id: str, transcript: str) -> bool:
    """Update session with diverse transcript."""
    logger.info(f"Updating session {session_id} with diverse transcript")
    
    try:
        response = requests.patch(  # Changed from PUT to PATCH
            f"{BASE_URL}/sessions/{session_id}",
            json={"transcript": transcript},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        logger.info("Updated session with transcript")
        return True
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        return False

def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Process session to extract diverse nodes."""
    logger.info(f"Processing session {session_id} to extract nodes")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=TIMEOUT * 2  # Longer timeout for processing
        )
        response.raise_for_status()
        nodes = response.json()
        logger.info(f"Extracted {len(nodes)} diverse nodes from session")
        return nodes
    except Exception as e:
        logger.error(f"Error processing session: {e}")
        return None

def process_embeddings(batch_size: int = 20) -> Optional[Dict[str, Any]]:
    """Process embeddings for all nodes."""
    logger.info(f"Processing embeddings with batch size {batch_size}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/embeddings/process?batch_size={batch_size}",
            timeout=TIMEOUT * 2  # Longer timeout for processing
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Embedding processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing embeddings: {e}")
        return None

def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges to generate diverse edge types."""
    logger.info(f"Processing edges for user {user_id} with batch size {batch_size}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/edges/process/{user_id}?batch_size={batch_size}",
            timeout=TIMEOUT * 3  # Much longer timeout for edge processing
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Edge processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing edges: {e}")
        return None

def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    logger.info(f"Getting edges for user {user_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/edges/user/{user_id}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        edges = response.json()
        logger.info(f"Found {len(edges)} edges for user")
        
        # Count edge types
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("edge_type")
            if edge_type in edge_types:
                edge_types[edge_type] += 1
            else:
                edge_types[edge_type] = 1
        
        logger.info(f"Edge type distribution: {edge_types}")
        return edges
    except Exception as e:
        logger.error(f"Error getting user edges: {e}")
        return None

def analyze_edge_types(edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the distribution of edge types."""
    if not edges:
        return {}
    
    edge_types = {}
    for edge in edges:
        edge_type = edge.get("edge_type")
        if edge_type in edge_types:
            edge_types[edge_type] += 1
        else:
            edge_types[edge_type] = 1
    
    # Calculate percentages
    total = len(edges)
    percentages = {edge_type: (count / total) * 100 for edge_type, count in edge_types.items()}
    
    logger.info("Edge Type Distribution:")
    for edge_type, percentage in percentages.items():
        logger.info(f"  {edge_type}: {percentage:.1f}% ({edge_types[edge_type]} edges)")
    
    return edge_types

def run_diverse_edges_test():
    """Run the diverse edges test end-to-end."""
    logger.info("=== Starting Diverse Edges Test ===\n")
    
    # 1. Create a test user
    logger.info("1. Creating a test user...")
    user = create_test_user()
    if not user:
        logger.error("Failed to create user. Aborting test.")
        return
    
    # 2. Create a session
    logger.info("\n2. Creating a session...")
    session = create_test_session(user["id"])
    if not session:
        logger.error("Failed to create session. Aborting test.")
        return
    
    # 3. Update session with diverse transcript
    logger.info("\n3. Updating session with diverse transcript...")
    success = update_session_transcript(session["id"], DIVERSE_TRANSCRIPT)
    if not success:
        logger.error("Failed to update session. Aborting test.")
        return
    
    # 4. Process session to extract nodes
    logger.info("\n4. Processing session to extract nodes...")
    nodes = process_session_to_nodes(session["id"])
    if not nodes:
        logger.error("Failed to process nodes. Aborting test.")
        return
    
    # 5. Process embeddings for all nodes
    logger.info("\n5. Processing node embeddings...")
    embedding_result = process_embeddings(batch_size=20)
    if not embedding_result:
        logger.error("Failed to process embeddings. Aborting test.")
        return
    
    # Let's wait a moment to ensure all embeddings are processed
    logger.info("Waiting 5 seconds for embeddings to be fully processed...")
    time.sleep(5)
    
    # 6. Process edges to generate diverse edge types
    logger.info("\n6. Processing edges to generate diverse edge types...")
    edge_result = process_edges(user["id"], batch_size=10)
    if not edge_result:
        logger.error("Failed to process edges. Aborting test.")
        return
    
    # 7. Get and analyze edges
    logger.info("\n7. Getting and analyzing edges...")
    edges = get_user_edges(user["id"])
    if not edges:
        logger.error("Failed to get edges. Aborting test.")
        return
    
    # 8. Detailed analysis of edge types
    logger.info("\n8. Detailed analysis of edge types")
    edge_types = analyze_edge_types(edges)
    
    logger.info("\n=== Diverse Edges Test Completed ===")
    logger.info(f"Created user: {user['id']}")
    logger.info(f"Created session: {session['id']}")
    logger.info(f"Generated {len(nodes)} nodes")
    logger.info(f"Created {len(edges)} edges with {len(edge_types)} different types")
    logger.info(f"Edge type distribution: {edge_types}")

if __name__ == "__main__":
    run_diverse_edges_test()