"""
Test script for Phase 2 functionality of the Smriti API.

This script tests the end-to-end flow of Phase 2 with extended timeout:
1. Create a user (or use existing)
2. Create a session with transcript
3. Process the session to extract nodes
4. Verify that nodes were created
"""
import json
import requests
import uuid
import time
from typing import Dict, Any, Optional, List

# Base URL for API
BASE_URL = "http://localhost:5000/api/v1"
# Set a longer timeout (120 seconds) for the API calls
TIMEOUT = 120

def test_phase2():
    """Test Phase 2 functionality."""
    print("=== Testing Phase 2 Functionality ===\n")
    
    # 1. Create or get an existing user
    print("1. Creating a user...")
    response = requests.post(
        f"{BASE_URL}/users/",
        json={"email": "phase2@example.com"},
        timeout=TIMEOUT
    )
    
    if response.status_code == 201:
        user = response.json()
        user_id = user["id"]
        print(f"User created with ID: {user_id}")
    elif response.status_code == 400 and ("already exists" in response.text or "already registered" in response.text):
        # User already exists, get user by email
        response = requests.get(f"{BASE_URL}/users/", timeout=TIMEOUT)
        if response.status_code == 200:
            users = response.json()
            user = next((u for u in users if u["email"] == "phase2@example.com"), None)
            if user:
                user_id = user["id"]
                print(f"Using existing user with ID: {user_id}")
            else:
                print(f"Could not find existing user.")
                return
        else:
            print(f"Failed to get users: {response.status_code} {response.text}")
            return
    else:
        print(f"Failed to create user: {response.status_code} {response.text}")
        return
    
    # 2. Create a session with transcript
    print("\n2. Creating a session with transcript...")
    transcript = """
    Today was a mix of emotions. I felt proud when my presentation at work was well-received, 
    but later I became anxious about the upcoming deadline for the next project. 
    This deadline reminds me of a time I missed an important submission and disappointed my team.
    I keep thinking that I'm not organized enough, though my manager has told me my work is solid. 
    Maybe I'm too hard on myself? But then again, I should be more disciplined with my time.
    The weekend trip I'm planning gives me something positive to look forward to.
    """
    
    # Create the session
    response = requests.post(
        f"{BASE_URL}/sessions/",
        json={"user_id": user_id, "duration_seconds": 300},
        timeout=TIMEOUT
    )
    
    if response.status_code == 201:
        session = response.json()
        session_id = session["id"]
        print(f"Session created with ID: {session_id}")
    else:
        print(f"Failed to create session: {response.status_code} {response.text}")
        return
    
    # Update the session with transcript
    transcript_data = {"transcript": transcript}
    response = requests.put(
        f"{BASE_URL}/sessions/{session_id}/transcript",
        json=transcript_data,
        timeout=TIMEOUT
    )
    
    if response.status_code == 200:
        updated_session = response.json()
        print(f"Session updated with transcript. Length: {len(updated_session['raw_transcript'])}")
    else:
        print(f"Failed to update session transcript: {response.status_code} {response.text}")
        return
    
    # 3. Process the session to extract nodes
    print("\n3. Processing session to extract nodes...")
    print("   This may take up to 2 minutes as it calls OpenAI...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=TIMEOUT
        )
        
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
            return
    except requests.exceptions.Timeout:
        print("Request timed out. The operation may still be processing on the server.")
        print("Waiting for 30 seconds before checking if nodes were created...")
        time.sleep(30)
    
    # 4. Verify that nodes were created by getting them directly
    print("\n4. Verifying nodes were created in the database...")
    try:
        response = requests.get(
            f"{BASE_URL}/nodes/session/{session_id}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            db_nodes = response.json()
            print(f"Retrieved {len(db_nodes)} nodes from the database.")
            
            # If we got nodes through processing earlier, verify these are the same nodes
            if 'nodes' in locals():
                if len(db_nodes) == len(nodes):
                    print("Verified: Node count matches.")
                else:
                    print(f"Warning: Node count mismatch. API returned {len(nodes)}, database has {len(db_nodes)}.")
            
            # If we didn't get nodes earlier (due to timeout), show them now
            if 'nodes' not in locals() and db_nodes:
                print(f"Found {len(db_nodes)} nodes in the database:")
                for i, node in enumerate(db_nodes, 1):
                    print(f"\nNode {i}:")
                    print(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
                    print(f"  Emotion: {node['emotion']}")
                    print(f"  Theme: {node['theme']}")
                    print(f"  Cognition Type: {node['cognition_type']}")
        else:
            print(f"Failed to get nodes: {response.status_code} {response.text}")
    except requests.exceptions.Timeout:
        print("Request to verify nodes timed out.")
    
    print("\n=== Phase 2 Test Complete ===")

if __name__ == "__main__":
    test_phase2()