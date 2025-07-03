"""
Service for processing session transcripts and extracting cognitive/emotional nodes.
"""
import json
import logging
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.repositories import node_repository, session_repository
from app.schemas.schemas import NodeCreate
from app.utils.openai_utils import extract_nodes_from_transcript

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_transcript(db: DbSession, session_id: UUID) -> bool:
    """
    Process a session transcript to extract nodes.
    
    This function:
    1. Retrieves the session
    2. Extracts nodes from the transcript using OpenAI
    3. Creates node entries in the database
    4. Marks the session as processed
    
    Args:
        db: Database session.
        session_id: ID of the session to process.
        
    Returns:
        Boolean indicating success (True) or failure (False).
    """
    logger.info(f"Starting to process transcript for session: {session_id}")
    
    # Get the session
    db_session = session_repository.get_session(db, session_id)
    if db_session is None or not db_session.raw_transcript:
        # Session not found or no transcript
        logger.error(f"Session not found or no transcript for session: {session_id}")
        return False
    
    logger.info(f"Retrieved session with transcript length: {len(db_session.raw_transcript)}")
    
    # Extract nodes from the transcript
    logger.info("Calling OpenAI API to extract nodes...")
    extracted_nodes = extract_nodes_from_transcript(db_session.raw_transcript)
    if not extracted_nodes:
        # No nodes extracted
        logger.error("No nodes extracted from transcript")
        return False
    
    # Log the type of extracted_nodes for debugging
    logger.info(f"Extracted nodes type: {type(extracted_nodes)}")
    logger.info(f"Extracted nodes content: {extracted_nodes}")
    
    # Handle different possible response formats
    if isinstance(extracted_nodes, str):
        # If we got a string, try to parse it as JSON
        try:
            logger.info("Attempting to parse string response as JSON")
            extracted_nodes = json.loads(extracted_nodes)
        except json.JSONDecodeError:
            logger.error("Failed to parse extracted_nodes as JSON")
            return False
    
    # If we got a list directly, use it, otherwise check for nodes key
    if isinstance(extracted_nodes, dict) and "nodes" in extracted_nodes:
        node_list = extracted_nodes["nodes"]
        logger.info(f"Using 'nodes' key from response, found {len(node_list)} nodes")
    elif isinstance(extracted_nodes, list):
        node_list = extracted_nodes
        logger.info(f"Using direct list from response, found {len(node_list)} nodes")
    else:
        logger.error(f"Unexpected format for extracted_nodes: {type(extracted_nodes)}")
        return False
    
    # Convert extracted nodes to NodeCreate objects
    node_creates = []
    for i, node_data in enumerate(node_list):
        # Ensure node_data is a dictionary
        if not isinstance(node_data, dict):
            logger.warning(f"Skipping non-dict node data at index {i}: {node_data}")
            continue
            
        logger.info(f"Creating node {i+1} with text: {node_data.get('text', '')[:50]}...")
        node_create = NodeCreate(
            user_id=db_session.user_id,
            session_id=session_id,
            text=node_data.get("text", ""),
            emotion=node_data.get("emotion"),
            theme=node_data.get("theme"),
            cognition_type=node_data.get("cognition_type"),
            belief_value=node_data.get("belief_value"),
            contradiction_flag=node_data.get("contradiction_flag", False)
        )
        node_creates.append(node_create)
    
    # Create nodes in the database
    logger.info(f"Creating {len(node_creates)} nodes in the database")
    created_nodes = node_repository.create_nodes_batch(db, node_creates)
    
    # Mark the session as processed
    logger.info(f"Marking session {session_id} as processed")
    session_repository.mark_session_processed(db, session_id)
    
    logger.info(f"Process completed successfully, created {len(created_nodes)} nodes")
    return bool(created_nodes)