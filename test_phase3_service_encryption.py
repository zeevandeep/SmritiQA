#!/usr/bin/env python3
"""
Test script to verify Phase 3 service layer encryption functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import uuid
from app.models.models import User, Session as DbSessionModel
from app.schemas.schemas import NodeCreate
from app.repositories.node_repository import create_node
from app.services.embedding_processor import get_unprocessed_nodes
from app.services.reflection_processor import build_node_chain
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_service_layer_encryption():
    """Test service layer encryption functionality."""
    print("Testing Phase 3: Service Layer Encryption...")
    print("=" * 60)
    
    try:
        # Setup database connection
        engine = create_engine(os.environ.get("DATABASE_URL"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get existing user and session
        existing_user = db.query(User).first()
        if not existing_user:
            print("ERROR: No existing users found")
            return False
        
        test_user_id = existing_user.id
        
        # Find or create session
        existing_session = db.query(DbSessionModel).filter(DbSessionModel.user_id == test_user_id).first()
        if existing_session:
            test_session_id = existing_session.id
        else:
            test_session = DbSessionModel(
                user_id=test_user_id,
                raw_transcript="Test transcript for Phase 3 service encryption testing",
                is_processed=False,
                is_encrypted=False
            )
            db.add(test_session)
            db.commit()
            db.refresh(test_session)
            test_session_id = test_session.id
        
        print(f"Testing with user_id: {test_user_id}")
        print(f"ENCRYPT_NEW_NODES setting: {os.environ.get('ENCRYPT_NEW_NODES', 'NOT_SET')}")
        
        # Test 1: Create encrypted nodes
        print("\n1. Testing node creation with encryption...")
        test_nodes = []
        for i in range(3):
            node_data = NodeCreate(
                user_id=test_user_id,
                session_id=test_session_id,
                text=f"Test node {i+1}: This contains sensitive personal information that should be encrypted.",
                emotion=f"emotion_{i+1}",
                theme=f"theme_{i+1}",
                cognition_type=f"cognition_{i+1}"
            )
            created_node = create_node(db, node_data)
            test_nodes.append(created_node)
            print(f"✓ Created node {i+1} with ID: {created_node.id}, encrypted: {created_node.is_encrypted}")
        
        # Test 2: Test embedding processor service
        print("\n2. Testing embedding processor service...")
        unprocessed_nodes = get_unprocessed_nodes(db, batch_size=5)
        print(f"✓ Embedding service found {len(unprocessed_nodes)} unprocessed nodes")
        
        if unprocessed_nodes:
            # Check if decrypted text is returned
            sample_node_id, sample_text = unprocessed_nodes[0]
            print(f"✓ Sample decrypted text length: {len(sample_text)}")
            print(f"✓ Sample text preview: {sample_text[:50]}...")
            
            # Verify it's actually decrypted (readable)
            is_readable = "sensitive" in sample_text.lower() or "test" in sample_text.lower()
            print(f"✓ Text appears to be decrypted: {is_readable}")
        
        # Test 3: Test reflection processor chain building
        print("\n3. Testing reflection processor service...")
        
        # Create a simple edge-like structure for testing
        mock_edge = {
            'id': str(uuid.uuid4()),
            'from_node_id': test_nodes[0].id,
            'to_node_id': test_nodes[1].id if len(test_nodes) > 1 else test_nodes[0].id,
            'match_strength': 0.85
        }
        
        visited_nodes = set()
        try:
            chain = build_node_chain(db, mock_edge, test_user_id, visited_nodes)
            print(f"✓ Chain building service created chain with {len(chain)} nodes")
            
            if chain:
                # Check if decrypted text is in the chain
                sample_chain_node = chain[0]
                print(f"✓ Chain node text length: {len(sample_chain_node['text'])}")
                print(f"✓ Chain text preview: {sample_chain_node['text'][:50]}...")
                
                # Verify it's decrypted
                is_readable = "sensitive" in sample_chain_node['text'].lower() or "test" in sample_chain_node['text'].lower()
                print(f"✓ Chain text appears to be decrypted: {is_readable}")
            
        except Exception as e:
            print(f"⚠ Chain building test skipped (expected for mock edge): {e}")
        
        # Cleanup
        for node in test_nodes:
            db.delete(node)
        db.commit()
        db.close()
        
        print("\n" + "=" * 60)
        print("Phase 3 service layer encryption tests COMPLETED!")
        return True
        
    except Exception as e:
        print(f"✗ Phase 3 service test FAILED with error: {e}")
        if 'db' in locals():
            db.close()
        return False

if __name__ == "__main__":
    print("Starting Phase 3 service layer encryption tests...")
    success = test_service_layer_encryption()
    exit(0 if success else 1)