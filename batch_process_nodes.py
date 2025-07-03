"""
Batch process all unprocessed sessions and convert them to nodes.

This script directly uses SQLAlchemy to access the database and
calls the OpenAI API to process unprocessed sessions.
"""
import logging
import time
import sys
import os
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session as SQLAlchemySession
import requests

# Import the node extraction function
from app.utils.openai_utils import extract_nodes_from_transcript

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def get_unprocessed_sessions() -> List[Dict[str, Any]]:
    """Get all sessions that haven't been processed yet."""
    try:
        with SQLAlchemySession(engine) as db:
            # Query for sessions where is_processed is false
            result = db.execute(
                text("SELECT id, user_id, raw_transcript FROM sessions WHERE is_processed = false")
            )
            sessions = [
                {"id": row[0], "user_id": row[1], "raw_transcript": row[2]} 
                for row in result.fetchall()
            ]
            logger.info(f"Found {len(sessions)} unprocessed sessions")
            return sessions
    except Exception as e:
        logger.error(f"Error getting unprocessed sessions: {e}", exc_info=True)
        return []

def create_node(db, node_data: Dict[str, Any], session_id: str, user_id: str) -> str:
    """Insert a node into the database."""
    try:
        # Insert the node
        query = text("""
            INSERT INTO nodes (id, user_id, session_id, text, theme, emotion, cognition_type, created_at, is_processed)
            VALUES (gen_random_uuid(), :user_id, :session_id, :text, :theme, :emotion, :cognition_type, NOW(), false)
            RETURNING id
        """)
        
        result = db.execute(
            query,
            {
                "user_id": user_id,
                "session_id": session_id,
                "text": node_data.get("text", ""),
                "theme": node_data.get("theme", "generic"),
                "emotion": node_data.get("emotion", "generic"),
                "cognition_type": node_data.get("cognition_type", "generic")
            }
        )
        
        node_id = result.scalar()
        db.commit()
        return node_id
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating node: {e}", exc_info=True)
        return None

def process_session(session: Dict[str, Any]) -> bool:
    """
    Process a single session to extract nodes and save them to the database.
    
    Args:
        session: A dictionary containing session data (id, user_id, raw_transcript)
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    session_id = session.get('id')
    user_id = session.get('user_id')
    transcript = session.get('raw_transcript', '')
    
    if not session_id or not user_id or not transcript:
        logger.warning(f"Missing required data for session: {session_id}")
        return False
    
    try:
        logger.info(f"Processing session: {session_id}")
        
        # Extract nodes from transcript using OpenAI
        nodes = extract_nodes_from_transcript(transcript)
        
        if not nodes:
            logger.warning(f"No nodes extracted from session {session_id}")
            return False
        
        # Save nodes to database
        with SQLAlchemySession(engine) as db:
            # Create each node
            node_ids = []
            for node_data in nodes:
                node_id = create_node(db, node_data, session_id, user_id)
                if node_id:
                    node_ids.append(node_id)
            
            # Mark session as processed
            if node_ids:
                db.execute(
                    text("UPDATE sessions SET is_processed = true WHERE id = :session_id"),
                    {"session_id": session_id}
                )
                db.commit()
                logger.info(f"Successfully processed session {session_id}, created {len(node_ids)} nodes")
                return True
            else:
                logger.warning(f"Failed to create any nodes for session {session_id}")
                return False
                
    except Exception as e:
        logger.error(f"Error processing session {session_id}: {e}", exc_info=True)
        return False

def batch_process_all_sessions():
    """Process all unprocessed sessions in a batch."""
    sessions = get_unprocessed_sessions()
    
    if not sessions:
        logger.info("No unprocessed sessions found")
        return
    
    success_count = 0
    failure_count = 0
    
    for session in sessions:
        success = process_session(session)
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Add a small delay between requests to avoid overwhelming the OpenAI API
        time.sleep(0.5)
    
    logger.info(f"Batch processing complete. Success: {success_count}, Failures: {failure_count}")
    return {
        "total": len(sessions),
        "success": success_count,
        "failure": failure_count
    }

if __name__ == "__main__":
    logger.info("Starting batch processing of unprocessed sessions...")
    results = batch_process_all_sessions()
    logger.info("Batch processing completed")
    sys.exit(0)