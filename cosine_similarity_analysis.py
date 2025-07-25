#!/usr/bin/env python3
"""
Cosine Similarity Analysis Script for Smriti
Analyzes cosine similarity between nodes for a specific user in the last 7 days
Independent script that doesn't modify existing code
"""

import os
import sys
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import struct

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def decode_embedding(embedding_data):
    """Decode PostgreSQL bytea embedding data to numpy array"""
    if embedding_data is None:
        return None
    
    try:
        # PostgreSQL bytea is stored as bytes, convert to list of floats
        if isinstance(embedding_data, (bytes, memoryview)):
            # Unpack binary data as float32 values
            num_floats = len(embedding_data) // 4
            embedding = list(struct.unpack(f'{num_floats}f', embedding_data))
            return np.array(embedding)
        elif isinstance(embedding_data, list):
            return np.array(embedding_data)
        else:
            # Try to convert directly
            return np.array(embedding_data)
    except Exception as e:
        logger.error(f"Error decoding embedding: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    # Handle zero vectors
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)

def get_database_connection():
    """Get database connection using environment variables"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def fetch_user_nodes_last_7_days(session, user_id):
    """Fetch all nodes for a user from the last 7 days with embeddings"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    query = text("""
        SELECT 
            n.id,
            n.theme,
            n.emotion,
            n.cognition_type,
            n.embedding,
            n.is_processed,
            n.created_at,
            n.session_id,
            s.raw_transcript
        FROM nodes n
        LEFT JOIN sessions s ON n.session_id = s.id
        WHERE n.user_id = :user_id
        AND n.created_at >= :seven_days_ago
        AND n.embedding IS NOT NULL
        ORDER BY n.created_at ASC
    """)
    
    result = session.execute(query, {
        'user_id': user_id,
        'seven_days_ago': seven_days_ago
    })
    
    return result.fetchall()

def analyze_similarity_matrix(nodes):
    """Create and analyze similarity matrix for all nodes"""
    if len(nodes) < 2:
        logger.info("Less than 2 nodes found, cannot compute similarities")
        return
    
    logger.info(f"Analyzing {len(nodes)} nodes for similarity patterns")
    
    # Extract embeddings
    embeddings = []
    node_info = []
    
    for node in nodes:
        embedding = decode_embedding(node.embedding)
        if embedding is not None:
            embeddings.append(embedding)
            node_info.append({
                'id': str(node.id),
                'theme': node.theme,
                'emotion': node.emotion,
                'cognition_type': node.cognition_type,
                'is_processed': node.is_processed,
                'created_at': node.created_at,
                'session_id': str(node.session_id)
            })
    
    if len(embeddings) < 2:
        logger.info("Less than 2 valid embeddings found")
        return
    
    # Calculate similarity matrix
    n = len(embeddings)
    similarity_matrix = np.zeros((n, n))
    
    logger.info("\n" + "="*80)
    logger.info("COSINE SIMILARITY ANALYSIS")
    logger.info("="*80)
    
    # Print node summary
    logger.info(f"\nNODE SUMMARY ({n} nodes):")
    for i, info in enumerate(node_info):
        logger.info(f"Node {i}: {info['id'][:8]}... | Theme: {info['theme']:<12} | "
                   f"Emotion: {info['emotion']:<10} | Processed: {info['is_processed']} | "
                   f"Date: {info['created_at'].strftime('%Y-%m-%d %H:%M')}")
    
    # Calculate all pairwise similarities
    high_similarities = []
    medium_similarities = []
    low_similarities = []
    
    logger.info(f"\nSIMILARITY MATRIX:")
    logger.info("   " + "".join([f"{i:>8}" for i in range(n)]))
    
    for i in range(n):
        row_str = f"{i:2} "
        for j in range(n):
            if i == j:
                similarity_matrix[i][j] = 1.0
                row_str += f"{1.0:>8.3f}"
            else:
                sim = cosine_similarity(embeddings[i], embeddings[j])
                similarity_matrix[i][j] = sim
                row_str += f"{sim:>8.3f}"
                
                # Categorize similarities
                if sim >= 0.84:  # Final threshold
                    high_similarities.append((i, j, sim, node_info[i], node_info[j]))
                elif sim >= 0.7:  # Initial threshold
                    medium_similarities.append((i, j, sim, node_info[i], node_info[j]))
                else:
                    low_similarities.append((i, j, sim, node_info[i], node_info[j]))
        
        logger.info(row_str)
    
    # Analysis results
    logger.info(f"\nSIMILARITY ANALYSIS RESULTS:")
    logger.info(f"Total pairs analyzed: {(n * (n-1)) // 2}")
    logger.info(f"High similarities (≥0.84): {len(high_similarities)}")
    logger.info(f"Medium similarities (0.7-0.84): {len(medium_similarities)}")
    logger.info(f"Low similarities (<0.7): {len(low_similarities)}")
    
    # Detailed high similarity pairs
    if high_similarities:
        logger.info(f"\nHIGH SIMILARITY PAIRS (≥0.84) - WOULD CREATE EDGES:")
        for i, j, sim, node1, node2 in high_similarities:
            logger.info(f"  Nodes {i}↔{j}: {sim:.4f}")
            logger.info(f"    Node {i}: {node1['theme']} | {node1['emotion']} | Processed: {node1['is_processed']}")
            logger.info(f"    Node {j}: {node2['theme']} | {node2['emotion']} | Processed: {node2['is_processed']}")
            logger.info(f"    Time gap: {abs((node1['created_at'] - node2['created_at']).total_seconds() / 3600):.1f} hours")
            logger.info("")
    else:
        logger.info(f"\nNO HIGH SIMILARITY PAIRS FOUND (≥0.84)")
        logger.info("This explains why no edges were created!")
    
    # Top medium similarity pairs
    if medium_similarities:
        logger.info(f"\nTOP MEDIUM SIMILARITY PAIRS (0.7-0.84):")
        medium_similarities.sort(key=lambda x: x[2], reverse=True)
        for i, j, sim, node1, node2 in medium_similarities[:5]:  # Top 5
            logger.info(f"  Nodes {i}↔{j}: {sim:.4f}")
            logger.info(f"    Node {i}: {node1['theme']} | {node1['emotion']}")
            logger.info(f"    Node {j}: {node2['theme']} | {node2['emotion']}")
    
    # Statistical summary
    all_similarities = [sim for i, j, sim, _, _ in high_similarities + medium_similarities + low_similarities]
    if all_similarities:
        logger.info(f"\nSTATISTICAL SUMMARY:")
        logger.info(f"Average similarity: {np.mean(all_similarities):.4f}")
        logger.info(f"Max similarity: {np.max(all_similarities):.4f}")
        logger.info(f"Min similarity: {np.min(all_similarities):.4f}")
        logger.info(f"Std deviation: {np.std(all_similarities):.4f}")
    
    return similarity_matrix, node_info

def analyze_processed_status(nodes):
    """Analyze the is_processed status of nodes"""
    logger.info(f"\nPROCESSED STATUS ANALYSIS:")
    
    processed_count = sum(1 for node in nodes if node.is_processed)
    unprocessed_count = len(nodes) - processed_count
    
    logger.info(f"Total nodes: {len(nodes)}")
    logger.info(f"Processed nodes: {processed_count}")
    logger.info(f"Unprocessed nodes: {unprocessed_count}")
    
    if unprocessed_count > 0:
        logger.info(f"\nUNPROCESSED NODES:")
        for node in nodes:
            if not node.is_processed:
                logger.info(f"  {str(node.id)[:8]}... | Theme: {node.theme} | "
                           f"Date: {node.created_at.strftime('%Y-%m-%d %H:%M')} | "
                           f"Session: {str(node.session_id)[:8]}...")

def main():
    """Main analysis function"""
    user_id = "1d8beecc-2468-4217-a469-a242214b3426"
    
    try:
        # Get database connection
        session, engine = get_database_connection()
        
        # Fetch user nodes from last 7 days
        logger.info(f"Fetching nodes for user {user_id} from last 7 days...")
        nodes = fetch_user_nodes_last_7_days(session, user_id)
        
        if not nodes:
            logger.info("No nodes found for the specified user in the last 7 days")
            return
        
        logger.info(f"Found {len(nodes)} nodes with embeddings")
        
        # Analyze processed status
        analyze_processed_status(nodes)
        
        # Perform similarity analysis
        similarity_matrix, node_info = analyze_similarity_matrix(nodes)
        
        # Close session
        session.close()
        
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)