"""
Test script for reflection generation functionality.

This script tests the reflection generation process by:
1. Getting all users
2. For each user, checking if they have unprocessed edges
3. Generating reflections for users with unprocessed edges
4. Reporting the results
"""
import requests
import json
from typing import Dict, Any, List, Optional
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:5000/api/v1"


def get_users() -> Optional[List[Dict[str, Any]]]:
    """Get all users from the API."""
    try:
        response = requests.get(f"{BASE_URL}/users/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error getting users: {e}")
        return None


def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a specific user."""
    try:
        response = requests.get(f"{BASE_URL}/edges/user/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error getting edges for user {user_id}: {e}")
        return None


def check_unprocessed_edges(edges: List[Dict[str, Any]]) -> int:
    """Check how many unprocessed edges a user has."""
    return sum(1 for edge in edges if not edge.get('is_processed', True))


def generate_reflections_for_user(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Generate reflections for a specific user."""
    try:
        response = requests.post(
            f"{BASE_URL}/reflections/user/{user_id}/generate?batch_size={batch_size}"
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error generating reflections for user {user_id}: {e}")
        return None


def get_user_reflections(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get reflections for a specific user."""
    try:
        response = requests.get(f"{BASE_URL}/reflections/user/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error getting reflections for user {user_id}: {e}")
        return None


def main():
    """Run the reflection generation test."""
    logger.info("Starting reflection generation test")
    
    # Get all users
    users = get_users()
    if not users:
        logger.error("No users found, exiting")
        return
    
    logger.info(f"Found {len(users)} users")
    
    # Find users with unprocessed edges
    users_with_unprocessed_edges = []
    for user in users:
        user_id = user.get('id')
        if not user_id:
            continue
        
        edges = get_user_edges(user_id)
        if not edges:
            logger.warning(f"No edges found for user {user_id}")
            continue
        
        unprocessed_count = check_unprocessed_edges(edges)
        if unprocessed_count > 0:
            logger.info(f"User {user_id} has {unprocessed_count} unprocessed edges")
            users_with_unprocessed_edges.append({
                'user_id': user_id,
                'unprocessed_count': unprocessed_count
            })
    
    if not users_with_unprocessed_edges:
        logger.warning("No users with unprocessed edges found, exiting")
        return
    
    logger.info(f"Found {len(users_with_unprocessed_edges)} users with unprocessed edges")
    
    # Generate reflections for users with unprocessed edges
    for user_data in users_with_unprocessed_edges:
        user_id = user_data['user_id']
        batch_size = min(user_data['unprocessed_count'], 5)  # Process up to 5 edges at a time
        
        logger.info(f"Generating reflections for user {user_id} with batch size {batch_size}")
        
        # Get previous reflection count
        prev_reflections = get_user_reflections(user_id)
        prev_count = len(prev_reflections) if prev_reflections else 0
        
        # Generate reflections
        start_time = time.time()
        result = generate_reflections_for_user(user_id, batch_size)
        elapsed_time = time.time() - start_time
        
        if not result:
            logger.error(f"Failed to generate reflections for user {user_id}")
            continue
        
        logger.info(f"Reflection generation for user {user_id} completed in {elapsed_time:.2f} seconds")
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        # Get updated reflection count
        new_reflections = get_user_reflections(user_id)
        new_count = len(new_reflections) if new_reflections else 0
        
        logger.info(f"Added {new_count - prev_count} new reflections for user {user_id}")
        
        # Log the actual reflections
        if new_reflections and new_count > prev_count:
            for i, reflection in enumerate(new_reflections[:new_count - prev_count]):
                logger.info(f"New reflection {i+1}: {reflection.get('generated_text', '')[:100]}...")
    
    logger.info("Reflection generation test completed")


if __name__ == "__main__":
    main()