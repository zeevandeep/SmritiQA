"""
Node repository for database operations related to cognitive/emotional nodes.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Node
from app.schemas.schemas import NodeCreate

def get_node(db: DbSession, node_id: UUID) -> Optional[Node]:
    """
    Get a node by ID.
    
    Args:
        db: Database session.
        node_id: ID of the node to retrieve.
        
    Returns:
        Node object if found, None otherwise.
    """
    return db.query(Node).filter(Node.id == node_id).first()


def get_user_nodes(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Node]:
    """
    Get nodes for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of nodes to skip.
        limit: Maximum number of nodes to return.
        
    Returns:
        List of Node objects.
    """
    return db.query(Node)\
        .filter(Node.user_id == user_id)\
        .order_by(Node.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_session_nodes(db: DbSession, session_id: UUID) -> List[Node]:
    """
    Get nodes for a specific session.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        
    Returns:
        List of Node objects.
    """
    return db.query(Node)\
        .filter(Node.session_id == session_id)\
        .order_by(Node.created_at)\
        .all()


def get_node_details(db: DbSession, node_ids: List[UUID]) -> List[Node]:
    """
    Get detailed information for a list of nodes.
    
    Args:
        db: Database session.
        node_ids: List of node IDs to retrieve.
        
    Returns:
        List of Node objects.
    """
    return db.query(Node).filter(Node.id.in_(node_ids)).all()


def create_node(db: DbSession, node: NodeCreate) -> Node:
    """
    Create a new node.
    
    Args:
        db: Database session.
        node: Node data.
        
    Returns:
        Created Node object.
    """
    db_node = Node(**node.model_dump())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


def create_nodes_batch(db: DbSession, nodes: List[NodeCreate]) -> List[Node]:
    """
    Create multiple nodes in a batch.
    
    Args:
        db: Database session.
        nodes: List of node data.
        
    Returns:
        List of created Node objects.
    """
    db_nodes = [Node(**node.model_dump()) for node in nodes]
    db.add_all(db_nodes)
    db.commit()
    for node in db_nodes:
        db.refresh(node)
    return db_nodes


def mark_node_processed(db: DbSession, node_id: UUID) -> Optional[Node]:
    """
    Mark a node as processed.
    
    Args:
        db: Database session.
        node_id: ID of the node.
        
    Returns:
        Updated Node object if found, None otherwise.
    """
    db_node = get_node(db, node_id)
    if db_node is None:
        return None
    
    # Use setattr to avoid direct attribute assignment LSP error
    setattr(db_node, 'is_processed', True)
    db.commit()
    db.refresh(db_node)
    return db_node