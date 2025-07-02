"""
Comprehensive end-to-end test for the Smriti application.

This script tests the full flow from user creation to edge processing:
1. Create a user
2. Create a session
3. Add a transcript
4. Process the session to extract nodes
5. Generate embeddings for the nodes
6. Create edges between the nodes
7. Verify results

This script is useful for testing the entire application pipeline.
"""
import requests
import json
import time
import logging
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)

# Connect through the Flask proxy
BASE_URL = "http://0.0.0.0:5000/api/v1"

def create_user() -> Optional[Dict[str, Any]]:
    """Create a new user for testing."""
    try:
        response = requests.post(
            f"{BASE_URL}/users/",
            json={"email": "end_to_end@example.com"},
            timeout=10
        )
        
        if response.status_code == 201:
            user = response.json()
            logging.info(f"Created user with ID: {user['id']}")
            return user
        elif response.status_code == 400 and ("already exists" in response.text or "already registered" in response.text):
            logging.info("User already exists, fetching existing user")
            return get_existing_user("end_to_end@example.com")
        else:
            logging.error(f"Failed to create user: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def get_existing_user(email: str) -> Optional[Dict[str, Any]]:
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

def create_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Create a new session for the user."""
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/",
            json={"user_id": user_id, "duration_seconds": 300},
            timeout=10
        )
        
        if response.status_code == 201:
            session = response.json()
            logging.info(f"Created session with ID: {session['id']}")
            return session
        else:
            logging.error(f"Failed to create session: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error creating session: {e}")
        return None

def update_session_transcript(session_id: str, transcript: str) -> bool:
    """Update session with transcript."""
    try:
        response = requests.put(
            f"{BASE_URL}/sessions/{session_id}/transcript",
            json={"transcript": transcript},
            timeout=10
        )
        
        if response.status_code == 200:
            updated_session = response.json()
            transcript_length = len(updated_session.get("raw_transcript", ""))
            logging.info(f"Updated session with transcript of length: {transcript_length}")
            return True
        else:
            logging.error(f"Failed to update session transcript: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error updating session transcript: {e}")
        return False

def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Process session transcript to extract nodes."""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=60  # Longer timeout for OpenAI processing
        )
        
        if response.status_code == 200:
            nodes = response.json()
            logging.info(f"Processed transcript and extracted {len(nodes)} nodes")
            
            # Print summary of nodes
            for i, node in enumerate(nodes, 1):
                logging.info(f"Node {i}:")
                truncated_text = node['text'][:50] + "..." if len(node['text']) > 50 else node['text']
                logging.info(f"  Text: {truncated_text}")
                logging.info(f"  Emotion: {node['emotion']}")
                logging.info(f"  Theme: {node['theme']}")
                logging.info(f"  Cognition Type: {node['cognition_type']}")
            
            return nodes
        else:
            logging.error(f"Failed to process transcript: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error processing transcript: {e}")
        return None

def process_node_embeddings(batch_size: int = 50) -> Optional[Dict[str, Any]]:
    """Process a batch of nodes to generate embeddings."""
    try:
        # First check if the endpoint exists
        # Try to get API schema
        logging.info("Getting API schema to check for node embedding endpoint...")
        schema_response = requests.get("http://0.0.0.0:5000/openapi.json", timeout=10)
        endpoints = []
        if schema_response.status_code == 200:
            schema = schema_response.json()
            for path in schema.get("paths", {}).keys():
                if "nodes" in path and "embedding" in path:
                    endpoints.append(path)
            logging.info(f"Found embedding endpoints: {endpoints}")
        
        # Try a few possible endpoint patterns
        endpoint_patterns = [
            "/nodes/embeddings/batch",
            "/nodes/batch/embeddings",
            "/nodes/embeddings/process",
            "/nodes/process/embeddings"
        ]
        
        for pattern in endpoint_patterns:
            try:
                logging.info(f"Trying endpoint pattern: {pattern}")
                response = requests.post(
                    f"{BASE_URL}{pattern}",
                    json={"batch_size": batch_size},
                    timeout=60  # Longer timeout for OpenAI embeddings
                )
                
                if response.status_code != 404:
                    logging.info(f"Found working endpoint: {pattern}")
                    if response.status_code == 200:
                        stats = response.json()
                        logging.info(f"Processed {stats.get('nodes_processed', 0)} node embeddings")
                        return stats
                    else:
                        logging.error(f"Failed to process embeddings: {response.status_code} {response.text}")
                        return None
            except Exception as e:
                logging.error(f"Error with endpoint {pattern}: {e}")
                continue
        
        logging.error("Could not find a working node embedding endpoint")
        return None
    except Exception as e:
        logging.error(f"Error processing embeddings: {e}")
        return None

def process_edges(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process edges for a user."""
    try:
        response = requests.post(
            f"{BASE_URL}/edges/process/{user_id}",
            json={"batch_size": batch_size},
            timeout=60  # Longer timeout for edge processing
        )
        
        if response.status_code == 200:
            stats = response.json()
            logging.info(f"Processed edges: {stats}")
            return stats
        else:
            logging.error(f"Failed to process edges: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error processing edges: {e}")
        return None

def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user."""
    try:
        response = requests.get(
            f"{BASE_URL}/edges/user/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            edges = response.json()
            edge_count = len(edges)
            logging.info(f"Found {edge_count} edges for user {user_id}")
            
            # Analyze edge types
            edge_types = {}
            for edge in edges:
                edge_type = edge.get("edge_type", "unknown")
                if edge_type not in edge_types:
                    edge_types[edge_type] = 0
                edge_types[edge_type] += 1
            
            if edge_types:
                logging.info("Edge type distribution:")
                for edge_type, count in edge_types.items():
                    logging.info(f"  {edge_type}: {count}")
            
            return edges
        else:
            logging.error(f"Failed to get edges: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting edges: {e}")
        return None

def get_node_details(node_id: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific node."""
    try:
        response = requests.get(
            f"{BASE_URL}/nodes/{node_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            node = response.json()
            logging.info(f"Retrieved node with ID: {node_id}")
            return node
        else:
            logging.error(f"Failed to get node: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error getting node: {e}")
        return None

def run_end_to_end_test():
    """Run the end-to-end test."""
    logging.info("=== Starting End-to-End Test ===")
    
    # 1. Create a user
    user = create_user()
    if not user:
        logging.error("Failed to create user, exiting test")
        return
    
    user_id = user["id"]
    
    # 2. Create a session
    session = create_session(user_id)
    if not session:
        logging.error("Failed to create session, exiting test")
        return
    
    session_id = session["id"]
    
    # 3. Define a transcript with emotional and cognitive diversity
    transcript = """
    Today I experienced several different emotions.
    
    First, I felt anxious about my upcoming presentation at work. I worry that I won't be prepared enough.
    But then I reminded myself that I've been practicing and know the material well, which made me feel more confident.
    
    I had lunch with Sarah, and when she told me about her promotion, I felt genuinely happy for her, but also a bit envious.
    I wonder why I haven't been promoted yet despite working so hard. Maybe I need to be more assertive about my accomplishments.
    
    Later, my boss criticized my report in front of the team, and I felt embarrassed and angry. I think the criticism was unfair
    because I had followed all the guidelines. I'm not sure if I should bring it up with him or just let it go.
    
    On my way home, I saw a homeless person and felt sad about how many people struggle with basic needs. It made me grateful
    for what I have, but also guilty that I don't do more to help others.
    
    Tonight, I'm feeling hopeful about the weekend plans with friends. It's been a while since we've all gotten together,
    and I'm looking forward to relaxing and having fun.
    """
    
    # 4. Update the session with transcript
    if not update_session_transcript(session_id, transcript):
        logging.error("Failed to update session transcript, exiting test")
        return
    
    # 5. Process session to extract nodes
    nodes = process_session_to_nodes(session_id)
    if not nodes:
        logging.error("Failed to process nodes, exiting test")
        return
    
    # 6. Process node embeddings
    embedding_stats = process_node_embeddings(batch_size=10)
    if not embedding_stats:
        logging.error("Failed to process embeddings, exiting test")
        return
    
    # Wait a moment to ensure embeddings are processed
    logging.info("Waiting 5 seconds for embeddings to be processed...")
    time.sleep(5)
    
    # 7. Process edges
    edge_stats = process_edges(user_id, batch_size=5)
    if not edge_stats:
        logging.error("Failed to process edges, exiting test")
        return
    
    # 8. Get user edges
    edges = get_user_edges(user_id)
    if not edges:
        logging.info("No edges found, but test will continue")
    
    # 9. Check a few node details
    if nodes and len(nodes) > 0:
        first_node_id = nodes[0]["id"]
        node_details = get_node_details(first_node_id)
        if node_details:
            logging.info(f"Verified node details for node {first_node_id}")
    
    logging.info("=== End-to-End Test Complete ===")

if __name__ == "__main__":
    run_end_to_end_test()