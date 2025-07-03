"""
Simple test script to verify edge type variety.

This script focuses specifically on analyzing openai_utils.py's edge creation function.
"""
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the OpenAI utilities directly
# This approach bypasses the full API testing flow
try:
    from app.utils.openai_utils import create_edges_between_nodes
except ImportError:
    logger.error("Failed to import create_edges_between_nodes from app.utils.openai_utils")
    exit(1)

# Test data - a variety of thought pairs designed to trigger different edge types
TEST_PAIRS = [
    # Pair 1: Emotional shift
    {
        "from_node": {
            "text": "I felt anxious at work today during a meeting with clients.",
            "emotion": "anxiety",
            "theme": "work and stress",
            "cognition_type": "observation",
            "belief_value": None,
            "contradiction_flag": False,
            "id": "node1",
            "session_id": "session1"
        },
        "to_node": {
            "text": "I managed to stay calm.",
            "emotion": "calmness", 
            "theme": "self-control",
            "cognition_type": "observation",
            "belief_value": "I can remain calm under pressure.",
            "contradiction_flag": False,
            "id": "node2",
            "session_id": "session1"
        }
    },
    
    # Pair 2: Contradiction loop
    {
        "from_node": {
            "text": "I believe I'm fundamentally not good at public speaking.",
            "emotion": "insecurity",
            "theme": "public speaking",
            "cognition_type": "belief",
            "belief_value": "I am not good at public speaking.",
            "contradiction_flag": False,
            "id": "node3",
            "session_id": "session1"
        },
        "to_node": {
            "text": "I've given good presentations before and received positive feedback.",
            "emotion": "confidence",
            "theme": "public speaking",
            "cognition_type": "memory",
            "belief_value": "I can be good at public speaking.",
            "contradiction_flag": True,
            "id": "node4",
            "session_id": "session1"
        }
    },
    
    # Pair 3: Recurrence theme
    {
        "from_node": {
            "text": "My colleagues seem to present so effortlessly.",
            "emotion": "envy",
            "theme": "comparison",
            "cognition_type": "observation",
            "belief_value": None,
            "contradiction_flag": False,
            "id": "node5",
            "session_id": "session1"
        },
        "to_node": {
            "text": "Perhaps I should focus on my strengths instead of comparing myself to others.",
            "emotion": "determination",
            "theme": "comparison",
            "cognition_type": "realization",
            "belief_value": "It's better to focus on my strengths than compare myself to others.",
            "contradiction_flag": False,
            "id": "node6",
            "session_id": "session1"
        }
    },
    
    # Pair 4: Belief mutation
    {
        "from_node": {
            "text": "When I think about it rationally, I know that one presentation won't define my career.",
            "emotion": "thoughtfulness",
            "theme": "perspective",
            "cognition_type": "reasoning",
            "belief_value": "One event does not define my worth.",
            "contradiction_flag": False,
            "id": "node7", 
            "session_id": "session1"
        },
        "to_node": {
            "text": "I need to practice more to build my confidence.",
            "emotion": "determination",
            "theme": "self-improvement",
            "cognition_type": "planning",
            "belief_value": "Practice builds confidence.",
            "contradiction_flag": False,
            "id": "node8",
            "session_id": "session1"
        }
    },
    
    # Pair 5: Recurrence emotion
    {
        "from_node": {
            "text": "I remember feeling this same anxiety before my college thesis presentation.",
            "emotion": "anxiety",
            "theme": "memory",
            "cognition_type": "recollection",
            "belief_value": None,
            "contradiction_flag": False,
            "id": "node9",
            "session_id": "session1"
        },
        "to_node": {
            "text": "I've been feeling anxious about my upcoming presentation at work.",
            "emotion": "anxiety",
            "theme": "work and presentations",
            "cognition_type": "observation",
            "belief_value": None,
            "contradiction_flag": False,
            "id": "node10",
            "session_id": "session1"
        }
    }
]

def test_edge_types():
    """Test creation of different edge types."""
    logger.info("=== Testing Edge Types Diversity ===\n")
    
    results = []
    
    for i, pair in enumerate(TEST_PAIRS):
        logger.info(f"\nTesting pair {i+1}:")
        logger.info(f"FROM: {pair['from_node']['text']}")
        logger.info(f"TO: {pair['to_node']['text']}")
        
        try:
            edge_data = create_edges_between_nodes(pair["from_node"], pair["to_node"])
            edge_type = edge_data.get("edge_type")
            match_strength = edge_data.get("match_strength")
            explanation = edge_data.get("explanation")
            
            logger.info(f"Edge Type: {edge_type}")
            logger.info(f"Match Strength: {match_strength}")
            logger.info(f"Explanation: {explanation[:100]}...")
            
            results.append({
                "pair": i+1,
                "edge_type": edge_type,
                "match_strength": match_strength,
                "explanation_snippet": explanation[:100] if explanation else None
            })
        except Exception as e:
            logger.error(f"Error processing pair {i+1}: {e}")
    
    # Analyze results
    edge_types = {}
    for result in results:
        edge_type = result.get("edge_type")
        if edge_type in edge_types:
            edge_types[edge_type] += 1
        else:
            edge_types[edge_type] = 1
    
    logger.info("\n=== Edge Type Distribution ===")
    for edge_type, count in edge_types.items():
        logger.info(f"{edge_type}: {count} ({(count/len(results))*100:.1f}%)")
    
    logger.info("\n=== Test Complete ===")
    return results

if __name__ == "__main__":
    test_edge_types()