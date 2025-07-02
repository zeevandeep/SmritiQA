"""
Edge repository for database operations related to edges between nodes.
"""
from typing import List, Optional, Tuple, Sequence, Any
from uuid import UUID

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.engine.row import Row

from app.models.models import Edge, Node
from app.schemas.schemas import EdgeCreate


def get_edge(db: DbSession, edge_id: UUID) -> Optional[Edge]:
    """
    Get an edge by ID.
    
    Args:
        db: Database session.
        edge_id: ID of the edge to retrieve.
        
    Returns:
        Edge object if found, None otherwise.
    """
    return db.query(Edge).filter(Edge.id == edge_id).first()


def get_user_edges(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Edge]:
    """
    Get edges for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of edges to skip.
        limit: Maximum number of edges to return.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge)\
        .filter(Edge.user_id == user_id)\
        .order_by(Edge.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def create_edge(db: DbSession, edge: EdgeCreate) -> Edge:
    """
    Create a new edge.
    
    Args:
        db: Database session.
        edge: Edge data.
        
    Returns:
        Created Edge object.
    """
    db_edge = Edge(
        from_node=edge.from_node,
        to_node=edge.to_node,
        user_id=edge.user_id,
        edge_type=edge.edge_type,
        match_strength=edge.match_strength,
        session_relation=edge.session_relation,
        explanation=edge.explanation
    )
    db.add(db_edge)
    db.commit()
    db.refresh(db_edge)
    return db_edge


def create_edges_batch(db: DbSession, edges: List[EdgeCreate]) -> List[Edge]:
    """
    Create multiple edges in a batch.
    
    Args:
        db: Database session.
        edges: List of edge data.
        
    Returns:
        List of created Edge objects.
    """
    db_edges = []
    for edge in edges:
        db_edge = Edge(
            from_node=edge.from_node,
            to_node=edge.to_node,
            user_id=edge.user_id,
            edge_type=edge.edge_type,
            match_strength=edge.match_strength,
            session_relation=edge.session_relation,
            explanation=edge.explanation
        )
        db.add(db_edge)
        db_edges.append(db_edge)
    
    db.commit()
    for edge in db_edges:
        db.refresh(edge)
    
    return db_edges


def get_node_edges(db: DbSession, node_id: UUID) -> List[Edge]:
    """
    Get all edges connected to a node (both incoming and outgoing).
    
    Args:
        db: Database session.
        node_id: ID of the node.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge)\
        .filter(or_(Edge.from_node == node_id, Edge.to_node == node_id))\
        .order_by(Edge.created_at.desc())\
        .all()


def get_from_edges(db: DbSession, node_id: UUID) -> List[Edge]:
    """
    Get edges where the node is the source.
    
    Args:
        db: Database session.
        node_id: ID of the source node.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge)\
        .filter(Edge.from_node == node_id)\
        .order_by(Edge.created_at.desc())\
        .all()


def get_to_edges(db: DbSession, node_id: UUID) -> List[Edge]:
    """
    Get edges where the node is the target.
    
    Args:
        db: Database session.
        node_id: ID of the target node.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge)\
        .filter(Edge.to_node == node_id)\
        .order_by(Edge.created_at.desc())\
        .all()


def get_edges_between_nodes(db: DbSession, from_node_id: UUID, to_node_id: UUID) -> List[Edge]:
    """
    Get all edges between two specific nodes (directed from -> to).
    
    Args:
        db: Database session.
        from_node_id: Source node ID.
        to_node_id: Target node ID.
        
    Returns:
        List of Edge objects connecting the two nodes.
    """
    return db.query(Edge)\
        .filter(Edge.from_node == from_node_id, Edge.to_node == to_node_id)\
        .order_by(Edge.created_at.desc())\
        .all()


def get_session_edges(db: DbSession, session_id: UUID) -> List[Edge]:
    """
    Get edges where at least one node belongs to the specified session.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        
    Returns:
        List of Edge objects.
    """
    # Find all nodes in the session
    session_nodes = db.query(Node.id).filter(Node.session_id == session_id).all()
    node_ids = [node.id for node in session_nodes]
    
    # Find edges that connect to or from these nodes
    return db.query(Edge)\
        .filter(or_(Edge.from_node.in_(node_ids), Edge.to_node.in_(node_ids)))\
        .order_by(Edge.created_at.desc())\
        .all()


def get_unprocessed_edges_limited(db: DbSession, limit: int = 100) -> List[Edge]:
    """
    Get a limited number of edges that have not been processed yet.
    
    Args:
        db: Database session.
        limit: Maximum number of edges to return.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge)\
        .filter(Edge.is_processed == False)\
        .order_by(Edge.created_at)\
        .limit(limit)\
        .all()


def mark_edge_as_processed(db: DbSession, edge_id: UUID) -> Optional[Edge]:
    """
    Mark an edge as processed.
    
    Args:
        db: Database session.
        edge_id: ID of the edge to mark as processed.
        
    Returns:
        Updated Edge object, or None if not found.
    """
    edge = get_edge(db, edge_id)
    if edge:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(edge, 'is_processed', True)
        db.commit()
        db.refresh(edge)
    
    return edge


def check_edge_exists(db: DbSession, from_node_id: UUID, to_node_id: UUID) -> bool:
    """
    Check if an edge already exists between two nodes.
    
    Args:
        db: Database session.
        from_node_id: ID of the source node.
        to_node_id: ID of the target node.
        
    Returns:
        True if an edge exists, False otherwise.
    """
    edge = db.query(Edge)\
        .filter(and_(Edge.from_node == from_node_id, Edge.to_node == to_node_id))\
        .first()
    
    return edge is not None


def get_edge_count(db: DbSession, user_id: UUID) -> int:
    """
    Get the total number of edges for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        
    Returns:
        Count of edges.
    """
    return db.query(func.count(Edge.id))\
        .filter(Edge.user_id == user_id)\
        .scalar()


def get_top_edge_types(db: DbSession, user_id: UUID, limit: int = 5) -> Sequence[Row]:
    """
    Get the most common edge types for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        limit: Maximum number of edge types to return.
        
    Returns:
        Sequence of Row objects containing edge_type and count.
    """
    return db.query(Edge.edge_type, func.count(Edge.edge_type).label('count'))\
        .filter(Edge.user_id == user_id)\
        .group_by(Edge.edge_type)\
        .order_by(desc('count'))\
        .limit(limit)\
        .all()


def mark_chain_linked_edges(db: DbSession, user_id: Optional[UUID] = None, batch_size: int = 100) -> int:
    """
    Identify and mark edges that are part of potential chains.
    
    An edge is considered part of a chain if its to_node is also the from_node of another edge.
    
    Args:
        db: Database session.
        user_id: Optional user ID to limit processing to a specific user.
        batch_size: Maximum number of edges to process.
        
    Returns:
        Number of edges marked as processed.
    """
    # Build a CTE query to identify chain-linked edges
    from sqlalchemy.sql import text
    
    # Prepare the user filter
    user_filter = f"AND user_id = '{user_id}'" if user_id else ""
    
    # Execute a raw SQL query with CTEs for efficiency
    sql = text(f"""
    WITH UserIds AS (
        SELECT DISTINCT user_id
        FROM edges
        WHERE is_processed = false
        {user_filter}
        LIMIT {batch_size}
    ),
    ChainLinkedEdges AS (
        SELECT 
            e1.id AS edge_id
        FROM edges e1
        JOIN edges e2 ON e1.to_node = e2.from_node 
        WHERE 
            e1.is_processed = false
            AND e2.is_processed = false
            AND e1.user_id = e2.user_id
            AND e1.user_id IN (SELECT user_id FROM UserIds)
    ),
    UpdatedEdges AS (
        UPDATE edges
        SET is_processed = true
        WHERE id IN (SELECT edge_id FROM ChainLinkedEdges)
        RETURNING id
    )
    SELECT COUNT(*) AS processed_count FROM UpdatedEdges
    """)
    
    result = db.execute(sql)
    processed_count = result.scalar() or 0
    db.commit()
    
    return processed_count


def get_unprocessed_edges(db: DbSession, user_id: Optional[UUID] = None) -> List[Edge]:
    """
    Get edges that have not been processed yet (is_processed=False).
    
    Args:
        db: Database session.
        user_id: Optional user ID to limit results to a specific user.
        
    Returns:
        List of unprocessed Edge objects.
    """
    query = db.query(Edge).filter(Edge.is_processed == False)
    
    if user_id:
        query = query.filter(Edge.user_id == user_id)
    
    return query.order_by(Edge.user_id, Edge.created_at.desc()).all()


def get_all_user_edges(db: DbSession, user_id: UUID) -> List[Edge]:
    """
    Get all edges for a user regardless of processing status.
    
    This is used for building chains that include both processed and unprocessed edges.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        
    Returns:
        List of all Edge objects for the user.
    """
    return db.query(Edge).filter(Edge.user_id == user_id).all()


def get_edges_by_ids(db: DbSession, edge_ids: List[UUID]) -> List[Edge]:
    """
    Get edges by their IDs.
    
    Args:
        db: Database session.
        edge_ids: List of edge IDs to retrieve.
        
    Returns:
        List of Edge objects.
    """
    return db.query(Edge).filter(Edge.id.in_(edge_ids)).all()


def mark_edge_processed(db: DbSession, edge_id: UUID) -> Optional[Edge]:
    """
    Mark an edge as processed (is_processed=True).
    
    Args:
        db: Database session.
        edge_id: ID of the edge to mark as processed.
        
    Returns:
        Updated Edge object if found, None otherwise.
    """
    edge = get_edge(db, edge_id)
    if edge:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(edge, 'is_processed', True)
        db.commit()
        db.refresh(edge)
    
    return edge