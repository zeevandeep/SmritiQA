"""
Batch process all unprocessed nodes and create edges between them.

This script processes a specified user's nodes in batches to create edges.
"""
import argparse
import logging
import requests
import json
import time
import sys
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL
BASE_URL = "http://127.0.0.1:5000/api/v1"

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by ID."""
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}")
        if response.status_code == 200:
            user = response.json()
            logger.info(f"Found user: {user.get('email')}")
            return user
        elif response.status_code == 404:
            logger.error(f"User with ID {user_id} not found")
            return None
        else:
            logger.error(f"Failed to get user: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting user: {e}", exc_info=True)
        return None

def get_unprocessed_node_count(user_id: str) -> int:
    """Get count of unprocessed nodes."""
    try:
        # This endpoint might not exist, in which case we'll get a 404
        response = requests.get(f"{BASE_URL}/nodes/unprocessed/count/{user_id}")
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 0)
        else:
            # Fall back to SQL query through execute_sql endpoint if it exists
            logger.info("Unprocessed node count endpoint not available, using database count")
            return 0  # Default if we can't get the count
    except Exception as e:
        logger.error(f"Error getting unprocessed node count: {e}", exc_info=True)
        return 0

def process_edges_batch(user_id: str, batch_size: int = 5) -> Optional[Dict[str, Any]]:
    """Process a batch of edges."""
    try:
        logger.info(f"Processing edge batch of size {batch_size} for user {user_id}")
        response = requests.post(
            f"{BASE_URL}/edges/process/{user_id}",
            params={"batch_size": batch_size}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Edge batch processing result: {result}")
            return result
        else:
            logger.error(f"Failed to process edges: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error processing edge batch: {e}", exc_info=True)
        return None

def get_user_edges(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get all edges for a user."""
    try:
        response = requests.get(f"{BASE_URL}/edges/user/{user_id}")
        if response.status_code == 200:
            edges = response.json()
            logger.info(f"Retrieved {len(edges)} edges for user {user_id}")
            return edges
        else:
            logger.error(f"Failed to get edges: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting edges: {e}", exc_info=True)
        return None

def analyze_edge_types(edges: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze the distribution of edge types."""
    type_counts = {}
    for edge in edges:
        edge_type = edge.get("edge_type")
        if edge_type:
            type_counts[edge_type] = type_counts.get(edge_type, 0) + 1
    
    # Sort by count in descending order
    sorted_counts = {k: v for k, v in sorted(
        type_counts.items(), key=lambda item: item[1], reverse=True)}
    
    return sorted_counts

def process_all_edges(user_id: str, batch_size: int = 5, max_batches: int = None):
    """Process all unprocessed nodes in batches."""
    # Verify user exists
    user = get_user_by_id(user_id)
    if not user:
        logger.error(f"User {user_id} not found, exiting")
        return
    
    # Start time for overall processing
    start_time = time.time()
    
    # Process batches until no more unprocessed nodes
    batch_num = 0
    total_processed = 0
    total_edges_created = 0
    
    while True:
        if max_batches is not None and batch_num >= max_batches:
            logger.info(f"Reached maximum number of batches ({max_batches}), stopping")
            break
        
        # Process a batch
        logger.info(f"Processing batch {batch_num + 1}...")
        result = process_edges_batch(user_id, batch_size)
        
        if not result:
            logger.error("Error processing batch, stopping")
            break
        
        processed = result.get("processed_nodes", 0)
        created = result.get("created_edges", 0)
        
        total_processed += processed
        total_edges_created += created
        
        logger.info(f"Batch {batch_num + 1}: Processed {processed} nodes, created {created} edges")
        
        # Check if we're done
        if processed == 0:
            logger.info("No more nodes to process, stopping")
            break
        
        batch_num += 1
        
        # Small delay between batches to avoid overwhelming the server
        time.sleep(1)
    
    # Calculate total time
    elapsed_time = time.time() - start_time
    
    # Get final edge statistics
    logger.info("Getting final edge statistics...")
    edges = get_user_edges(user_id)
    
    if edges:
        # Analyze edge types
        edge_types = analyze_edge_types(edges)
        
        # Print summary
        logger.info(f"\n{'='*50}")
        logger.info(f"EDGE PROCESSING SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Total batches processed: {batch_num}")
        logger.info(f"Total nodes processed: {total_processed}")
        logger.info(f"Total edges created: {total_edges_created}")
        logger.info(f"Total unique edges in database: {len(edges)}")
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        logger.info(f"\nEdge Type Distribution:")
        for edge_type, count in edge_types.items():
            logger.info(f"  - {edge_type}: {count} ({count/len(edges)*100:.1f}%)")
        logger.info(f"{'='*50}")
    else:
        logger.info(f"\n{'='*50}")
        logger.info(f"EDGE PROCESSING SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Total batches processed: {batch_num}")
        logger.info(f"Total nodes processed: {total_processed}")
        logger.info(f"Total edges created: {total_edges_created}")
        logger.info(f"Could not retrieve final edge statistics")
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        logger.info(f"{'='*50}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process all unprocessed nodes for edge creation")
    parser.add_argument("--user-id", required=True, help="ID of the user to process")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of nodes to process in each batch")
    parser.add_argument("--max-batches", type=int, default=None, help="Maximum number of batches to process (default: all)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting edge batch processing for user {args.user_id}")
    process_all_edges(args.user_id, args.batch_size, args.max_batches)
    logger.info("Edge batch processing completed")

if __name__ == "__main__":
    main()