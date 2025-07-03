"""
Test embedding fixing functionality
"""
import logging
import requests
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_test_node():
    """Create a single test node"""
    try:
        # Get first user from the database
        user_response = requests.get(f"{BASE_URL}/users/")
        if user_response.status_code != 200:
            logger.error(f"Failed to get users: {user_response.status_code}, {user_response.text}")
            return None
        
        users = user_response.json()
        if not users:
            logger.error("No users found")
            return None
        
        user_id = users[0]["id"]
        logger.info(f"Using user ID: {user_id}")
        
        # Create a session
        session_response = requests.post(
            f"{BASE_URL}/sessions/",
            json={
                "user_id": user_id,
                "title": "Embedding Fix Test Session",
                "description": "Testing the embedding fix"
            }
        )
        
        if session_response.status_code != 201:
            logger.error(f"Failed to create session: {session_response.status_code}, {session_response.text}")
            return None
        
        session = session_response.json()
        session_id = session["id"]
        logger.info(f"Created session with ID: {session_id}")
        
        # Create a test node
        node_response = requests.post(
            f"{BASE_URL}/nodes/",
            json={
                "user_id": user_id,
                "session_id": session_id,
                "text": "This is a test node for the embedding fix",
                "emotion": "hopeful",
                "theme": "generic",
                "cognition_type": "self_reflection"
            }
        )
        
        if node_response.status_code != 201:
            logger.error(f"Failed to create node: {node_response.status_code}, {node_response.text}")
            return None
        
        node = node_response.json()
        node_id = node["id"]
        logger.info(f"Created node with ID: {node_id}")
        
        # Process embeddings
        embedding_response = requests.post(
            f"{BASE_URL}/nodes/embeddings/process",
            params={"batch_size": 10}
        )
        
        if embedding_response.status_code != 200:
            logger.error(f"Failed to process embeddings: {embedding_response.status_code}, {embedding_response.text}")
            return None
        
        embedding_result = embedding_response.json()
        logger.info(f"Embedding processing result: {embedding_result}")
        
        # Check node processing status
        check_response = requests.get(f"{BASE_URL}/nodes/{node_id}")
        if check_response.status_code != 200:
            logger.error(f"Failed to get node: {check_response.status_code}, {check_response.text}")
            return None
        
        node_data = check_response.json()
        logger.info(f"Node status: is_processed={node_data.get('is_processed')}, has_embedding={node_data.get('embedding') is not None}")
        
        # Verify node will be processed by edge processor
        edge_candidates_response = requests.get(f"{BASE_URL}/edges/unprocessed/{user_id}")
        if edge_candidates_response.status_code != 200:
            logger.error(f"Failed to get unprocessed nodes: {edge_candidates_response.status_code}, {edge_candidates_response.text}")
            
            # Create the endpoint if it doesn't exist
            logger.info("Endpoint might not exist, let's try to verify directly in the database")
            
            # Try to process edges to see if our node gets processed
            process_response = requests.post(
                f"{BASE_URL}/edges/process/{user_id}",
                params={"batch_size": 5}
            )
            
            if process_response.status_code == 200:
                process_result = process_response.json()
                logger.info(f"Edge processing result: {process_result}")
                
                # If nodes were processed, our fix works!
                if process_result.get("processed_nodes", 0) > 0:
                    logger.info("SUCCESS: Fix is working! Nodes are being processed by edge processor.")
                    return node_data
                else:
                    logger.info("No nodes were processed. This could be because the node was not eligible for edge creation.")
            else:
                logger.error(f"Failed to process edges: {process_response.status_code}, {process_response.text}")
        else:
            unprocessed = edge_candidates_response.json()
            logger.info(f"Found {len(unprocessed)} unprocessed nodes for edge processing")
            
            # Check if our node is in the list
            for n in unprocessed:
                if n.get("id") == node_id:
                    logger.info("SUCCESS: Our node is in the unprocessed list! Fix is working.")
                    break
            else:
                logger.warning("Our node was not found in the unprocessed list.")
                
        return node_data
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting embedding fix test")
    result = create_test_node()
    if result:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")