"""
Test the improvements to the edge creation process by directly creating test data and using the OpenAI API.

This script:
1. Creates test nodes with specific values
2. Tests the modified edge creation logic from openai_utils.py
"""
import os
import uuid
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import json

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import OpenAI utils
sys.path.append(os.getcwd())
from app.utils.openai_utils import create_edges_between_nodes, calculate_cosine_similarity

def create_test_data():
    """Create test nodes with specific values for testing."""
    
    # Create a current node
    current_node = {
        "id": str(uuid.uuid4()),
        "text": "I feel anxious about the upcoming presentation at work. I haven't prepared enough.",
        "theme": "work",
        "cognition_type": "worry",
        "emotion": "anxiety",
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create candidate nodes
    candidate_nodes = [
        {
            "id": str(uuid.uuid4()),
            "text": "My manager has been critical of my last few presentations. I'm worried about more negative feedback.",
            "theme": "work",
            "cognition_type": "fear",
            "emotion": "worry",
            "user_id": current_node["user_id"],
            "session_id": str(uuid.uuid4()),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "text": "I need to work on my public speaking skills to feel more confident.",
            "theme": "personal_growth",
            "cognition_type": "reflection",
            "emotion": "determination",
            "user_id": current_node["user_id"],
            "session_id": str(uuid.uuid4()),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "text": "When I present to large groups, I often feel my heart racing and my hands shaking.",
            "theme": "health",
            "cognition_type": "physical_sensation",
            "emotion": "anxiety",
            "user_id": current_node["user_id"],
            "session_id": str(uuid.uuid4()),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
        }
    ]
    
    return current_node, candidate_nodes

def test_edge_creation():
    """Test the edge creation process with our improvements."""
    
    # Create test data
    current_node, candidate_nodes = create_test_data()
    logger.info(f"Current node: {current_node['text']}")
    
    for i, node in enumerate(candidate_nodes):
        logger.info(f"Candidate node {i+1}: {node['text']}")
    
    # Call the edge creation function
    edges = create_edges_between_nodes(current_node, candidate_nodes)
    
    # Check the results
    logger.info(f"Created {len(edges)} edges")
    for i, edge in enumerate(edges):
        logger.info(f"Edge {i+1}:")
        logger.info(f"  From: {edge.get('from_node_id')}")
        logger.info(f"  To: {edge.get('to_node_id')}")
        logger.info(f"  Type: {edge.get('edge_type')}")
        logger.info(f"  Strength: {edge.get('match_strength')}")
        logger.info(f"  Explanation: {edge.get('explanation')}")
        
if __name__ == "__main__":
    test_edge_creation()