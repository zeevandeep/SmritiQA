"""
Simple test script to test the node extraction function directly.
"""
import json
import logging
from app.utils.openai_utils import extract_nodes_from_transcript
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test transcript
TEST_TRANSCRIPT = """
Today was a rollercoaster. I started the day feeling confident about my career path, 
but by lunch I was questioning if this is really what I want to do with my life.
When I think about my family, I feel guilty that I don't call my parents enough.
My relationship with my partner is going well, but sometimes I feel like I'm not 
good enough for them. I worry they'll eventually see my flaws and leave.
Money has been tight lately, and I'm anxious about my financial future.
I've been thinking about my values and what truly matters to me.
Sometimes I wonder if I'm making any real difference in the world.
"""

def test_extract_nodes(transcript=None):
    """Test the node extraction function directly."""
    if transcript is None:
        transcript = TEST_TRANSCRIPT
        
    print("=== Testing Node Extraction ===\n")
    
    # Extract nodes from the test transcript
    print("Extracting nodes from test transcript...")
    nodes = extract_nodes_from_transcript(transcript)
    
    print(f"\nExtracted {len(nodes)} nodes:")
    print(json.dumps(nodes, indent=2))
    
    # Print a summary of each node
    print("\nNode Summary:")
    for i, node in enumerate(nodes, 1):
        print(f"\nNode {i}:")
        print(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
        print(f"  Emotion: {node['emotion']}")
        print(f"  Theme: {node['theme']}")
        print(f"  Cognition Type: {node['cognition_type']}")
    
    return nodes

if __name__ == "__main__":
    test_extract_nodes()