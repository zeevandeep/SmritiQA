"""
Node repository for database operations related to cognitive/emotional nodes.
"""
import os
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Node, MigrationError
from app.schemas.schemas import NodeCreate
from app.utils.encryption import encrypt_data, decrypt_data, EncryptionError

logger = logging.getLogger(__name__)

def get_node(db: DbSession, node_id: UUID, decrypt_for_processing: bool = False) -> Optional[Node]:
    """
    Get a node by ID with optional decryption for processing.
    
    Args:
        db: Database session.
        node_id: ID of the node to retrieve.
        decrypt_for_processing: If True, returns detached object with decrypted data for OpenAI.
                               If False (default), returns attached SQLAlchemy object for normal operations.
        
    Returns:
        Node object (attached or detached based on decrypt_for_processing) if found, None otherwise.
    """
    logger.info(f"Getting node: {node_id}, decrypt_for_processing: {decrypt_for_processing}")
    
    db_node = db.query(Node).filter(Node.id == node_id).first()
    if not db_node:
        logger.warning(f"Node not found: {node_id}")
        return None
    
    logger.info(f"Found node {node_id}, is_encrypted: {db_node.is_encrypted}")
    
    # If not requesting decryption, return the attached SQLAlchemy object
    if not decrypt_for_processing:
        logger.info(f"Returning attached SQLAlchemy object for node {node_id}")
        return db_node
    
    # For processing - return detached object with decrypted data if encrypted
    if db_node.is_encrypted and db_node.text:
        try:
            user_id = str(db_node.user_id)
            logger.info(f"Decrypting node {node_id} for processing (user {user_id})")
            
            # Create a new Node object with decrypted data (not a copy)
            decrypted_text = decrypt_data(db_node.text, user_id)
            
            decrypted_node = Node(
                id=db_node.id,
                user_id=db_node.user_id,
                session_id=db_node.session_id,
                text=decrypted_text,  # Use decrypted text
                emotion=db_node.emotion,
                theme=db_node.theme,
                cognition_type=db_node.cognition_type,
                embedding=db_node.embedding,
                created_at=db_node.created_at,
                is_processed=db_node.is_processed,
                is_encrypted=db_node.is_encrypted
            )
            
            logger.info(f"Successfully decrypted node {node_id} for processing, decrypted length: {len(decrypted_text)}")
            return decrypted_node
            
        except EncryptionError as e:
            logger.error(f"[ENCRYPTION FAIL] op=decrypt node_id={node_id} user_id={user_id} error={e}")
            # Log encryption error for review
            error_record = MigrationError(
                user_id=db_node.user_id,
                session_id=db_node.session_id,
                error_type="node_decryption_failed",
                error_message=f"Failed to decrypt node {node_id}: {str(e)}"
            )
            db.add(error_record)
            db.commit()
            
            # Return original encrypted node for fallback
            logger.warning(f"Decryption failed for node {node_id}, returning encrypted node")
            return db_node
    
    # For unencrypted nodes or processing without decryption needed
    logger.info(f"Returning node {node_id} (encryption not needed)")
    return db_node


def get_user_nodes(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100, decrypt_for_processing: bool = False) -> List[Node]:
    """
    Get nodes for a user with optional decryption.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of nodes to skip.
        limit: Maximum number of nodes to return.
        decrypt_for_processing: If True, returns decrypted text for processing.
        
    Returns:
        List of Node objects with decrypted text if requested.
    """
    logger.info(f"Getting user nodes: user_id={user_id}, skip={skip}, limit={limit}, decrypt_for_processing={decrypt_for_processing}")
    
    db_nodes = db.query(Node)\
        .filter(Node.user_id == user_id)\
        .order_by(Node.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    if not decrypt_for_processing:
        # For user-facing operations, return attached SQLAlchemy objects
        return db_nodes
    
    # For processing operations, return with processing decryption
    return [get_node(db, node.id, decrypt_for_processing=True) for node in db_nodes if get_node(db, node.id, decrypt_for_processing=True)]


def get_session_nodes(db: DbSession, session_id: UUID, decrypt_for_processing: bool = False) -> List[Node]:
    """
    Get nodes for a specific session with optional decryption.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        decrypt_for_processing: If True, returns decrypted text for processing.
        
    Returns:
        List of Node objects with decrypted text if requested.
    """
    logger.info(f"Getting session nodes: session_id={session_id}, decrypt_for_processing={decrypt_for_processing}")
    
    db_nodes = db.query(Node)\
        .filter(Node.session_id == session_id)\
        .order_by(Node.created_at)\
        .all()
    
    if not db_nodes:
        return []
    
    user_id = str(db_nodes[0].user_id)  # All nodes in session belong to same user
    
    if not decrypt_for_processing:
        # For user-facing operations, return attached SQLAlchemy objects
        return db_nodes
    
    # For processing operations, return with processing decryption
    return [get_node(db, node.id, decrypt_for_processing=True) for node in db_nodes if get_node(db, node.id, decrypt_for_processing=True)]


def get_node_details(db: DbSession, node_ids: List[UUID], decrypt_for_processing: bool = False) -> List[Node]:
    """
    Get detailed information for a list of nodes with optional decryption.
    
    Args:
        db: Database session.
        node_ids: List of node IDs to retrieve.
        decrypt_for_processing: If True, returns decrypted text for processing.
        
    Returns:
        List of Node objects with decrypted text if requested.
    """
    logger.info(f"Getting node details: {len(node_ids)} nodes, decrypt_for_processing={decrypt_for_processing}")
    
    db_nodes = db.query(Node).filter(Node.id.in_(node_ids)).all()
    
    if not db_nodes:
        return []
    
    if not decrypt_for_processing:
        # For user-facing operations, return attached SQLAlchemy objects
        return db_nodes
    
    # For processing operations, return with processing decryption
    return [get_node(db, node.id, decrypt_for_processing=True) for node in db_nodes if get_node(db, node.id, decrypt_for_processing=True)]


def _decrypt_nodes_for_user(db: DbSession, nodes: List[Node], user_id: str) -> List[Node]:
    """
    Helper function to decrypt nodes for user-facing operations (always return decrypted text).
    
    Args:
        db: Database session.
        nodes: List of Node objects to decrypt.
        user_id: User ID for decryption.
        
    Returns:
        List of Node objects with decrypted text for display.
    """
    decrypted_nodes = []
    
    for node in nodes:
        if node.is_encrypted and node.text:
            try:
                logger.info(f"Decrypting node {node.id} for user display (user {user_id})")
                decrypted_text = decrypt_data(node.text, user_id)
                
                # Create new node with decrypted text for display
                decrypted_node = Node(
                    id=node.id,
                    user_id=node.user_id,
                    session_id=node.session_id,
                    text=decrypted_text,
                    emotion=node.emotion,
                    theme=node.theme,
                    cognition_type=node.cognition_type,
                    embedding=node.embedding,
                    created_at=node.created_at,
                    is_processed=node.is_processed,
                    is_encrypted=node.is_encrypted
                )
                decrypted_nodes.append(decrypted_node)
                logger.info(f"Successfully decrypted node {node.id} for user display")
                
            except EncryptionError as e:
                logger.error(f"[ENCRYPTION FAIL] op=decrypt_for_user node_id={node.id} user_id={user_id} error={e}")
                # Log encryption error
                error_record = MigrationError(
                    user_id=node.user_id,
                    session_id=node.session_id,
                    error_type="node_user_decryption_failed",
                    error_message=f"Failed to decrypt node {node.id} for user display: {str(e)}"
                )
                db.add(error_record)
                db.commit()
                
                # Return encrypted node as fallback
                decrypted_nodes.append(node)
                logger.warning(f"Decryption failed for node {node.id}, returning encrypted text")
        else:
            # Node is not encrypted, return as-is
            decrypted_nodes.append(node)
    
    return decrypted_nodes


def create_node(db: DbSession, node: NodeCreate) -> Node:
    """
    Create a new node with optional encryption based on environment settings.
    
    Args:
        db: Database session.
        node: Node data.
        
    Returns:
        Created Node object.
    """
    logger.info(f"Creating new node for user {node.user_id}")
    
    # Check if encryption is enabled for new nodes
    encrypt_new_nodes = os.environ.get("ENCRYPT_NEW_NODES", "false").lower() == "true"
    logger.info(f"ENCRYPT_NEW_NODES setting: {encrypt_new_nodes}")
    
    node_data = node.model_dump()
    
    if encrypt_new_nodes and node_data.get('text'):
        try:
            user_id = str(node.user_id)
            original_text = node_data['text']
            logger.info(f"Encrypting node text for user {user_id}, original length: {len(original_text)}")
            
            # Encrypt the text
            encrypted_text = encrypt_data(original_text, user_id)
            node_data['text'] = encrypted_text
            node_data['is_encrypted'] = True
            
            logger.info(f"Successfully encrypted node text for user {user_id}, encrypted length: {len(encrypted_text)}")
            
        except EncryptionError as e:
            logger.error(f"[ENCRYPTION FAIL] op=encrypt user_id={user_id} error={e}")
            # Log encryption error
            error_record = MigrationError(
                user_id=node.user_id,
                session_id=node.session_id,
                error_type="node_encryption_failed",
                error_message=f"Failed to encrypt node text: {str(e)}"
            )
            db.add(error_record)
            db.commit()
            
            # Continue with unencrypted text as fallback
            node_data['is_encrypted'] = False
            logger.warning(f"Encryption failed for user {user_id}, storing as plain text")
    else:
        # Encryption disabled or no text to encrypt
        node_data['is_encrypted'] = False
        logger.info(f"Node encryption disabled or no text, storing as plain text")
    
    db_node = Node(**node_data)
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    
    logger.info(f"Successfully created node {db_node.id}, encrypted: {db_node.is_encrypted}")
    return db_node


def create_nodes_batch(db: DbSession, nodes: List[NodeCreate]) -> List[Node]:
    """
    Create multiple nodes in a batch with optional encryption based on environment settings.
    
    Args:
        db: Database session.
        nodes: List of node data.
        
    Returns:
        List of created Node objects.
    """
    logger.info(f"Creating batch of {len(nodes)} nodes")
    
    # Check if encryption is enabled for new nodes
    encrypt_new_nodes = os.environ.get("ENCRYPT_NEW_NODES", "false").lower() == "true"
    logger.info(f"ENCRYPT_NEW_NODES setting: {encrypt_new_nodes}")
    
    db_nodes = []
    
    for node in nodes:
        node_data = node.model_dump()
        
        if encrypt_new_nodes and node_data.get('text'):
            try:
                user_id = str(node.user_id)
                original_text = node_data['text']
                logger.info(f"Encrypting batch node text for user {user_id}, original length: {len(original_text)}")
                
                # Encrypt the text
                encrypted_text = encrypt_data(original_text, user_id)
                node_data['text'] = encrypted_text
                node_data['is_encrypted'] = True
                
                logger.info(f"Successfully encrypted batch node text for user {user_id}")
                
            except EncryptionError as e:
                logger.error(f"[ENCRYPTION FAIL] op=encrypt_batch user_id={user_id} error={e}")
                # Log encryption error
                error_record = MigrationError(
                    user_id=node.user_id,
                    session_id=node.session_id,
                    error_type="node_batch_encryption_failed",
                    error_message=f"Failed to encrypt batch node text: {str(e)}"
                )
                db.add(error_record)
                db.commit()
                
                # Continue with unencrypted text as fallback
                node_data['is_encrypted'] = False
                logger.warning(f"Batch encryption failed for user {user_id}, storing as plain text")
        else:
            # Encryption disabled or no text to encrypt
            node_data['is_encrypted'] = False
        
        db_nodes.append(Node(**node_data))
    
    db.add_all(db_nodes)
    db.commit()
    for node in db_nodes:
        db.refresh(node)
    
    encrypted_count = sum(1 for node in db_nodes if node.is_encrypted)
    logger.info(f"Successfully created batch of {len(db_nodes)} nodes, {encrypted_count} encrypted")
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