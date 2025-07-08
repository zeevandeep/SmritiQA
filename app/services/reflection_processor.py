"""
Reflection processing service module for the Smriti application.

This module is responsible for generating reflections based on connected nodes
in the graph. It identifies chains of connected nodes, extracts insights from
these chains, and returns personalized reflections.
"""
from typing import List, Dict, Any, Optional, Set, Union, cast
from uuid import UUID
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import time
import random
import os

from sqlalchemy.orm import Session as DbSession
from sqlalchemy import Column

from app.repositories import edge_repository, node_repository, reflection_repository
from app.utils.openai_utils import generate_reflection
from app.schemas.schemas import ReflectionCreate
from app.models.models import Edge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum chain length to follow when building node chains
MAX_CHAIN_LENGTH = int(os.environ.get("MAX_CHAIN_LENGTH", "20"))

# Maximum age of nodes to include in the chain (in days)
MAX_NODE_AGE_DAYS = int(os.environ.get("MAX_NODE_AGE_DAYS", "90"))


def build_node_chain(db: DbSession, edge: Dict[str, Any], user_id: UUID, visited_nodes: Set[UUID]) -> List[Dict[str, Any]]:
    """
    Build a chain of connected nodes starting from an unprocessed edge.
    
    Args:
        db: Database session.
        edge: The starting edge to build the chain from.
        user_id: The user ID for whom we're building the chain.
        visited_nodes: Set of node IDs that have already been visited to avoid cycles.
        
    Returns:
        List of dictionaries containing node information in the chain.
    """
    logger.info(f"Building node chain starting from edge: {edge.get('id')}")
    
    # Extract the source and target nodes from the edge
    # Keys are from_node_id and to_node_id in the dictionary, even though fields in DB are from_node and to_node
    from_node_id = edge.get('from_node_id') 
    to_node_id = edge.get('to_node_id')
    
    # Initialize the chain with the source node
    chain = []
    
    # Add the source node to the chain if it hasn't been visited and is not None
    if from_node_id and from_node_id not in visited_nodes:
        # Convert to UUID if necessary
        from_node_id_uuid = from_node_id if isinstance(from_node_id, UUID) else UUID(str(from_node_id))
        from_node = node_repository.get_node(db, from_node_id_uuid)
        if from_node:
            chain.append({
                'id': str(from_node.id),
                'text': from_node.text,
                'theme': from_node.theme,
                'cognition_type': from_node.cognition_type,
                'emotion': from_node.emotion,
                'created_at': from_node.created_at
            })
            # Convert to UUID before adding to set
            visited_nodes.add(UUID(str(from_node.id)))
    
    # Add the target node to the chain if it hasn't been visited and is not None
    if to_node_id and to_node_id not in visited_nodes:
        # Convert to UUID if necessary
        to_node_id_uuid = to_node_id if isinstance(to_node_id, UUID) else UUID(str(to_node_id))
        to_node = node_repository.get_node(db, to_node_id_uuid)
        if to_node:
            chain.append({
                'id': str(to_node.id),
                'text': to_node.text,
                'theme': to_node.theme,
                'cognition_type': to_node.cognition_type,
                'emotion': to_node.emotion,
                'created_at': to_node.created_at
            })
            # Convert to UUID before adding to set
            visited_nodes.add(UUID(str(to_node.id)))
    
    # If we have both nodes, move backwards through the graph to extend the chain
    # We'll use all edges (both processed and unprocessed) for the user to build the chain
    current_chain_length = len(chain)
    all_user_edges = edge_repository.get_all_user_edges(db, user_id)
    
    # Convert the edges to a dictionary for faster lookups
    edge_dict = defaultdict(list)
    for e in all_user_edges:
        edge_dict[str(e.to_node)].append({
            'id': str(e.id),
            'from_node_id': str(e.from_node),
            'to_node_id': str(e.to_node),
            'edge_type': e.edge_type,
            'match_strength': e.match_strength,
            'explanation': e.explanation
        })
    
    # Start extending the chain from the source node of the original edge
    current_node_id = from_node_id
    
    # Continue building the chain until we reach the maximum length or have no more edges
    while current_chain_length < MAX_CHAIN_LENGTH:
        # Find edges where the current node is the target
        prev_edges = edge_dict.get(str(current_node_id), [])
        
        if not prev_edges:
            # No more edges connecting to the current node, stop extending the chain
            break
        
        # Calculate combined_score for each edge (even though we'll choose randomly)
        # This is kept for logging and potential future use
        now = datetime.now()
        for edge in prev_edges:
            # Default to a neutral value (7 days) if we can't determine the age
            days_since_creation = 7
            
            # Try to determine the edge's age
            try:
                # First check if created_at is in the edge dictionary
                if 'created_at' in edge and edge['created_at'] is not None:
                    edge_date = edge['created_at']
                    if isinstance(edge_date, datetime):
                        days_since_creation = (now - edge_date).days
                        days_since_creation = max(0, days_since_creation)  # Ensure non-negative
                # If not in the dictionary, try to fetch from the database
                else:
                    edge_id_str = edge.get('id')
                    if edge_id_str:
                        try:
                            edge_id = UUID(str(edge_id_str))
                            db_edge = edge_repository.get_edge(db, edge_id)
                            if db_edge is not None:
                                # Extract created_at by string name to avoid SQLAlchemy Column type issues
                                edge_date = getattr(db_edge, 'created_at', None)
                                if isinstance(edge_date, datetime):
                                    days_since_creation = (now - edge_date).days
                                    days_since_creation = max(0, days_since_creation)  # Ensure non-negative
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid edge ID format: {e}")
            except Exception as e:
                logger.warning(f"Error determining edge age: {e}")
                # Keep using the default value
                
            # Calculate decay value
            decay_value = 1.0 / (1.0 + (days_since_creation / 7.0))
            
            # Calculate combined score
            match_strength = float(edge.get('match_strength', 0))
            combined_score = match_strength + (0.3 * decay_value)
            
            # Store the combined score in the edge dictionary
            edge['combined_score'] = combined_score
            
            # Log the score components for debugging
            logger.debug(f"Edge {edge.get('id')}: match_strength={match_strength:.3f}, decay_value={decay_value:.3f}, combined_score={combined_score:.3f}, days_since_creation={days_since_creation}")
        
        # Choose a random edge from all available edges (totally random selection)
        # Create a copy of the edges list to safely remove from it if needed due to cycles
        available_edges = prev_edges.copy()
        
        while available_edges:
            # Select a random edge from available edges
            prev_edge = random.choice(available_edges)
            logger.info(f"Randomly selected edge {prev_edge.get('id')} for chain extension")
            
            # Get the source node ID from this edge
            prev_node_id = UUID(prev_edge.get('from_node_id'))
            
            # Check if adding this node would create a cycle
            if prev_node_id in visited_nodes:
                # This would create a cycle, remove it from available edges and try another
                logger.debug(f"Edge {prev_edge.get('id')} would create a cycle, trying another")
                available_edges.remove(prev_edge)
                continue
            
            # We found a usable edge that doesn't create a cycle
            break
        
        # If we exhausted all edges without finding a suitable one (all created cycles)
        if not available_edges:
            logger.info("All available edges would create cycles, stopping chain extension")
            break
            
        # Add the previous node to the chain
        prev_node = node_repository.get_node(db, prev_node_id)
        if prev_node:
            # Check if the node is older than MAX_NODE_AGE_DAYS
            now = datetime.now()
            if prev_node.created_at and (now - prev_node.created_at).days > MAX_NODE_AGE_DAYS:
                logger.info(f"Node {prev_node.id} is older than {MAX_NODE_AGE_DAYS} days, stopping chain extension")
                break
                
            chain.insert(0, {  # Insert at the beginning to maintain chronological order
                'id': str(prev_node.id),
                'text': prev_node.text,
                'theme': prev_node.theme,
                'cognition_type': prev_node.cognition_type,
                'emotion': prev_node.emotion,
                'created_at': prev_node.created_at
            })
            # Convert to UUID before adding to set
            visited_nodes.add(UUID(str(prev_node.id)))
            current_chain_length += 1
            current_node_id = prev_node_id
        else:
            # Node not found, stop extending the chain
            break
    
    # Sort the chain chronologically by created_at
    chain.sort(key=lambda x: x.get('created_at', datetime.min))
    
    logger.info(f"Built chain with {len(chain)} nodes")
    return chain


def collect_edges_for_chain(db: DbSession, node_ids: List[UUID]) -> List[Dict[str, Any]]:
    """
    Collect all edges between nodes in the chain.
    
    Args:
        db: Database session.
        node_ids: List of node IDs in the chain.
        
    Returns:
        List of dictionaries containing edge information.
    """
    logger.info(f"Collecting edges for {len(node_ids)} nodes")
    
    edges = []
    
    # For each consecutive pair of nodes in the chain, find the edge connecting them
    for i in range(len(node_ids) - 1):
        from_node_id = node_ids[i]
        to_node_id = node_ids[i + 1]
        
        # Check if an edge exists from from_node to to_node
        edge_exists = edge_repository.check_edge_exists(db, from_node_id, to_node_id)
        
        if edge_exists:
            # Get all edges connecting the nodes using the repository
            matching_edges = edge_repository.get_edges_between_nodes(db, from_node_id, to_node_id)
                
            if matching_edges:
                edge = matching_edges[0]  # Take the first matching edge
                edges.append({
                    'id': str(edge.id),
                    'edge_type': edge.edge_type,
                    'match_strength': edge.match_strength,
                    'explanation': edge.explanation,
                    'from_node_id': str(edge.from_node),
                    'to_node_id': str(edge.to_node)
                })
        
        # Check if an edge exists from to_node to from_node (in case the direction is reversed)
        edge_exists = edge_repository.check_edge_exists(db, to_node_id, from_node_id)
        
        if edge_exists:
            # Get all edges connecting the nodes in reverse direction using the repository
            matching_edges = edge_repository.get_edges_between_nodes(db, to_node_id, from_node_id)
                
            if matching_edges:
                edge = matching_edges[0]  # Take the first matching edge
                edges.append({
                    'id': str(edge.id),
                    'edge_type': edge.edge_type,
                    'match_strength': edge.match_strength,
                    'explanation': edge.explanation,
                    'from_node_id': str(edge.to_node),  # Reverse direction for consistency
                    'to_node_id': str(edge.from_node)   # Reverse direction for consistency
                })
    
    logger.info(f"Collected {len(edges)} edges for the chain")
    return edges


def generate_reflection_from_chain(chain: List[Dict[str, Any]], edges: List[Dict[str, Any]], user_id: UUID) -> Dict[str, Any]:
    """
    Generate a reflection based on a chain of nodes.
    
    Args:
        chain: List of node dictionaries in the chain.
        edges: List of edge dictionaries connecting the nodes.
        user_id: The user ID to associate with the reflection.
        
    Returns:
        Dictionary containing the created reflection data.
        
    Note:
        If the reflection cannot be generated, returns a dict with 'success': False
        Otherwise, returns a dict with the reflection data and 'success': True
    """
    logger.info(f"Generating reflection from chain with {len(chain)} nodes")
    
    # Generate the reflection using OpenAI
    max_retries = 3
    retry_count = 0
    reflection_result = None
    
    while retry_count < max_retries:
        try:
            reflection_result = generate_reflection(chain, edges)
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Error generating reflection (attempt {retry_count}/{max_retries}): {e}", exc_info=True)
            time.sleep(2 * retry_count)  # Exponential backoff
    
    if not reflection_result:
        logger.warning("Failed to generate reflection after multiple attempts")
        return {
            "error": "Failed to generate reflection after multiple attempts",
            "success": False
        }
    
    # Extract node IDs from the chain, safely handling None values
    node_ids = []
    for node in chain:
        if node and node.get('id'):
            try:
                node_ids.append(UUID(str(node.get('id'))))
            except (ValueError, TypeError):
                pass
    
    # Extract edge IDs from the edges, safely handling None values
    edge_ids = []
    for edge in edges:
        if edge and edge.get('id'):
            try:
                edge_ids.append(UUID(str(edge.get('id'))))
            except (ValueError, TypeError):
                pass
    
    # Check if we have valid node_ids before creating the reflection
    if not node_ids:
        logger.warning("No valid node IDs found for reflection generation")
        return {
            "error": "No valid node IDs found for reflection generation",
            "success": False
        }
    
    # Create a reflection object
    # edge_ids is optional in our schema, only include if we have them
    reflection_args = {
        "user_id": user_id,
        "node_ids": node_ids,
        "generated_text": reflection_result.get('generated_text', ''),
        "confidence_score": reflection_result.get('confidence_score', 0.0)
    }
    
    # Only add edge_ids if we have them
    if edge_ids:
        reflection_args["edge_ids"] = edge_ids
        
    reflection_data = ReflectionCreate(**reflection_args)
    
    logger.info(f"Generated reflection with confidence score: {reflection_data.confidence_score}")
    # Convert ReflectionCreate to dict for return value
    result_dict = {
        "user_id": str(reflection_data.user_id),
        "node_ids": [str(node_id) for node_id in reflection_data.node_ids],
        "generated_text": reflection_data.generated_text,
        "confidence_score": reflection_data.confidence_score,
        "success": True
    }
    
    # Only include edge_ids if they exist
    if reflection_data.edge_ids:
        result_dict["edge_ids"] = [str(edge_id) for edge_id in reflection_data.edge_ids]
        
    return result_dict


def generate_single_reflection_for_user(
    db: DbSession,
    user_id: UUID
) -> Dict[str, Any]:
    """
    Generate a single reflection for a user using iterative edge selection.
    
    Tries multiple edges in order of strength until finding one that produces
    a valid chain (minimum 3 nodes) for reflection generation.
    
    Args:
        db: Database session.
        user_id: User ID to generate reflection for.
        
    Returns:
        Dictionary containing the result with 'reflections_created' count and reflection data.
    """
    logger.info(f"Generating single reflection for user: {user_id}")
    
    stats = {
        'reflections_created': 0,
        'edges_processed': 0,
        'errors': 0,
        'attempts_made': 0
    }
    
    # Maximum number of edges to try before giving up
    MAX_ATTEMPTS = int(os.environ.get("MAX_REFLECTION_ATTEMPTS", "10"))
    attempt_count = 0
    
    try:
        while attempt_count < MAX_ATTEMPTS:
            # Get current unprocessed edges (refreshed each iteration)
            edges = edge_repository.get_unprocessed_edges(db, user_id)
            
            if not edges:
                logger.info(f"No more unprocessed edges found for user {user_id} after {attempt_count} attempts")
                break
            
            attempt_count += 1
            stats['attempts_made'] = attempt_count
            
            # Calculate combined scores for all remaining edges
            edges_with_scores = []
            now = datetime.now()
            
            for edge in edges:
                # Calculate days since creation for decay factor
                days_since_creation = 7  # Default value
                
                if hasattr(edge, 'created_at') and edge.created_at:
                    days_since_creation = max(0, (now - edge.created_at).days)
                
                # Calculate decay value and combined score
                decay_value = 1.0 / (1.0 + (days_since_creation / 7.0))
                combined_score = float(edge.match_strength) + (0.3 * decay_value)
                
                edges_with_scores.append({
                    'edge': edge,
                    'combined_score': combined_score
                })
            
            # Sort edges by combined score in descending order
            edges_with_scores.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Select the strongest remaining edge for this attempt
            strongest_edge = edges_with_scores[0]['edge']
            logger.info(f"Attempt {attempt_count}: Selected edge {strongest_edge.id} with score {edges_with_scores[0]['combined_score']}")
            
            # Convert the edge to a dictionary for easier handling
            edge_dict = {
                'id': str(strongest_edge.id),
                'from_node_id': strongest_edge.from_node,
                'to_node_id': strongest_edge.to_node,
                'edge_type': strongest_edge.edge_type,
                'match_strength': strongest_edge.match_strength,
                'explanation': strongest_edge.explanation
            }
            
            # Build a chain of nodes from this edge
            visited_nodes = set()
            chain = build_node_chain(db, edge_dict, user_id, visited_nodes)
            
            if len(chain) < 3:
                logger.info(f"Chain too short for edge {strongest_edge.id} ({len(chain)} nodes), marking as processed and trying next edge")
                edge_repository.mark_edge_processed(db, UUID(str(strongest_edge.id)))
                stats['edges_processed'] += 1
                continue  # Try next edge
            
            logger.info(f"Found valid chain with {len(chain)} nodes for edge {strongest_edge.id}")
            
            # Collect all edges connecting nodes in the chain
            node_ids = [UUID(node.get('id')) for node in chain]
            edges_for_chain = collect_edges_for_chain(db, node_ids)
            
            # Generate a reflection from the chain
            reflection_data = generate_reflection_from_chain(chain, edges_for_chain, user_id)
            
            if reflection_data and isinstance(reflection_data, dict) and reflection_data.get('success', False):
                # SUCCESS: Create proper ReflectionCreate object from the dict
                reflection_create = ReflectionCreate(
                    user_id=UUID(reflection_data['user_id']),
                    node_ids=[UUID(nid) for nid in reflection_data['node_ids']],
                    edge_ids=[UUID(eid) for eid in reflection_data['edge_ids']] if 'edge_ids' in reflection_data else [],
                    generated_text=reflection_data['generated_text'],
                    confidence_score=reflection_data['confidence_score']
                )
                
                # Create the reflection in the database
                reflection = reflection_repository.create_reflection(db, reflection_create)
                logger.info(f"Successfully created reflection: {reflection.id} after {attempt_count} attempts")
                
                # Mark the starting edge as processed
                edge_repository.mark_edge_processed(db, UUID(str(strongest_edge.id)))
                
                stats['reflections_created'] = 1
                stats['edges_processed'] += 1
                stats['reflection'] = {
                    'id': str(reflection.id),
                    'generated_text': reflection.generated_text,
                    'confidence_score': reflection.confidence_score,
                    'generated_at': reflection.generated_at.isoformat()
                }
                
                # Return immediately on success
                return stats
            else:
                logger.warning(f"Failed to generate reflection for edge {strongest_edge.id}, marking as processed and trying next edge")
                edge_repository.mark_edge_processed(db, UUID(str(strongest_edge.id)))
                stats['edges_processed'] += 1
                stats['errors'] += 1
                continue  # Try next edge
                
        # If we reach here, we've either exhausted all attempts or all edges
        if attempt_count >= MAX_ATTEMPTS:
            logger.warning(f"Reached maximum attempts ({MAX_ATTEMPTS}) for user {user_id} without generating reflection")
        else:
            logger.info(f"No more unprocessed edges available for user {user_id} after {attempt_count} attempts")
            
    except Exception as e:
        logger.error(f"Error generating reflection for user {user_id}: {e}", exc_info=True)
        stats['errors'] += 1
    
    return stats


def process_unprocessed_edges_for_reflection(
    db: DbSession,
    user_id: Optional[UUID] = None,
    batch_size_per_user: int = 5,
    overall_batch_size: int = 50
) -> Dict[str, Any]:
    """
    Process unprocessed edges to generate reflections.
    
    Args:
        db: Database session.
        user_id: Optional user ID to limit processing to a specific user.
        batch_size_per_user: Maximum number of unprocessed edges to process per user.
        overall_batch_size: Maximum total number of unprocessed edges to process.
        
    Returns:
        Dictionary containing processing statistics.
    """
    logger.info(f"Processing unprocessed edges for reflection generation")
    
    stats = {
        'reflections_created': 0,
        'edges_processed': 0,
        'users_processed': 0,
        'errors': 0
    }
    
    # Organize unprocessed edges by user
    edges_by_user = defaultdict(list)
    
    if user_id:
        logger.info(f"Getting unprocessed edges for user: {user_id}")
        # Get unprocessed edges for the specific user
        edges = edge_repository.get_unprocessed_edges(db, user_id)
        edges_by_user[user_id] = edges
    else:
        logger.info("Getting unprocessed edges for all users")
        # Group unprocessed edges by user
        all_unprocessed_edges = edge_repository.get_unprocessed_edges(db)
        
        for edge in all_unprocessed_edges:
            # Determine the user ID from the edge
            edge_user_id = None
            
            # Get the from_node to determine its user_id
            try:
                from_node_uuid = UUID(str(edge.from_node))
                from_node = node_repository.get_node(db, from_node_uuid)
                if from_node:
                    # Extract user_id attribute safely
                    try:
                        user_id_str = str(from_node.user_id) if from_node.user_id is not None else None
                    except:
                        user_id_str = None
                    edge_user_id = UUID(user_id_str) if user_id_str else None
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error extracting user_id from edge {edge.id}: {e}")
            
            if edge_user_id:
                edges_by_user[edge_user_id].append(edge)
    
    # Process one reflection per user based on the strongest edge
    processed_users = set()
    now = datetime.now()
    
    for uid, edges in edges_by_user.items():
        if not edges:
            continue
            
        try:
            # Calculate combined scores for all edges
            edges_with_scores = []
            for edge in edges:
                # Calculate days since creation for decay factor
                days_since_creation = 7  # Default value
                
                if hasattr(edge, 'created_at') and edge.created_at:
                    days_since_creation = max(0, (now - edge.created_at).days)
                
                # Calculate decay value and combined score
                decay_value = 1.0 / (1.0 + (days_since_creation / 7.0))
                combined_score = float(edge.match_strength) + (0.3 * decay_value)
                
                edges_with_scores.append({
                    'edge': edge,
                    'combined_score': combined_score
                })
            
            # Sort edges by combined score in descending order
            edges_with_scores.sort(key=lambda x: x['combined_score'], reverse=True)
            
            if not edges_with_scores:
                logger.warning(f"No edges with scores found for user {uid}")
                continue
                
            # Select the edge with the highest combined score
            strongest_edge = edges_with_scores[0]['edge']
            logger.info(f"Selected strongest edge {strongest_edge.id} for user {uid} with score {edges_with_scores[0]['combined_score']}")
            
            # Mark all other edges as processed immediately
            for edge_score in edges_with_scores[1:]:
                edge = edge_score['edge']
                edge_repository.mark_edge_processed(db, UUID(str(edge.id)))
                stats['edges_processed'] += 1
                logger.info(f"Marked edge {edge.id} as processed without using it for reflection")
            
            # Process the strongest edge to generate a reflection
            # Convert the edge to a dictionary for easier handling
            edge_dict = {
                'id': str(strongest_edge.id),
                'from_node_id': strongest_edge.from_node,
                'to_node_id': strongest_edge.to_node,
                'edge_type': strongest_edge.edge_type,
                'match_strength': strongest_edge.match_strength,
                'explanation': strongest_edge.explanation
            }
            
            # Build a chain of nodes from this edge
            visited_nodes = set()
            chain = build_node_chain(db, edge_dict, uid, visited_nodes)
            
            if len(chain) < 3:
                logger.warning(f"Chain too short for edge: {strongest_edge.id}, marking as processed (minimum 3 nodes required)")
                edge_repository.mark_edge_processed(db, UUID(str(strongest_edge.id)))
                stats['edges_processed'] += 1
                continue
            
            # Collect all edges connecting nodes in the chain
            node_ids = [UUID(node.get('id')) for node in chain]
            edges_for_chain = collect_edges_for_chain(db, node_ids)
            
            # Generate a reflection from the chain
            reflection_data = generate_reflection_from_chain(chain, edges_for_chain, uid)
            
            if reflection_data:
                # Check if the reflection data is a dict with success=False or a ReflectionCreate object
                if isinstance(reflection_data, dict) and not reflection_data.get('success', False):
                    logger.warning(f"Failed to generate reflection for edge: {strongest_edge.id}")
                    stats['errors'] += 1
                    continue
                
                # If it's a dict with success=True, extract the reflection data and create the reflection
                if isinstance(reflection_data, dict):
                    # Create proper ReflectionCreate object from the dict
                    reflection_create = ReflectionCreate(
                        user_id=UUID(reflection_data['user_id']),
                        node_ids=[UUID(nid) for nid in reflection_data['node_ids']],
                        edge_ids=[UUID(eid) for eid in reflection_data['edge_ids']],
                        generated_text=reflection_data['generated_text'],
                        confidence_score=reflection_data['confidence_score']
                    )
                else:
                    # It's already a ReflectionCreate object
                    reflection_create = reflection_data
                
                # Create the reflection in the database
                reflection = reflection_repository.create_reflection(db, reflection_create)
                logger.info(f"Created reflection: {reflection.id}")
                
                # Mark the starting edge as processed
                edge_repository.mark_edge_processed(db, UUID(str(strongest_edge.id)))
                
                stats['reflections_created'] += 1
                stats['edges_processed'] += 1
                processed_users.add(uid)
            else:
                logger.warning(f"Failed to generate reflection for edge: {strongest_edge.id}")
                stats['errors'] += 1
        except Exception as e:
            logger.error(f"Error processing edges for user {uid}: {e}", exc_info=True)
            stats['errors'] += 1
    
    stats['users_processed'] = len(processed_users)
    
    logger.info(f"Reflection generation stats: {stats}")
    return stats