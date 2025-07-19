#!/usr/bin/env python3
"""
Test script to verify node encryption functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import uuid
from app.models.models import Node
from app.schemas.schemas import NodeCreate
from app.repositories.node_repository import create_node, get_node
from app.utils.encryption import test_encryption_roundtrip
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_node_encryption():
    """Test node encryption functionality."""
    print("Testing node encryption system...")
    print("=" * 60)
    
    # Get existing user from database
    engine = create_engine(os.environ.get("DATABASE_URL"))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Find an existing user
    from app.models.models import User, Session as DbSessionModel
    existing_user = db.query(User).first()
    if not existing_user:
        print("ERROR: No existing users found in database")
        return False
    
    test_user_id = existing_user.id
    
    # Find an existing session or create one for this user
    existing_session = db.query(DbSessionModel).filter(DbSessionModel.user_id == test_user_id).first()
    if existing_session:
        test_session_id = existing_session.id
    else:
        # Create a simple session for testing
        test_session = DbSessionModel(
            user_id=test_user_id,
            raw_transcript="Test transcript for encryption testing",
            is_processed=False,
            is_encrypted=False
        )
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        test_session_id = test_session.id
    
    # Test data
    test_text = "This is a test journal node with sensitive personal information about my feelings and thoughts."
    
    try:
        # Database already setup above
        
        print(f"Testing with user_id: {test_user_id}")
        print(f"ENCRYPT_NEW_NODES setting: {os.environ.get('ENCRYPT_NEW_NODES', 'NOT_SET')}")
        
        # Test 1: Create encrypted node
        print("\n1. Creating encrypted node...")
        node_data = NodeCreate(
            user_id=test_user_id,
            session_id=test_session_id,
            text=test_text,
            emotion="test_emotion",
            theme="test_theme",
            cognition_type="test_cognition"
        )
        
        created_node = create_node(db, node_data)
        print(f"✓ Node created with ID: {created_node.id}")
        print(f"✓ Is encrypted: {created_node.is_encrypted}")
        print(f"✓ Text length: {len(created_node.text)}")
        
        # Test 2: Retrieve node for user display (should be decrypted)
        print("\n2. Retrieving node for user display...")
        user_node = get_node(db, created_node.id, decrypt_for_processing=False)
        print(f"✓ Retrieved node for user display")
        print(f"✓ Text matches original: {user_node.text == test_text}")
        
        # Test 3: Retrieve node for processing (should be decrypted)
        print("\n3. Retrieving node for processing...")
        processing_node = get_node(db, created_node.id, decrypt_for_processing=True)
        print(f"✓ Retrieved node for processing")
        print(f"✓ Text matches original: {processing_node.text == test_text}")
        
        # Test 4: Verify encryption is working (check raw database)
        print("\n4. Verifying encryption in database...")
        raw_node = db.query(Node).filter(Node.id == created_node.id).first()
        if raw_node.is_encrypted:
            print(f"✓ Raw database text is encrypted: {raw_node.text != test_text}")
            print(f"✓ Encrypted text length: {len(raw_node.text)}")
        else:
            print("✓ Node stored as plain text (encryption disabled)")
        
        # Cleanup
        db.delete(raw_node)
        db.commit()
        db.close()
        
        print("\n" + "=" * 60)
        print("All node encryption tests PASSED!")
        return True
        
    except Exception as e:
        print(f"✗ Node encryption test FAILED with error: {e}")
        if 'db' in locals():
            db.close()
        return False

if __name__ == "__main__":
    print("Starting node encryption tests...")
    success = test_node_encryption()
    exit(0 if success else 1)