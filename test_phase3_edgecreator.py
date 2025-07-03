"""
Simple test script for Phase 3 - Edge Creation

This script tests the edge creation algorithm implemented in Phase 3
by creating test nodes and running the edge creation process.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:8000/api/v1"


def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user for edge creation testing."""
    try:
        # Create a unique user
        user_email = f"test_edge_creator_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/users/",
            json={
                "username": f"test_edge_creator_{uuid.uuid4().hex[:8]}",
                "email": user_email,
                "full_name": "Test Edge Creator",
                "password": "testpassword123"
            }
        )
        
        if response.status_code == 201:
            logger.info(f"Created test user: {user_email}")
            return response.json()
        else:
            logger.error(f"Failed to create user: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test user: {e}", exc_info=True)
        return None


def create_test_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a test session for the user."""
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/",
            json={
                "user_id": user_id,
                "title": f"Edge Creator Test Session {datetime.now().isoformat()}",
                "description": "Testing the edge creation algorithm"
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


def create_diverse_nodes(session_id: str, user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Create diverse test nodes for thorough edge testing."""
    try:
        # Create 10 nodes with various themes, emotions, and cognition types
        node_data = [
            {
                "text": "I'm excited about starting my new job next week",
                "emotion": "joy",
                "theme": "career",
                "cognition_type": "forward_looking"
            },
            {
                "text": "I'm worried I won't fit in with my new team",
                "emotion": "fear",
                "theme": "career",
                "cognition_type": "catastrophizing"
            },
            {
                "text": "My previous job experience was really disappointing",
                "emotion": "sadness",
                "theme": "career",
                "cognition_type": "ruminating"
            },
            {
                "text": "I should have negotiated for better pay",
                "emotion": "regret",
                "theme": "finance",
                "cognition_type": "self_criticism"
            },
            {
                "text": "My partner is proud of my career growth",
                "emotion": "love",
                "theme": "relationships",
                "cognition_type": "affirming"
            },
            {
                "text": "I'm determined to excel in this role",
                "emotion": "determination",
                "theme": "personal_growth",
                "cognition_type": "goal_setting"
            },
            {
                "text": "I'm anxious about the performance reviews",
                "emotion": "anxiety",
                "theme": "career",
                "cognition_type": "anticipating"
            },
            {
                "text": "I'm grateful for this opportunity",
                "emotion": "gratitude",
                "theme": "spirituality",
                "cognition_type": "meaning_making"
            },
            {
                "text": "I wonder if I deserve this position",
                "emotion": "doubt",
                "theme": "self_image",
                "cognition_type": "questioning"
            },
            {
                "text": "I feel at peace with my decision to change careers",
                "emotion": "contentment",
                "theme": "life_direction",
                "cognition_type": "accepting"
            }
        ]
        
        created_nodes = []
        for data in node_data:
            response = requests.post(
                f"{BASE_URL}/nodes/",
                json={
                    "user_id": user_id,
                    "session_id": session_id,
                    "text": data["text"],
                    "emotion": data["emotion"],
                    "theme": data["theme"],
                    "cognition_type": data["cognition_type"]
                }
            )
            
            if response.status_code == 201:
                created_nodes.append(response.json())
                logger.info(f"Created node: {data['text'][:30]}...")
            else:
                logger.error(f"Failed to create node: {response.status_code}, {response.text}")
        
        logger.info(f"Created {len(created_nodes)} test nodes")
        return created_nodes
    except Exception as e:
        logger.error(f"Error creating test nodes: {e}", exc_info=True)
        return None


def process_embeddings(batch_size: int = 10) -> Optional[Dict[str, Any]]:
    """Process embeddings for all unprocessed nodes."""
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


def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges for the user's nodes."""
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


def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    try:
        response = requests.get(
            f"{BASE_URL}/edges/user/{user_id}"
        )
        
        if response.status_code == 200:
            edges = response.json()
            logger.info(f"Retrieved {len(edges)} edges for user {user_id}")
            return edges
        else:
            logger.error(f"Failed to get edges: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting user edges: {e}", exc_info=True)
        return None


def analyze_edge_types(edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the distribution of edge types."""
    if not edges:
        return {}
    
    edge_types = {}
    for edge in edges:
        edge_type = edge.get("edge_type")
        if edge_type:
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    return edge_types


def run_edge_creation_test():
    """Run the edge creation test end-to-end."""
    logger.info("Starting edge creation test")
    
    # Create a test user
    user = create_test_user()
    if not user:
        logger.error("Failed to create test user, aborting test")
        return
    
    user_id = user["id"]
    logger.info(f"Test user ID: {user_id}")
    
    # Create a test session
    session = create_test_session(user_id)
    if not session:
        logger.error("Failed to create test session, aborting test")
        return
    
    session_id = session["id"]
    logger.info(f"Test session ID: {session_id}")
    
    # Create test nodes
    nodes = create_diverse_nodes(session_id, user_id)
    if not nodes:
        logger.error("Failed to create test nodes, aborting test")
        return
    
    logger.info(f"Created {len(nodes)} test nodes")
    
    # Process embeddings
    embedding_result = process_embeddings()
    if not embedding_result:
        logger.error("Failed to process embeddings, aborting test")
        return
    
    # Process edges
    edge_result = process_edges(user_id)
    if not edge_result:
        logger.error("Failed to process edges, aborting test")
        return
    
    # Get created edges
    edges = get_user_edges(user_id)
    if not edges:
        logger.error("Failed to retrieve edges, aborting test")
        return
    
    # Analyze edge types
    edge_type_distribution = analyze_edge_types(edges)
    logger.info(f"Edge type distribution: {json.dumps(edge_type_distribution, indent=2)}")
    
    if edges:
        # Print detailed edge info
        logger.info("Edge details:")
        for i, edge in enumerate(edges, 1):
            logger.info(f"Edge {i}:")
            logger.info(f"  Type: {edge.get('edge_type')}")
            logger.info(f"  Match Strength: {edge.get('match_strength')}")
            explanation = edge.get('explanation', '')
            if explanation:
                logger.info(f"  Explanation: {explanation[:50]}...")
            else:
                logger.info("  No explanation provided")
    else:
        logger.info("No edges were created")
    
    logger.info("Edge creation test completed successfully")


if __name__ == "__main__":
    run_edge_creation_test()