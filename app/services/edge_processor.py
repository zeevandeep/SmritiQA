"""
Edge processor for creating connections between cognitive/emotional nodes.

This module handles the batch processing of edges using embeddings and emotional context.
"""
import logging
import time
import datetime
from typing import List, Dict, Any, Tuple, Optional, Set
from uuid import UUID
import heapq

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.models import Node, Edge
from app.repositories import node_repository, edge_repository
from app.schemas.schemas import EdgeCreate
from app.utils.openai_utils import (
    deserialize_embedding,
    create_edges_between_nodes,
    calculate_cosine_similarity,
    calculate_adjusted_similarity,
    INITIAL_SIMILARITY_THRESHOLD,
    FINAL_SIMILARITY_THRESHOLD,
    MAX_SESSIONS_TO_CONSIDER,
    MAX_DAYS_TO_CONSIDER,
    MAX_CANDIDATE_NODES,
    MAX_EDGES_PER_NODE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_nodes_with_embeddings(db: DbSession, user_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get a batch of nodes with embeddings for a specific user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        limit: Maximum number of nodes to fetch.
        
    Returns:
        List of node dictionaries with deserialized embeddings.
    """
    logger.info(f"Fetching up to {limit} nodes with embeddings for user {user_id}")
    
    # Get nodes with embeddings
    db_nodes = db.query(Node).filter(
        Node.user_id == user_id,
        Node.embedding.is_not(None)
    ).order_by(Node.created_at.desc()).limit(limit).all()
    
    logger.info(f"Found {len(db_nodes)} nodes with embeddings")
    
    # Convert to dictionaries and deserialize embeddings
    nodes = []
    for node in db_nodes:
        node_dict = {
            "id": node.id,
            "user_id": node.user_id,
            "session_id": node.session_id,
            "text": node.text,
            "emotion": node.emotion,
            "theme": node.theme,
            "cognition_type": node.cognition_type,
            "belief_value": node.belief_value,
            "contradiction_flag": node.contradiction_flag,
            "embedding": deserialize_embedding(node.embedding),
            "created_at": node.created_at
        }
        nodes.append(node_dict)
    
    return nodes


def get_unprocessed_nodes(db: DbSession, user_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get a batch of nodes that haven't been processed for edge creation.
    
    A node is considered unprocessed if it has an embedding but doesn't have
    the maximum number of edges.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        limit: Maximum number of nodes to fetch.
        
    Returns:
        List of node dictionaries.
    """
    logger.info(f"Fetching up to {limit} unprocessed nodes for user {user_id}")
    
    # Get nodes with embeddings that haven't been processed yet
    # Sort by created_at in ascending order to process oldest nodes first
    db_nodes = db.query(Node).filter(
        Node.user_id == user_id,
        Node.embedding.is_not(None),
        Node.is_processed == False
    ).order_by(Node.created_at.asc()).limit(limit).all()
    
    if not db_nodes:
        logger.info("No unprocessed nodes with embeddings found")
        return []
    
    # Convert to dictionaries and deserialize embeddings
    nodes = []
    for node in db_nodes:
        # Check if this node already has the maximum number of edges
        edge_count = len(edge_repository.get_node_edges(db, node.id))
        if edge_count >= MAX_EDGES_PER_NODE:
            logger.info(f"[EDGE_TRACE] Node {node.id} already has {edge_count} edges (max: {MAX_EDGES_PER_NODE}) - marking as processed")
            # Mark node as processed since it has reached its maximum edges
            node_repository.mark_node_processed(db, node.id)
            continue
        
        node_dict = {
            "id": node.id,
            "user_id": node.user_id,
            "session_id": node.session_id,
            "text": node.text,
            "emotion": node.emotion,
            "theme": node.theme,
            "cognition_type": node.cognition_type,
            "embedding": deserialize_embedding(node.embedding),
            "created_at": node.created_at,
            "edge_count": edge_count
        }
        nodes.append(node_dict)
    
    logger.info(f"Found {len(nodes)} unprocessed nodes")
    return nodes


def find_candidate_nodes(
    db: DbSession,
    current_node: Dict[str, Any],
    max_candidates: int = MAX_CANDIDATE_NODES
) -> List[Dict[str, Any]]:
    """
    Find and rank candidate nodes for edge creation based on the refined algorithm.
    
    Args:
        db: Database session.
        current_node: The current node being processed.
        max_candidates: Maximum number of candidate nodes to return.
        
    Returns:
        List of candidate node dictionaries, ranked by adjusted similarity score.
    """
    user_id = current_node["user_id"]
    node_id = current_node["id"]
    
    logger.info(f"Finding candidate nodes for node {node_id}")
    
    # Calculate date cutoff (45 days from current node creation)
    current_timestamp = current_node.get("created_at")
    if not current_timestamp:
        logger.warning(f"Node {node_id} has no timestamp")
        return []
    
    date_cutoff = current_timestamp - datetime.timedelta(days=MAX_DAYS_TO_CONSIDER)
    
    # Get nodes from the most recent sessions (up to 25 sessions, within 45 days)
    # This query gets nodes that:
    # 1. Belong to the same user
    # 2. Have embeddings
    # 3. Were created after the cutoff date
    # 4. Are not the current node itself
    # 5. Are from the 25 most recent sessions
    
    logger.info(f"Fetching candidate nodes from sessions after {date_cutoff}")
    
    # First, get the most recent sessions
    # For DISTINCT with ORDER BY, we need to make sure the ORDER BY columns are in the SELECT clause
    recent_sessions = db.query(Node.session_id, Node.created_at).filter(
        Node.user_id == user_id,
        Node.created_at > date_cutoff
    ).distinct(Node.session_id).order_by(Node.session_id, Node.created_at.desc()).limit(MAX_SESSIONS_TO_CONSIDER).all()
    
    session_ids = [session.session_id for session in recent_sessions]
    
    if not session_ids:
        logger.warning(f"No recent sessions found for user {user_id}")
        return []
    
    logger.info(f"Found {len(session_ids)} recent sessions")
    
    # Now, get nodes from these sessions
    # Only get nodes that:
    # 1. Are processed (have already been evaluated for their own edges)
    # 2. Were created before the current node (ensure temporal direction)
    db_nodes = db.query(Node).filter(
        Node.user_id == user_id,
        Node.embedding.is_not(None),
        Node.id != node_id,
        Node.session_id.in_(session_ids),
        Node.is_processed == True,
        Node.created_at < current_timestamp
    ).order_by(Node.created_at.desc()).all()
    
    if not db_nodes:
        logger.info(f"No candidate nodes found for node {node_id}")
        return []
    
    logger.info(f"Found {len(db_nodes)} potential candidate nodes")
    
    # Convert to dictionaries and deserialize embeddings
    candidate_nodes = []
    for node in db_nodes:
        candidate_node = {
            "id": node.id,
            "user_id": node.user_id,
            "session_id": node.session_id,
            "text": node.text,
            "emotion": node.emotion,
            "theme": node.theme,
            "cognition_type": node.cognition_type,
            "embedding": deserialize_embedding(node.embedding),
            "created_at": node.created_at
        }
        candidate_nodes.append(candidate_node)
    
    # Calculate base and adjusted similarity scores for candidates
    qualified_candidates = []
    for candidate in candidate_nodes:
        # Calculate base cosine similarity
        base_similarity = calculate_cosine_similarity(current_node["embedding"], candidate["embedding"])
        
        # Skip nodes below initial threshold
        if base_similarity < INITIAL_SIMILARITY_THRESHOLD:
            continue
        
        # Calculate adjusted similarity score with boosts and penalties
        adjusted_similarity = calculate_adjusted_similarity(base_similarity, current_node, candidate)
        
        # Skip nodes below final threshold after adjustments
        if adjusted_similarity < FINAL_SIMILARITY_THRESHOLD:
            continue
        
        # Store both scores for sorting and reference
        candidate["base_similarity"] = base_similarity
        candidate["adjusted_similarity"] = adjusted_similarity
        qualified_candidates.append(candidate)
    
    logger.info(f"Found {len(qualified_candidates)} qualified candidates (above thresholds)")
    
    # Sort by adjusted similarity (highest first), with base similarity as tiebreaker
    qualified_candidates.sort(
        key=lambda x: (x["adjusted_similarity"], x["base_similarity"]), 
        reverse=True
    )
    
    # Take top N candidates
    top_candidates = qualified_candidates[:max_candidates]
    
    logger.info(f"Selected top {len(top_candidates)} candidates for edge creation")
    
    return top_candidates


def create_edges_batch(
    db: DbSession,
    current_node: Dict[str, Any],
    candidate_nodes: List[Dict[str, Any]]
) -> List[Edge]:
    """
    Create edges between the current node and multiple candidate nodes.
    
    Args:
        db: Database session.
        current_node: The current node being processed.
        candidate_nodes: List of candidate nodes to create edges with.
        
    Returns:
        List of created Edge objects.
    """
    if not candidate_nodes:
        logger.info(f"No candidate nodes provided for edge creation with node {current_node['id']}")
        return []
    
    logger.info(f"Creating edges for node {current_node['id']} with {len(candidate_nodes)} candidates")
    
    # Use OpenAI to analyze relationships and determine edge types
    try:
        edge_data_list = create_edges_between_nodes(current_node, candidate_nodes)
        logger.info(f"OpenAI returned {len(edge_data_list)} potential edges")
    except Exception as e:
        logger.error(f"Error getting edge data from OpenAI: {e}", exc_info=True)
        # Return None specifically to indicate API failure (not just empty results)
        return None
    
    # Create edges in the database
    created_edges = []
    for edge_data in edge_data_list:
        # Extract from_node_id and to_node_id
        from_node_id = edge_data.get("from_node_id")
        to_node_id = current_node["id"]  # The current node is always the target
        
        if not from_node_id:
            logger.warning("Missing from_node_id in edge data")
            continue
            
        # Validate the from_node_id is a valid UUID
        try:
            # Check if the UUID is properly formatted
            if len(from_node_id) != 36 or from_node_id.count("-") != 4:
                logger.warning(f"Invalid UUID format for from_node_id: {from_node_id}")
                continue
                
            # Try to parse it as a UUID
            uuid_obj = UUID(from_node_id)
            # Ensure the string representation matches the original
            if str(uuid_obj) != from_node_id:
                logger.warning(f"UUID formatting mismatch: {from_node_id} vs {uuid_obj}")
                continue
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid UUID for from_node_id: {from_node_id}, Error: {e}")
            continue
        
        # Check if edge already exists
        if edge_repository.check_edge_exists(db, from_node_id, to_node_id):
            logger.info(f"Edge already exists between {from_node_id} and {to_node_id}")
            continue
        
        # Get the edge type, handling different field names
        edge_type = edge_data.get("edge_type")
        if not edge_type:
            edge_type = edge_data.get("type") or edge_data.get("connection_type") or "thought_progression"
            
        # Get match_strength, ensuring it's a valid float
        match_strength = edge_data.get("match_strength")
        if match_strength is not None:
            try:
                match_strength = float(match_strength)
            except (ValueError, TypeError):
                match_strength = 0.7
        else:
            match_strength = 0.7
            
        # Ensure we only create edges with match_strength >= 0.7
        if match_strength < 0.7:
            logger.info(f"Skipping edge with match_strength {match_strength} < 0.7")
            continue
            
        # Get explanation, ensuring it's a string
        explanation = edge_data.get("explanation", "")
        if explanation is None:
            explanation = ""
            
        # Create EdgeCreate object
        edge_create = EdgeCreate(
            from_node=from_node_id,
            to_node=to_node_id,
            user_id=current_node["user_id"],
            edge_type=edge_type,
            match_strength=match_strength,
            session_relation=edge_data.get("session_relation", "cross_session"),
            explanation=explanation
        )
        
        # Create in database
        try:
            db_edge = edge_repository.create_edge(db, edge_create)
            logger.info(f"Created edge {db_edge.id} of type {db_edge.edge_type}")
            created_edges.append(db_edge)
        except Exception as e:
            logger.error(f"Error creating edge: {e}", exc_info=True)
    
    logger.info(f"Created {len(created_edges)} edges for node {current_node['id']}")
    return created_edges


def process_edges_batch(
    db: DbSession,
    user_id: UUID,
    batch_size: int = 5
) -> Dict[str, Any]:
    """
    Process a batch of nodes to create edges.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        batch_size: Number of source nodes to process.
        
    Returns:
        Dictionary with processing statistics.
    """
    start_time = time.time()
    logger.info(f"Starting batch edge processing for user {user_id}, batch size {batch_size}")
    
    # Get unprocessed nodes
    current_nodes = get_unprocessed_nodes(db, user_id, batch_size)
    
    if not current_nodes:
        logger.info("No unprocessed nodes found")
        return {
            "processed_nodes": 0,
            "created_edges": 0,
            "elapsed_time": 0,
            "message": "No unprocessed nodes found"
        }
    
    logger.info(f"Processing edges for {len(current_nodes)} nodes")
    
    # Track statistics
    processed_count = 0
    total_edges_created = 0
    
    # Process each node
    for current_node in current_nodes:
        logger.info(f"[EDGE_TRACE] Processing node {current_node['id']} (theme: {current_node.get('theme', 'unknown')})")
        node_id = current_node["id"]
        
        # Find candidate nodes using the refined algorithm
        candidates = find_candidate_nodes(db, current_node)
        
        if not candidates:
            logger.info(f"[EDGE_TRACE] No qualified candidates found for node {node_id} - marking as processed")
            # Only mark as processed if we have no candidates (not an API failure)
            node_repository.mark_node_processed(db, node_id)
            processed_count += 1
            continue
        
        # Create edges in batch using OpenAI analysis
        logger.info(f"Found {len(candidates)} qualified candidates for node {node_id}")
        
        # Create edges between current node and candidates
        created_edges = create_edges_batch(db, current_node, candidates)
        
        # If the OpenAI API call was successful (returned edges), mark as processed
        # Only mark as processed if we actually got edges (not an API failure)
        if created_edges is not None:
            edges_created = len(created_edges)
            logger.info(f"[EDGE_TRACE] Created {edges_created} edges for node {node_id} - marking as processed")
            total_edges_created += edges_created
            
            # Mark node as processed after successful edge creation
            node_repository.mark_node_processed(db, node_id)
            processed_count += 1
        else:
            logger.warning(f"[EDGE_TRACE] OpenAI API call failed for node {node_id} - NOT marking as processed")
            # Node remains unprocessed so it can be tried again later
    
    elapsed_time = time.time() - start_time
    
    result = {
        "processed_nodes": processed_count,
        "created_edges": total_edges_created,
        "elapsed_time": elapsed_time,
        "message": f"Processed {processed_count} nodes, created {total_edges_created} edges in {elapsed_time:.2f} seconds"
    }
    
    logger.info(f"Edge processing batch completed in {elapsed_time:.2f} seconds")
    logger.info(f"Processed {processed_count} nodes, created {total_edges_created} edges")
    
    return result