"""
Simplified test script for edge creation functionality.

This script tests just the edge processing API endpoint with an existing user.
"""
import requests
import json
import logging
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)

# Connect through the Flask proxy
BASE_URL = "http://0.0.0.0:5000/api/v1"

def create_test_user():
    """Create a test user for testing."""
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json={"email": "edge_test_user@example.com"},
            timeout=10
        )
        
        if response.status_code == 201:
            user = response.json()
            logging.info(f"Created user with ID: {user['id']}")
            return user
        elif response.status_code == 400 and "already exists" in response.text:
            logging.info("User already exists, fetching existing user")
            return get_existing_user("edge_test_user@example.com")
        else:
            logging.error(f"Failed to create user: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def get_existing_user(email):
    """Get existing user by email."""
    try:
        response = requests.get(f"{BASE_URL}/users/", timeout=10)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("email") == email:
                    logging.info(f"Found existing user with ID: {user['id']}")
                    return user
            logging.error(f"User with email {email} not found")
            return None
        else:
            logging.error(f"Failed to get users: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return None

def get_users():
    """Get list of users."""
    try:
        response = requests.get(f"{BASE_URL}/users/", timeout=10)
        if response.status_code == 200:
            users = response.json()
            return users
        else:
            logging.error(f"Failed to get users: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return None

def test_edges():
    """Test edge processing endpoint."""
    logging.info("=== Starting Edge Creation Simple Test ===")
    
    # Get or create test user
    user = create_test_user()
    if not user:
        users = get_users()
        if users and len(users) > 0:
            user = users[0]
            logging.info(f"Using first available user with ID: {user['id']}")
        else:
            logging.error("No users available, cannot proceed with test")
            return
    
    user_id = user["id"]
    logging.info(f"Testing edge creation for user ID: {user_id}")
    
    # Process edges in batch
    try:
        response = requests.post(
            f"{BASE_URL}/edges/process/{user_id}",
            json={"batch_size": 5},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"Edge processing result: {result}")
            
            # Get the user's edges to check what was created
            edges_response = requests.get(
                f"{BASE_URL}/edges/user/{user_id}",
                timeout=10
            )
            
            if edges_response.status_code == 200:
                edges = edges_response.json()
                edge_count = len(edges)
                logging.info(f"Found {edge_count} edges for user {user_id}")
                
                # Count edge types
                edge_types = {}
                for edge in edges:
                    edge_type = edge.get("edge_type", "unknown")
                    if edge_type not in edge_types:
                        edge_types[edge_type] = 0
                    edge_types[edge_type] += 1
                
                # Log edge type counts
                logging.info("Edge type distribution:")
                for edge_type, count in edge_types.items():
                    logging.info(f"  {edge_type}: {count}")
                
                logging.info("=== Edge Creation Test Complete ===")
            else:
                logging.error(f"Failed to get edges: {edges_response.status_code} {edges_response.text}")
        else:
            logging.error(f"Failed to process edges: {response.status_code} {response.text}")
    except Exception as e:
        logging.error(f"Error processing edges: {e}")

if __name__ == "__main__":
    test_edges()