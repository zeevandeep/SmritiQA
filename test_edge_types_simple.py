"""
Ultra-simplified test for edge type variety.

This completely bypasses database and API calls to test just the edge type logic.
"""
import os
import json
import logging
from typing import Dict, Any, List
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("Missing OpenAI API key. Make sure OPENAI_API_KEY is set.")
    exit(1)
    
class TestOpenAI:
    """Simple class to mimic the OpenAI utils functionality."""
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def create_edge_between_nodes(self, from_node, to_node):
        """
        Test just the edge creation logic directly with OpenAI, 
        bypassing the full application flow.
        """
        # Get node data
        from_emotion = from_node.get('emotion', 'Unknown')
        to_emotion = to_node.get('emotion', 'Unknown')
        from_family = self.get_emotional_family(from_emotion) or "Unknown"
        to_family = self.get_emotional_family(to_emotion) or "Unknown"
        
        # Determine if this is intra-session or cross-session
        same_session = from_node.get('session_id') == to_node.get('session_id')
        session_relation = 'intra_session' if same_session else 'cross_session'
        
        # Construct the prompt
        prompt = f"""
        Analyze the relationship between these two thoughts and identify the psychological connection:
        
        Thought 1: {from_node['text']}
        Emotion 1: {from_emotion}
        
        Thought 2: {to_node['text']}
        Emotion 2: {to_emotion}
        
        Determine:
        1. The type of connection (one of: thought_progression, emotion_shift, belief_mutation, contradiction_loop, mixed_transition, avoidance_drift, recurrence_theme, recurrence_emotion, recurrence_belief)
        2. Strength of the match (0.0 to 1.0)
        3. A brief explanation of the connection
        
        Format your response as a JSON object with edge_type, match_strength, and explanation fields.
        """
        
        # Enhance with emotional family context
        system_message = (
            "You are an expert in cognitive psychology and emotional analysis. "
            f"Note that '{from_emotion}' belongs to the '{from_family}' emotional family and "
            f"'{to_emotion}' belongs to the '{to_family}' emotional family. "
            "Consider these emotional families when determining the relationship between thoughts."
        )
        
        # Call OpenAI API directly
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
        )
        
        # Parse the response
        try:
            response_data = response.json()
            if "choices" in response_data and response_data["choices"]:
                result_text = response_data["choices"][0]["message"]["content"]
                result = json.loads(result_text)
                
                # Add session_relation
                result['session_relation'] = session_relation
                
                return result
            else:
                logger.error(f"Unexpected API response: {response_data}")
                return {
                    "edge_type": "thought_progression",
                    "match_strength": 0.5,
                    "explanation": "Failed to analyze the connection due to an API error.",
                    "session_relation": session_relation
                }
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {e}")
            return {
                "edge_type": "thought_progression",
                "match_strength": 0.5,
                "explanation": "Failed to analyze the connection due to an error.",
                "session_relation": session_relation
            }
    
    def get_emotional_family(self, emotion: str):
        """
        Get the emotional family for a given emotion based on predefined families.
        Simplified version that doesn't rely on the app code.
        """
        emotional_families = {
            "Fear": ["anxious", "anxiety", "terrified", "worried", "scared", "panic", "nervous", "afraid", "fearful", "dread", "insecurity"],
            "Anger": ["frustrated", "frustration", "irritated", "furious", "enraged", "resentful", "angry", "mad", "annoyed", "agitated", "envy"],
            "Sadness": ["disappointed", "disappointment", "depressed", "hopeless", "miserable", "guilty", "sad", "unhappy", "grief", "melancholy"],
            "Joy": ["happy", "happiness", "excited", "excitement", "content", "proud", "grateful", "joyful", "delighted", "cheerful"],
            "Calm": ["calm", "calmness", "serene", "tranquil", "peaceful", "relaxed", "composed", "collected", "at ease", "unruffled", "placid"],
            "Determination": ["determined", "determination", "resolute", "steadfast", "committed", "persistent", "tenacious", "dedicated", "focused"],
            "Trust": ["confident", "confidence", "assured", "secure", "faithful", "reliable", "trusting", "believing", "sure", "hopeful"]
        }
        
        if not emotion:
            return None
        
        # Normalize emotion (lowercase)
        normalized_emotion = emotion.lower()
        
        # Find the matching emotional family
        for family, emotions in emotional_families.items():
            if normalized_emotion in [e.lower() for e in emotions]:
                return family
        
        return None

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
            "emotion": "calm",
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
    
    # Initialize our test OpenAI client
    openai_client = TestOpenAI(OPENAI_API_KEY)
    
    results = []
    
    for i, pair in enumerate(TEST_PAIRS):
        logger.info(f"\nTesting pair {i+1}:")
        logger.info(f"FROM: {pair['from_node']['text']}")
        logger.info(f"TO: {pair['to_node']['text']}")
        
        try:
            edge_data = openai_client.create_edge_between_nodes(pair["from_node"], pair["to_node"])
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