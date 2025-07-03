"""
Test script for batch reflection generation across all users.

This script tests the reflection generation process by:
1. Generating reflections for all users with unprocessed edges
2. Reporting the results
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


def generate_reflections_for_all(batch_size_per_user: int = 5, overall_batch_size: int = 50) -> Optional[Dict[str, Any]]:
    """Generate reflections for all users with unprocessed edges."""
    try:
        response = requests.post(
            f"{BASE_URL}/reflections/generate?batch_size_per_user={batch_size_per_user}&overall_batch_size={overall_batch_size}"
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error generating reflections for all users: {e}")
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
    """Run the reflection generation test for all users."""
    logger.info("Starting batch reflection generation test")
    
    # Get all users
    users = get_users()
    if not users:
        logger.error("No users found, exiting")
        return
    
    logger.info(f"Found {len(users)} users")
    
    # Get unprocessed edge counts
    total_unprocessed = 0
    user_unprocessed_edges = {}
    
    for user in users:
        user_id = user.get('id')
        if not user_id:
            continue
        
        edges = get_user_edges(user_id)
        if not edges:
            logger.warning(f"No edges found for user {user_id}")
            continue
        
        unprocessed_count = check_unprocessed_edges(edges)
        total_unprocessed += unprocessed_count
        
        if unprocessed_count > 0:
            logger.info(f"User {user_id} has {unprocessed_count} unprocessed edges")
            user_unprocessed_edges[user_id] = unprocessed_count
    
    if total_unprocessed == 0:
        logger.warning("No unprocessed edges found, exiting")
        return
    
    logger.info(f"Found {total_unprocessed} total unprocessed edges across {len(user_unprocessed_edges)} users")
    
    # Store previous reflection counts
    prev_reflection_counts = {}
    for user_id in user_unprocessed_edges.keys():
        reflections = get_user_reflections(user_id)
        prev_reflection_counts[user_id] = len(reflections) if reflections else 0
    
    # Generate reflections for all users
    logger.info("Generating reflections for all users")
    batch_size_per_user = 5
    overall_batch_size = 50
    
    start_time = time.time()
    result = generate_reflections_for_all(batch_size_per_user, overall_batch_size)
    elapsed_time = time.time() - start_time
    
    if not result:
        logger.error("Failed to generate reflections")
        return
    
    logger.info(f"Batch reflection generation completed in {elapsed_time:.2f} seconds")
    logger.info(f"Result: {json.dumps(result, indent=2)}")
    
    # Check new reflection counts
    total_new_reflections = 0
    
    for user_id, prev_count in prev_reflection_counts.items():
        new_reflections = get_user_reflections(user_id)
        new_count = len(new_reflections) if new_reflections else 0
        added_count = new_count - prev_count
        
        if added_count > 0:
            total_new_reflections += added_count
            logger.info(f"Added {added_count} new reflections for user {user_id}")
            
            # Log the actual reflections
            if new_reflections:
                for i, reflection in enumerate(new_reflections[:added_count]):
                    logger.info(f"New reflection {i+1}: {reflection.get('generated_text', '')[:100]}...")
    
    logger.info(f"Total new reflections generated: {total_new_reflections}")
    logger.info("Batch reflection generation test completed")


if __name__ == "__main__":
    main()