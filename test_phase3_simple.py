"""
Simplified test script for Phase 3 functionality.

This script:
1. Creates a user
2. Creates a session with transcript
3. Processes nodes
4. Generates embeddings for the nodes
5. Creates edges
"""
import requests
import json
import time
import logging
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)

# Connect directly to FastAPI server
BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user."""
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json={"email": "phase3_test@example.com"},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create user: {e}")
        return None
    
    if response.status_code == 201:
        user = response.json()
        logging.info(f"Created user with ID: {user['id']}")
        return user
    elif response.status_code == 400 and "already exists" in response.text:
        # Get existing user
        try:
            response = requests.get(f"{BASE_URL}/users/", timeout=10)
            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u["email"] == "phase3_test@example.com"), None)
                if user:
                    logging.info(f"Using existing user with ID: {user['id']}")
                    return user
                logging.error("Could not find existing user")
                return None
            logging.error(f"Failed to get users: {response.status_code} {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get users: {e}")
            return None
    
    logging.error(f"Failed to create user: {response.status_code} {response.text}")
    return None


def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session."""
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/",
            json={"user_id": user_id, "duration_seconds": 300},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to create session: {e}")
        return None
    
    if response.status_code == 201:
        session = response.json()
        logging.info(f"Created session with ID: {session['id']}")
        return session
    
    logging.error(f"Failed to create session: {response.status_code} {response.text}")
    return None


def update_session_transcript(session_id: str, transcript: str) -> bool:
    """Update session with transcript."""
    try:
        response = requests.put(
            f"{BASE_URL}/sessions/{session_id}/transcript",
            json={"transcript": transcript},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update session transcript: {e}")
        return False
    
    if response.status_code == 200:
        logging.info(f"Updated session with transcript")
        return True
    
    logging.error(f"Failed to update session transcript: {response.status_code} {response.text}")
    return False


def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Process session transcript to extract nodes."""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=60  # Longer timeout for OpenAI processing
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to process nodes: {e}")
        return None
    
    if response.status_code == 200:
        nodes = response.json()
        logging.info(f"Processed transcript and extracted {len(nodes)} nodes")
        for i, node in enumerate(nodes, 1):
            logging.info(f"Node {i}:")
            logging.info(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
            logging.info(f"  Emotion: {node['emotion']}")
            logging.info(f"  Theme: {node['theme']}")
            logging.info(f"  Cognition Type: {node['cognition_type']}")
        return nodes
    
    logging.error(f"Failed to process transcript: {response.status_code} {response.text}")
    return None


def process_embeddings(batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process a batch of nodes to generate embeddings."""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/embeddings/batch",
            json={"batch_size": batch_size},
            timeout=60  # Longer timeout for OpenAI embeddings
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to process embeddings: {e}")
        return None
    
    if response.status_code == 200:
        stats = response.json()
        logging.info(f"Processed {stats.get('nodes_processed', 0)} node embeddings")
        return stats
    
    logging.error(f"Failed to process embeddings: {response.status_code} {response.text}")
    return None


def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges for a user."""
    try:
        response = requests.post(
            f"{BASE_URL}/edges/batch",
            json={"user_id": user_id, "batch_size": batch_size},
            timeout=60  # Longer timeout for edge processing
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to process edges: {e}")
        return None
    
    if response.status_code == 200:
        stats = response.json()
        logging.info(f"Processed edges: {stats}")
        return stats
    
    logging.error(f"Failed to process edges: {response.status_code} {response.text}")
    return None


def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    try:
        response = requests.get(
            f"{BASE_URL}/edges/user/{user_id}",
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get user edges: {e}")
        return None
    
    if response.status_code == 200:
        edges = response.json()
        logging.info(f"Retrieved {len(edges)} edges for user")
        # Log edge types for analysis
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("edge_type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        logging.info("Edge type distribution:")
        for edge_type, count in edge_types.items():
            logging.info(f"  {edge_type}: {count}")
        
        return edges
    
    logging.error(f"Failed to get user edges: {response.status_code} {response.text}")
    return None


def run_test():
    """Run the simplified Phase 3 test."""
    logging.info("=== Starting Phase 3 Simplified Test ===")
    
    # Create or get existing user
    user = create_test_user()
    if not user:
        logging.error("Failed to get/create user, exiting test")
        return
    
    user_id = user["id"]
    
    # Create a session
    session = create_test_session(user_id)
    if not session:
        logging.error("Failed to create session, exiting test")
        return
    
    session_id = session["id"]
    
    # Create transcript with emotional and cognitive diversity
    transcript = """
    Today I'm feeling really anxious about my upcoming presentation. 
    The last time I presented, I completely froze up and couldn't remember my points.
    But I also know that I've prepared better this time, and I should give myself credit for that.
    
    I'm frustrated with my colleague who always interrupts me in meetings. 
    She doesn't seem to value my input, and it makes me doubt my expertise sometimes.
    Maybe I need to be more assertive and stand up for myself.
    
    On a positive note, I'm excited about the weekend trip I've planned with my family.
    It's been months since we've had quality time together, and I miss them.
    
    When I think about my career trajectory, I worry I'm not moving forward fast enough.
    Others my age seem to be progressing more quickly. Am I falling behind?
    But then again, everyone has their own path, and comparison isn't always helpful.
    """
    
    if not update_session_transcript(session_id, transcript):
        logging.error("Failed to update session transcript, exiting test")
        return
    
    # Process session to extract nodes
    nodes = process_session_to_nodes(session_id)
    if not nodes:
        logging.error("Failed to process nodes, exiting test")
        return
    
    # Process node embeddings
    stats = process_embeddings()
    if not stats:
        logging.error("Failed to process embeddings, exiting test")
        return
    
    # Process edges
    edge_stats = process_edges(user_id)
    if not edge_stats:
        logging.error("Failed to process edges, exiting test")
        return
    
    # Get user edges
    edges = get_user_edges(user_id)
    if not edges:
        logging.error("Failed to get user edges, exiting test")
        return
    
    logging.info("=== Phase 3 Simplified Test Complete ===")


if __name__ == "__main__":
    run_test()