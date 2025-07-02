#!/usr/bin/env python3
"""
Process all unprocessed sessions for a specific user and convert them to nodes.

This script retrieves all sessions for a given user ID, extracts nodes from 
the transcripts using OpenAI, and stores them in the database.
"""
import argparse
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from uuid import UUID

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def get_user_sessions(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get all sessions for a specific user.
    
    Args:
        user_id: The user ID to get sessions for.
        
    Returns:
        List of session objects or None if there was an error.
    """
    logger.info(f"Getting sessions for user: {user_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/sessions/user/{user_id}",
            timeout=10
        )
        response.raise_for_status()
        sessions = response.json()
        logger.info(f"Found {len(sessions)} sessions")
        return sessions
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        return None

def process_session_to_nodes(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Process a session transcript to extract nodes.
    
    Args:
        session_id: The ID of the session to process.
        
    Returns:
        List of node objects or None if there was an error.
    """
    logger.info(f"Processing session {session_id} to extract nodes...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=60  # Longer timeout for OpenAI processing
        )
        response.raise_for_status()
        
        nodes = response.json()
        logger.info(f"Successfully processed transcript. Extracted {len(nodes)} nodes.")
        
        # Print a summary of each node
        for i, node in enumerate(nodes, 1):
            logger.info(f"Node {i}:")
            logger.info(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
            logger.info(f"  Emotion: {node['emotion']}")
            logger.info(f"  Theme: {node['theme']}")
            logger.info(f"  Cognition Type: {node['cognition_type']}")
        
        return nodes
    except requests.exceptions.Timeout:
        logger.warning("Request timed out. The operation may still be processing on the server.")
        logger.info("Waiting for 30 seconds before checking if nodes were created...")
        import time
        time.sleep(30)
        
        # Check if nodes were created despite timeout
        response = requests.get(f"{BASE_URL}/nodes/session/{session_id}")
        if response.status_code == 200:
            nodes = response.json()
            logger.info(f"Found {len(nodes)} nodes after timeout.")
            return nodes
        logger.error("No nodes found after timeout.")
        return None
    except Exception as e:
        logger.error(f"Error processing session to nodes: {e}")
        return None

def verify_nodes_created(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Verify that nodes were created for a session by getting them directly.
    
    Args:
        session_id: The ID of the session to verify.
        
    Returns:
        List of node objects or None if there was an error or no nodes were found.
    """
    logger.info(f"Verifying nodes were created for session: {session_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/nodes/session/{session_id}",
            timeout=10
        )
        response.raise_for_status()
        nodes = response.json()
        logger.info(f"Found {len(nodes)} nodes in the database")
        return nodes
    except Exception as e:
        logger.error(f"Error verifying nodes: {e}")
        return None

def process_all_user_sessions(user_id: str):
    """
    Process all sessions for a user to create nodes.
    
    Args:
        user_id: The user ID to process sessions for.
    """
    # Get all sessions for the user
    sessions = get_user_sessions(user_id)
    if not sessions:
        logger.error("No sessions found for user. Exiting.")
        return
    
    # Process each session to extract nodes
    for session in sessions:
        session_id = session["id"]
        
        # Check if nodes already exist for this session
        existing_nodes = verify_nodes_created(session_id)
        if existing_nodes:
            logger.info(f"Session {session_id} already has {len(existing_nodes)} nodes. Skipping.")
            continue
        
        # Process the session transcript to extract nodes
        nodes = process_session_to_nodes(session_id)
        if not nodes:
            logger.warning(f"Failed to extract nodes for session {session_id}. Continuing with next session.")
            continue
        
        # Verify that nodes were created
        db_nodes = verify_nodes_created(session_id)
        if db_nodes:
            logger.info(f"Successfully verified {len(db_nodes)} nodes in the database for session {session_id}")
        else:
            logger.warning(f"Could not verify nodes in the database for session {session_id}")
    
    logger.info("Finished processing all sessions for user.")

def main():
    parser = argparse.ArgumentParser(description="Process sessions for a specific user to extract nodes.")
    parser.add_argument("user_id", help="The user ID to process sessions for")
    args = parser.parse_args()
    
    user_id = args.user_id
    
    logger.info(f"Starting node creation process for user: {user_id}")
    process_all_user_sessions(user_id)
    logger.info("Node creation process completed.")

if __name__ == "__main__":
    main()