"""
Test with existing user
"""
import logging
import requests
import json
import sys
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_test_user():
    """Create a test user for testing."""
    try:
        # Create a unique user with deterministic email for testing
        response = requests.post(
            f"{BASE_URL}/users/",
            json={
                "username": "edge_tester",
                "email": "edge_tester@example.com",
                "full_name": "Edge Tester",
                "password": "testpassword123"
            }
        )
        
        if response.status_code == 201:
            logger.info(f"Created test user")
            return response.json()
        else:
            logger.warning(f"Failed to create user: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test user: {e}", exc_info=True)
        return None

def get_existing_user(email="edge_tester@example.com"):
    """Get existing user by email."""
    try:
        response = requests.get(f"{BASE_URL}/users/")
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get("email") == email:
                    logger.info(f"Found existing user with ID: {user['id']}")
                    return user
            logger.warning(f"No user found with email: {email}")
            return None
        else:
            logger.error(f"Failed to get users: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting existing user: {e}", exc_info=True)
        return None

def get_users():
    """Get list of users."""
    try:
        response = requests.get(f"{BASE_URL}/users/")
        if response.status_code == 200:
            users = response.json()
            logger.info(f"Found {len(users)} users")
            return users
        else:
            logger.error(f"Failed to get users: {response.status_code}, {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting users: {e}", exc_info=True)
        return []

def process_edges(user_id, batch_size=5):
    """Process edges for a user."""
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

def main():
    """Main entry point."""
    logger.info("Starting test")
    
    # Try to get existing user or create a new one
    user = get_existing_user()
    if not user:
        # Try to get any user
        users = get_users()
        if users:
            user = users[0]
            logger.info(f"Using existing user: {user['id']}")
        else:
            # Create a new user
            user = create_test_user()
            if not user:
                logger.error("Failed to get or create user, exiting")
                sys.exit(1)
    
    user_id = user["id"]
    logger.info(f"Testing with user ID: {user_id}")
    
    # Process edges
    result = process_edges(user_id)
    if result:
        logger.info(f"Edge processing result: {json.dumps(result, indent=2)}")
    else:
        logger.error("Failed to process edges")
    
    logger.info("Test complete")

if __name__ == "__main__":
    main()