"""
Test script for Phase 3 functionality of the Smriti API.

This script tests the end-to-end flow of Phase 3:
1. Create a user (or use existing)
2. Create a session with transcript
3. Process the session to extract nodes
4. Run the batch embedding process
5. Create edges between nodes
6. Verify edge creation
"""
import logging
import requests
import json
import time
import uuid
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "http://localhost:5000/api/v1"
TIMEOUT = 120  # 2 minutes

# Sample transcript for testing
SAMPLE_TRANSCRIPT = """
I've been reflecting on my career path today. The promotion I've been working towards finally came through, and I felt a burst of pride and satisfaction when my manager called me with the news. It validates all the late nights and extra effort I've put in over the past year.

But after the initial excitement wore off, I started feeling anxious about the new responsibilities. What if I can't handle the increased workload? What if the team doesn't respect me as a leader? I keep thinking about how my predecessor struggled with managing the team dynamics.

I also realized that I've been neglecting my health for this job. Last weekend, my friend invited me for a hiking trip and I declined because I needed to prepare for a presentation. I've been making these kinds of choices a lot lately, always prioritizing work over personal life.

There's a part of me that wonders if this career path is what I truly want, or if I'm just following expectations others have set for me. My parents always emphasized professional success, and I've internalized that. But when I imagine my ideal life, it involves more balance and creativity.

The promotion comes with a salary increase, which makes me feel more financially secure. This morning I checked my savings account and realized I'm finally getting closer to my goal of buying a home. That's a dream I've had since childhood - having a place that feels truly mine.

I need to find a better way to balance my ambition with my wellbeing. Maybe the new position will actually give me more control over my schedule? I'm hoping I can establish better boundaries than I have in the past.
"""


def create_user() -> Optional[Dict[str, Any]]:
    """Create a new user for testing."""
    logger.info("Creating a new test user...")
    
    try:
        user_data = {
            "email": f"test_user_{uuid.uuid4()}@example.com"
        }
        
        response = requests.post(f"{BASE_URL}/users", json=user_data, timeout=TIMEOUT)
        response.raise_for_status()
        
        user = response.json()
        logger.info(f"Created user with ID: {user['id']}")
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


def create_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a new session for testing."""
    logger.info(f"Creating a new session for user {user_id}...")
    
    try:
        session_data = {
            "user_id": user_id,
            "duration_seconds": 300  # 5 minutes
        }
        
        response = requests.post(f"{BASE_URL}/sessions", json=session_data, timeout=TIMEOUT)
        response.raise_for_status()
        
        session = response.json()
        logger.info(f"Created session with ID: {session['id']}")
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return None


def update_session_transcript(session_id: str, transcript: str) -> bool:
    """Update session with transcript."""
    logger.info(f"Updating session {session_id} with transcript...")
    
    try:
        data = {"raw_transcript": transcript}
        response = requests.patch(f"{BASE_URL}/sessions/{session_id}", json=data, timeout=TIMEOUT)
        response.raise_for_status()
        
        logger.info("Successfully updated session with transcript")
        return True
    except Exception as e:
        logger.error(f"Error updating session transcript: {e}")
        return False


def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Process session transcript to extract nodes."""
    logger.info(f"Processing session {session_id} to extract nodes...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        nodes = response.json()
        logger.info(f"Successfully processed transcript. Extracted {len(nodes)} nodes.")
        return nodes
    except requests.exceptions.Timeout:
        logger.warning("Request timed out. The operation may still be processing on the server.")
        logger.info("Waiting for 30 seconds before checking if nodes were created...")
        time.sleep(30)
        
        # Check if nodes were created despite timeout
        response = requests.get(f"{BASE_URL}/nodes/session/{session_id}")
        if response.status_code == 200:
            nodes = response.json()
            logger.info(f"Found {len(nodes)} nodes after timeout.")
            return nodes
        return None
    except Exception as e:
        logger.error(f"Error processing session to nodes: {e}")
        return None


def process_node_embeddings(batch_size: int = 50) -> Optional[Dict[str, Any]]:
    """Process a batch of nodes to generate embeddings."""
    logger.info(f"Processing node embeddings with batch size {batch_size}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/embeddings/process?batch_size={batch_size}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Embedding processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing node embeddings: {e}")
        return None


def process_edges(user_id: str, batch_size: int = 1) -> Optional[Dict[str, Any]]:
    """Process a batch of edges for a user."""
    logger.info(f"Processing edges for user {user_id} with batch size {batch_size}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/edges/process?user_id={user_id}&batch_size={batch_size}",
            timeout=TIMEOUT
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
    logger.info(f"Getting edges for user {user_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/edges?user_id={user_id}")
        response.raise_for_status()
        
        edges = response.json()
        logger.info(f"Found {len(edges)} edges for user {user_id}")
        return edges
    except Exception as e:
        logger.error(f"Error getting user edges: {e}")
        return None


def get_node_details(node_id: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific node."""
    logger.info(f"Getting details for node {node_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/nodes/{node_id}")
        response.raise_for_status()
        
        node = response.json()
        return node
    except Exception as e:
        logger.error(f"Error getting node details: {e}")
        return None


def get_edge_details(edge_id: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific edge."""
    logger.info(f"Getting details for edge {edge_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/edges/{edge_id}")
        response.raise_for_status()
        
        edge = response.json()
        return edge
    except Exception as e:
        logger.error(f"Error getting edge details: {e}")
        return None


def test_phase3():
    """Test Phase 3 functionality."""
    logger.info("=== Starting Phase 3 Test ===")
    
    # 1. Create a user
    logger.info("\n1. Creating a test user...")
    user = create_user()
    if not user:
        logger.error("Failed to create user. Aborting test.")
        return
    
    user_id = user["id"]
    
    # 2. Create a session
    logger.info("\n2. Creating a session...")
    session = create_session(user_id)
    if not session:
        logger.error("Failed to create session. Aborting test.")
        return
    
    session_id = session["id"]
    
    # 3. Update session with transcript
    logger.info("\n3. Updating session with transcript...")
    success = update_session_transcript(session_id, SAMPLE_TRANSCRIPT)
    if not success:
        logger.error("Failed to update session transcript. Aborting test.")
        return
    
    # 4. Process session to extract nodes
    logger.info("\n4. Processing session to extract nodes...")
    logger.info("   This may take up to 2 minutes as it calls OpenAI...")
    nodes = process_session_to_nodes(session_id)
    if not nodes:
        logger.error("Failed to process session to nodes. Aborting test.")
        return
    
    # Print a summary of each node
    logger.info(f"Extracted {len(nodes)} nodes:")
    for i, node in enumerate(nodes[:3], 1):  # Show first 3 nodes
        logger.info(f"\nNode {i}:")
        logger.info(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
        logger.info(f"  Emotion: {node['emotion']}")
        logger.info(f"  Theme: {node['theme']}")
    
    # 5. Process node embeddings
    logger.info("\n5. Processing node embeddings...")
    logger.info("   This may take some time as it calls OpenAI for embeddings...")
    embedding_result = process_node_embeddings(batch_size=len(nodes))
    if not embedding_result:
        logger.error("Failed to process node embeddings. Aborting test.")
        return
    
    # 6. Process edges
    logger.info("\n6. Processing edges...")
    logger.info("   This may take some time as it calls OpenAI for edge analysis...")
    edge_result = process_edges(user_id, batch_size=2)  # Process up to 2 source nodes
    if not edge_result:
        logger.error("Failed to process edges. Aborting test.")
        return
    
    # 7. Verify edge creation
    logger.info("\n7. Verifying edge creation...")
    edges = get_user_edges(user_id)
    if not edges:
        logger.info("No edges were created. This could mean:")
        logger.info("- No suitable node pairs were found")
        logger.info("- All nodes already have the maximum number of edges")
        logger.info("- There was an error in the edge creation process")
        return
    
    # Print details of edges
    logger.info(f"Found {len(edges)} edges:")
    for i, edge in enumerate(edges[:3], 1):  # Show first 3 edges
        logger.info(f"\nEdge {i}:")
        logger.info(f"  Edge Type: {edge['edge_type']}")
        logger.info(f"  Match Strength: {edge['match_strength']}")
        logger.info(f"  Session Relation: {edge['session_relation']}")
        
        # Get details of connected nodes
        from_node = get_node_details(edge['from_node'])
        to_node = get_node_details(edge['to_node'])
        
        if from_node and to_node:
            logger.info(f"  From Node: {from_node['text'][:50]}..." if len(from_node['text']) > 50 else f"  From Node: {from_node['text']}")
            logger.info(f"  To Node: {to_node['text'][:50]}..." if len(to_node['text']) > 50 else f"  To Node: {to_node['text']}")
    
    logger.info("\n=== Phase 3 Test Complete ===")


if __name__ == "__main__":
    test_phase3()