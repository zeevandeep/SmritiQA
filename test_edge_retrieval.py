"""
Test script specifically for testing edge retrieval.
"""
import requests
import uuid
import json
from typing import Optional, Dict, Any, List

# API URLs
BASE_URL = "http://localhost:5000/api/v1"
USERS_URL = f"{BASE_URL}/users"
EDGES_URL = f"{BASE_URL}/edges"

# Timeout for API requests (seconds)
TIMEOUT = 120

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user."""
    try:
        email = f"test_user_{uuid.uuid4()}@example.com"
        print(f"Creating user with email: {email}")
        
        response = requests.post(
            f"{USERS_URL}/",
            json={"email": email},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        user = response.json()
        print(f"Created user with ID: {user['id']}")
        return user
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def create_test_edge(
    from_node_id: str, 
    to_node_id: str, 
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Create a test edge manually."""
    try:
        print(f"Creating edge between nodes {from_node_id} and {to_node_id}")
        
        edge_data = {
            "from_node": from_node_id,
            "to_node": to_node_id,
            "user_id": user_id,
            "edge_type": "test_edge",
            "match_strength": 0.8,
            "session_relation": "same",
            "explanation": "Test edge created for testing"
        }
        
        response = requests.post(
            f"{EDGES_URL}/",
            json=edge_data,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        edge = response.json()
        print(f"Created edge with ID: {edge['id']}")
        return edge
    except Exception as e:
        print(f"Error creating edge: {e}")
        return None

def get_existing_users() -> Optional[List[Dict[str, Any]]]:
    """Get list of existing users."""
    try:
        response = requests.get(
            f"{USERS_URL}/",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        users = response.json()
        print(f"Found {len(users)} users")
        return users
    except Exception as e:
        print(f"Error getting users: {e}")
        return None

def get_user_edges_query_param(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user using query parameter."""
    try:
        print(f"Getting edges for user {user_id} with query parameter")
        url = f"{EDGES_URL}/?user_id={user_id}"
        print(f"URL: {url}")
        
        response = requests.get(
            url,
            timeout=TIMEOUT
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        response.raise_for_status()
        edges = response.json()
        print(f"Found {len(edges)} edges")
        return edges
    except Exception as e:
        print(f"Error getting edges: {e}")
        return None

def get_user_edges_direct_url(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get edges for a user using explicit URL path."""
    try:
        print(f"Getting edges for user {user_id} with direct URL")
        url = f"{EDGES_URL}/user/{user_id}"
        print(f"URL: {url}")
        
        response = requests.get(
            url,
            timeout=TIMEOUT
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 404:
            print("Endpoint not found. This is expected if the route doesn't exist.")
            return None
            
        response.raise_for_status()
        edges = response.json()
        print(f"Found {len(edges)} edges")
        return edges
    except Exception as e:
        print(f"Error getting edges: {e}")
        return None

def test_edge_retrieval():
    """Test edge retrieval."""
    print("=== Testing Edge Retrieval API ===")
    
    # Get an existing user or create a new one
    users = get_existing_users()
    if users and len(users) > 0:
        user = users[0]
        print(f"Using existing user: {user['id']}")
    else:
        user = create_test_user()
        if not user:
            print("Failed to create or get a user")
            return
    
    # Try different ways of retrieving edges
    print("\nTesting edge retrieval with query parameter:")
    edges1 = get_user_edges_query_param(user['id'])
    
    print("\nTesting edge retrieval with direct URL:")
    edges2 = get_user_edges_direct_url(user['id'])
    
    print("\n=== Edge Retrieval Test Complete ===")

if __name__ == "__main__":
    test_edge_retrieval()