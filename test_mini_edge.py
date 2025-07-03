"""
Minimalist edge creation test
"""
import logging
import requests
import uuid
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Get a user that was already created in the previous test
def get_users():
    try:
        response = requests.get(f"{BASE_URL}/users/")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get users: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def process_edges(user_id, batch_size=5):
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
        logger.error(f"Error processing edges: {e}")
        return None

def get_user_edges(user_id):
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
        logger.error(f"Error getting user edges: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting mini edge test")
    
    # Get existing users
    users = get_users()
    if not users:
        logger.error("No users found")
        exit(1)
    
    user_id = users[0]["id"]
    logger.info(f"Testing with user ID: {user_id}")
    
    # Process edges
    result = process_edges(user_id)
    if result:
        logger.info(f"Edge processing result: {result}")
    
        # Get edges
        edges = get_user_edges(user_id)
        if edges:
            logger.info(f"Found {len(edges)} edges")
            for i, edge in enumerate(edges[:5]):  # Show up to 5 edges
                logger.info(f"Edge {i+1}: {edge['edge_type']} (strength: {edge['match_strength']})")
                if edge.get("explanation"):
                    logger.info(f"Explanation: {edge['explanation'][:100]}...")
    
    logger.info("Test complete")