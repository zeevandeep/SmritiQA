"""
Test script for node extraction functionality.
"""
import requests

# Session ID from previous test
SESSION_ID = "c2c5fc23-4752-41cf-bae8-75ae90128663"
BASE_URL = "http://localhost:5000/api/v1"

def test_nodes():
    """Test node extraction for an existing session."""
    print("=== Testing Node Extraction ===\n")
    
    # Process the session to extract nodes
    print("Processing session to extract nodes...")
    response = requests.post(f"{BASE_URL}/nodes/session/{SESSION_ID}/process")
    
    if response.status_code == 200:
        nodes = response.json()
        print(f"Successfully processed transcript. Extracted {len(nodes)} nodes:")
        
        # Print a summary of each node
        for i, node in enumerate(nodes, 1):
            print(f"\nNode {i}:")
            print(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
            print(f"  Emotion: {node['emotion']}")
            print(f"  Theme: {node['theme']}")
            print(f"  Cognition Type: {node['cognition_type']}")
    else:
        print(f"Failed to process transcript: {response.status_code} {response.text}")

if __name__ == "__main__":
    test_nodes()