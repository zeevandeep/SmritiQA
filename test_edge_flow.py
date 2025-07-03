"""
Full edge creation test flow
"""
import logging
import requests
import json
import sys
import time
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_test_user():
    """Create a test user for edge flow testing."""
    user_id = str(uuid.uuid4())[:8]
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json={
                "username": f"edge_flow_{user_id}",
                "email": f"edge_flow_{user_id}@example.com",
                "full_name": "Edge Flow Test User",
                "password": "testpassword123"
            }
        )
        
        if response.status_code == 201:
            logger.info(f"Created test user: edge_flow_{user_id}@example.com")
            return response.json()
        else:
            logger.error(f"Failed to create user: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test user: {e}", exc_info=True)
        return None

def create_test_session(user_id):
    """Create a test session for the user."""
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/",
            json={
                "user_id": user_id,
                "title": f"Edge Flow Test Session {datetime.now().isoformat()}",
                "description": "Testing the edge creation flow"
            }
        )
        
        if response.status_code == 201:
            logger.info(f"Created test session for user {user_id}")
            return response.json()
        else:
            logger.error(f"Failed to create session: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test session: {e}", exc_info=True)
        return None

def create_test_nodes(session_id, user_id):
    """Create test nodes with various attributes for edge testing."""
    nodes_data = [
        {
            "text": "I'm feeling anxious about my upcoming job interview",
            "emotion": "anxiety",
            "theme": "career",
            "cognition_type": "catastrophizing"
        },
        {
            "text": "I keep thinking I'll say something stupid and ruin my chances",
            "emotion": "fear",
            "theme": "career",
            "cognition_type": "ruminating"
        },
        {
            "text": "My previous interview experiences have all been disasters",
            "emotion": "sadness",
            "theme": "career",
            "cognition_type": "overgeneralizing"
        },
        {
            "text": "I should have prepared more for this interview",
            "emotion": "regret",
            "theme": "self_development",
            "cognition_type": "self_criticism"
        },
        {
            "text": "What if I actually do well and get the job?",
            "emotion": "hope",
            "theme": "career",
            "cognition_type": "forward_looking"
        }
    ]
    
    created_nodes = []
    for node_data in nodes_data:
        try:
            response = requests.post(
                f"{BASE_URL}/nodes/",
                json={
                    "user_id": user_id,
                    "session_id": session_id,
                    "text": node_data["text"],
                    "emotion": node_data["emotion"],
                    "theme": node_data["theme"],
                    "cognition_type": node_data["cognition_type"]
                }
            )
            
            if response.status_code == 201:
                created_node = response.json()
                logger.info(f"Created node: {node_data['text'][:30]}...")
                created_nodes.append(created_node)
            else:
                logger.error(f"Failed to create node: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Error creating node: {e}", exc_info=True)
    
    logger.info(f"Created {len(created_nodes)} test nodes")
    return created_nodes

def process_embeddings(batch_size=10):
    """Process embeddings for all nodes."""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/embeddings/process",
            params={"batch_size": batch_size}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Processed embeddings: {result}")
            return result
        else:
            logger.error(f"Failed to process embeddings: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error processing embeddings: {e}", exc_info=True)
        return None

def process_edges(user_id, batch_size=5):
    """Process edges for the user."""
    try:
        response = requests.post(
            f"{BASE_URL}/edges/process/{user_id}",
            params={"batch_size": batch_size}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Processed edges: {result}")
            return result
        else:
            logger.error(f"Failed to process edges: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error processing edges: {e}", exc_info=True)
        return None

def get_user_edges(user_id):
    """Get all edges for a user."""
    try:
        response = requests.get(f"{BASE_URL}/edges/user/{user_id}")
        if response.status_code == 200:
            edges = response.json()
            logger.info(f"Retrieved {len(edges)} edges for user {user_id}")
            return edges
        else:
            logger.error(f"Failed to get edges: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting edges: {e}", exc_info=True)
        return None

def main():
    """Run the full edge creation test flow."""
    logger.info("Starting edge creation flow test")
    
    # Create test user
    user = create_test_user()
    if not user:
        logger.error("Failed to create test user, exiting")
        sys.exit(1)
    
    user_id = user["id"]
    logger.info(f"Test user ID: {user_id}")
    
    # Create test session
    session = create_test_session(user_id)
    if not session:
        logger.error("Failed to create test session, exiting")
        sys.exit(1)
    
    session_id = session["id"]
    logger.info(f"Test session ID: {session_id}")
    
    # Create test nodes
    nodes = create_test_nodes(session_id, user_id)
    if not nodes:
        logger.error("Failed to create test nodes, exiting")
        sys.exit(1)
    
    logger.info(f"Created {len(nodes)} test nodes")
    
    # Process embeddings
    embeddings_result = process_embeddings()
    if not embeddings_result:
        logger.error("Failed to process embeddings, exiting")
        sys.exit(1)
    
    # Allow some time for processing and retry if needed
    logger.info("Waiting for embedding processing to complete...")
    max_retries = 3
    for i in range(max_retries):
        time.sleep(3)
        # Verify embeddings were created by checking nodes in the user's session
        try:
            check_response = requests.get(f"{BASE_URL}/nodes/session/{session_id}")
            if check_response.status_code == 200:
                nodes = check_response.json()
                logger.info(f"Session has {len(nodes)} nodes")
                for node in nodes:
                    logger.info(f"Node {node['id']}: has_embedding={node.get('embedding') is not None}, is_processed={node.get('is_processed')}")
                break
        except Exception as e:
            logger.error(f"Error checking nodes: {e}")
            if i == max_retries - 1:
                logger.error("Maximum retries reached for embedding check")
            else:
                logger.info(f"Retrying in 3 seconds... (attempt {i+1}/{max_retries})")
    
    # Process edges
    edges_result = process_edges(user_id)
    if not edges_result:
        logger.error("Failed to process edges, exiting")
        sys.exit(1)
    
    # Allow some time for edge processing
    logger.info("Waiting a few seconds for edge processing to complete...")
    time.sleep(3)
    
    # Get created edges
    edges = get_user_edges(user_id)
    if not edges:
        logger.warning("No edges were created or retrieved")
    else:
        logger.info(f"Created {len(edges)} edges")
        
        # Print edge details
        for i, edge in enumerate(edges, 1):
            logger.info(f"Edge {i}:")
            logger.info(f"  Type: {edge.get('edge_type')}")
            logger.info(f"  Match Strength: {edge.get('match_strength')}")
            explanation = edge.get('explanation', '')
            if explanation:
                logger.info(f"  Explanation: {explanation[:100]}...")
            else:
                logger.info("  No explanation provided")
    
    logger.info("Edge creation flow test completed successfully")

if __name__ == "__main__":
    main()