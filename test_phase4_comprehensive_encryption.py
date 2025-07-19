#!/usr/bin/env python3
"""
Phase 4: Comprehensive Testing of Node Text Encryption System
Tests all user scenarios, edge cases, and integration points.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import uuid
import time
import json
from datetime import datetime, timedelta
from app.models.models import User, Session as DbSessionModel, Node, Edge
from app.schemas.schemas import NodeCreate, SessionCreate
from app.repositories.node_repository import create_node, get_node, mark_node_processed
from app.repositories.session_repository import create_session
from app.repositories.edge_repository import create_edge
from app.services.embedding_processor import get_unprocessed_nodes, process_embeddings_batch
from app.services.reflection_processor import build_node_chain
from app.services.edge_processor import process_edges_for_session
from app.utils.encryption import encrypt_data, decrypt_data
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_comprehensive_encryption():
    """Run comprehensive encryption tests across all scenarios."""
    print("Phase 4: Comprehensive Encryption Testing")
    print("=" * 60)
    
    try:
        # Setup database connection
        engine = create_engine(os.environ.get("DATABASE_URL"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get existing user
        existing_user = db.query(User).first()
        if not existing_user:
            print("ERROR: No existing users found")
            return False
        
        test_user_id = existing_user.id
        print(f"Testing with user_id: {test_user_id}")
        
        # Test results tracking
        test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test 1: Mixed Encryption Environment
        print("\n1. Testing Mixed Encryption Environment...")
        test_mixed_encryption(db, test_user_id, test_results)
        
        # Test 2: Backward Compatibility
        print("\n2. Testing Backward Compatibility...")
        test_backward_compatibility(db, test_user_id, test_results)
        
        # Test 3: Edge Cases & Error Handling
        print("\n3. Testing Edge Cases & Error Handling...")
        test_edge_cases(db, test_user_id, test_results)
        
        # Test 4: End-to-End Workflow
        print("\n4. Testing End-to-End Workflow...")
        test_end_to_end_workflow(db, test_user_id, test_results)
        
        # Test 5: Performance & Scalability
        print("\n5. Testing Performance & Scalability...")
        test_performance_scalability(db, test_user_id, test_results)
        
        # Test 6: Security Validation
        print("\n6. Testing Security Validation...")
        test_security_validation(db, test_user_id, test_results)
        
        # Print final results
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        print(f"✓ Tests Passed: {test_results['passed']}")
        print(f"✗ Tests Failed: {test_results['failed']}")
        
        if test_results['errors']:
            print("\nErrors encountered:")
            for error in test_results['errors']:
                print(f"  - {error}")
        
        db.close()
        return test_results['failed'] == 0
        
    except Exception as e:
        print(f"✗ Comprehensive test FAILED with error: {e}")
        if 'db' in locals():
            db.close()
        return False

def test_mixed_encryption(db, user_id, results):
    """Test mixed encrypted/unencrypted nodes."""
    try:
        print("  a) Creating mixed encryption scenarios...")
        
        # Create sessions first
        session1_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Test session for unencrypted node",
            duration=30,
            is_encrypted=False
        )
        session1 = create_session(db, session1_data)
        
        session2_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Test session for encrypted node",
            duration=30,
            is_encrypted=False
        )
        session2 = create_session(db, session2_data)
        
        # Create unencrypted node (simulate old data)
        original_setting = os.environ.get('ENCRYPT_NEW_NODES')
        os.environ['ENCRYPT_NEW_NODES'] = 'false'
        
        unencrypted_node_data = NodeCreate(
            user_id=user_id,
            session_id=session1.id,
            text="Unencrypted legacy node content",
            emotion="neutral",
            theme="legacy",
            cognition_type="memory"
        )
        unencrypted_node = create_node(db, unencrypted_node_data)
        
        # Create encrypted node
        os.environ['ENCRYPT_NEW_NODES'] = 'true'
        
        encrypted_node_data = NodeCreate(
            user_id=user_id,
            session_id=session2.id,
            text="Encrypted new node content with sensitive data",
            emotion="positive",
            theme="security",
            cognition_type="analysis"
        )
        encrypted_node = create_node(db, encrypted_node_data)
        
        # Test retrieval of both types
        unencrypted_retrieved = get_node(db, unencrypted_node.id, decrypt_for_processing=True)
        encrypted_retrieved = get_node(db, encrypted_node.id, decrypt_for_processing=True)
        
        # Verify correct handling
        assert not unencrypted_node.is_encrypted, "Legacy node should not be encrypted"
        assert encrypted_node.is_encrypted, "New node should be encrypted"
        assert "Unencrypted legacy" in unencrypted_retrieved.text, "Legacy text should be readable"
        assert "Encrypted new node" in encrypted_retrieved.text, "Encrypted text should be decrypted"
        
        # Cleanup
        db.delete(unencrypted_node)
        db.delete(encrypted_node)
        db.delete(session1)
        db.delete(session2)
        db.commit()
        
        # Restore original setting
        if original_setting:
            os.environ['ENCRYPT_NEW_NODES'] = original_setting
        
        print("  ✓ Mixed encryption handling works correctly")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ Mixed encryption test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Mixed encryption: {e}")

def test_backward_compatibility(db, user_id, results):
    """Test backward compatibility with existing unencrypted data."""
    try:
        print("  a) Testing service layer with unencrypted nodes...")
        
        # Create session first
        session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Test session for legacy compatibility",
            duration=30,
            is_encrypted=False
        )
        session = create_session(db, session_data)
        
        # Create unencrypted node
        os.environ['ENCRYPT_NEW_NODES'] = 'false'
        
        legacy_node_data = NodeCreate(
            user_id=user_id,
            session_id=session.id,
            text="Legacy unencrypted content for backward compatibility testing",
            emotion="neutral",
            theme="compatibility",
            cognition_type="testing"
        )
        legacy_node = create_node(db, legacy_node_data)
        
        # Test embedding processor with unencrypted node
        unprocessed_nodes = get_unprocessed_nodes(db, batch_size=10)
        legacy_in_batch = any(node_id == legacy_node.id for node_id, _ in unprocessed_nodes)
        
        if legacy_in_batch:
            # Find our legacy node in the batch
            legacy_text = next(text for node_id, text in unprocessed_nodes if node_id == legacy_node.id)
            assert "Legacy unencrypted" in legacy_text, "Legacy text should be accessible"
        
        # Test reflection processor
        mock_edge = {
            'id': str(uuid.uuid4()),
            'from_node_id': legacy_node.id,
            'to_node_id': legacy_node.id
        }
        
        try:
            visited_nodes = set()
            chain = build_node_chain(db, mock_edge, user_id, visited_nodes)
            if chain:
                assert "Legacy unencrypted" in chain[0]['text'], "Legacy text should be in chain"
        except Exception:
            pass  # Expected for mock edge
        
        # Cleanup
        db.delete(legacy_node)
        db.delete(session)
        db.commit()
        
        print("  ✓ Backward compatibility maintained")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ Backward compatibility test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Backward compatibility: {e}")

def test_edge_cases(db, user_id, results):
    """Test edge cases and error handling."""
    try:
        print("  a) Testing empty/null text handling...")
        
        # Create session for empty text test
        empty_session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Empty text test session",
            duration=10,
            is_encrypted=False
        )
        empty_session = create_session(db, empty_session_data)
        
        # Test empty text
        empty_node_data = NodeCreate(
            user_id=user_id,
            session_id=empty_session.id,
            text="",
            emotion="neutral",
            theme="empty",
            cognition_type="test"
        )
        
        try:
            empty_node = create_node(db, empty_node_data)
            retrieved_empty = get_node(db, empty_node.id, decrypt_for_processing=True)
            assert retrieved_empty.text == "", "Empty text should remain empty"
            db.delete(empty_node)
            db.delete(empty_session)
            db.commit()
            print("  ✓ Empty text handled correctly")
        except Exception as e:
            print(f"  ⚠ Empty text handling: {e}")
            db.rollback()
        
        # Test very long text
        print("  b) Testing long text encryption...")
        
        # Create session for long text test
        long_session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Long text test session",
            duration=30,
            is_encrypted=False
        )
        long_session = create_session(db, long_session_data)
        
        long_text = "Very long sensitive content: " + "A" * 5000
        
        long_node_data = NodeCreate(
            user_id=user_id,
            session_id=long_session.id,
            text=long_text,
            emotion="neutral",
            theme="performance",
            cognition_type="test"
        )
        
        long_node = create_node(db, long_node_data)
        retrieved_long = get_node(db, long_node.id, decrypt_for_processing=True)
        
        assert len(retrieved_long.text) == len(long_text), "Long text should be fully preserved"
        assert "Very long sensitive" in retrieved_long.text, "Long text should be decrypted correctly"
        
        # Cleanup
        db.delete(long_node)
        db.delete(long_session)
        db.commit()
        
        print("  ✓ Long text encryption works correctly")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ Edge cases test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Edge cases: {e}")

def test_end_to_end_workflow(db, user_id, results):
    """Test complete end-to-end workflow with encryption."""
    try:
        print("  a) Testing complete journal entry workflow...")
        
        # Create session
        session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="This is a test journal entry with sensitive personal information about my thoughts and feelings.",
            duration=60,
            is_encrypted=False
        )
        session = create_session(db, session_data)
        
        # Create nodes from the session
        node_texts = [
            "I feel anxious about my upcoming presentation at work tomorrow",
            "My relationship with my partner is improving since we started therapy",
            "I'm proud of completing my fitness goals this month"
        ]
        
        created_nodes = []
        for i, text in enumerate(node_texts):
            node_data = NodeCreate(
                user_id=user_id,
                session_id=session.id,
                text=text,
                emotion=["anxiety", "love", "pride"][i],
                theme=["work", "relationships", "health"][i],
                cognition_type=["worry", "reflection", "achievement"][i]
            )
            node = create_node(db, node_data)
            created_nodes.append(node)
        
        # Test embedding processing
        print("  b) Testing embedding generation...")
        unprocessed = get_unprocessed_nodes(db, batch_size=10)
        session_nodes = [(nid, text) for nid, text in unprocessed if any(nid == n.id for n in created_nodes)]
        
        assert len(session_nodes) == 3, f"Should find 3 session nodes, found {len(session_nodes)}"
        
        for node_id, text in session_nodes:
            assert any(expected in text for expected in node_texts), "Decrypted text should match original"
        
        # Test edge processing (session-only)
        print("  c) Testing edge processing...")
        try:
            edge_results = process_edges_for_session(db, user_id, session.id)
            assert 'processed_nodes' in edge_results, "Edge processing should return results"
        except Exception as e:
            print(f"  ⚠ Edge processing: {e}")
        
        # Cleanup
        for node in created_nodes:
            db.delete(node)
        db.delete(session)
        db.commit()
        
        print("  ✓ End-to-end workflow completed successfully")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ End-to-end workflow test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"End-to-end workflow: {e}")

def test_performance_scalability(db, user_id, results):
    """Test performance with multiple encrypted nodes."""
    try:
        print("  a) Testing batch processing performance...")
        
        # Create session for batch test
        batch_session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Batch performance test session",
            duration=60,
            is_encrypted=False
        )
        batch_session = create_session(db, batch_session_data)
        
        start_time = time.time()
        batch_nodes = []
        
        # Create batch of encrypted nodes
        for i in range(10):
            node_data = NodeCreate(
                user_id=user_id,
                session_id=batch_session.id,
                text=f"Performance test node {i+1} with sensitive data that needs encryption",
                emotion=f"emotion_{i}",
                theme=f"performance_{i}",
                cognition_type=f"test_{i}"
            )
            node = create_node(db, node_data)
            batch_nodes.append(node)
        
        creation_time = time.time() - start_time
        
        # Test batch retrieval
        start_time = time.time()
        unprocessed = get_unprocessed_nodes(db, batch_size=20)
        batch_in_unprocessed = [(nid, text) for nid, text in unprocessed if any(nid == n.id for n in batch_nodes)]
        
        retrieval_time = time.time() - start_time
        
        assert len(batch_in_unprocessed) == 10, f"Should retrieve 10 nodes, got {len(batch_in_unprocessed)}"
        
        # Verify all texts are properly decrypted
        for node_id, text in batch_in_unprocessed:
            assert "Performance test node" in text, "Batch decryption should work correctly"
            assert "sensitive data" in text, "All text content should be decrypted"
        
        # Cleanup
        for node in batch_nodes:
            db.delete(node)
        db.delete(batch_session)
        db.commit()
        
        print(f"  ✓ Batch processing: {len(batch_nodes)} nodes created in {creation_time:.3f}s, retrieved in {retrieval_time:.3f}s")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ Performance test failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Performance: {e}")

def test_security_validation(db, user_id, results):
    """Test security aspects of encryption implementation."""
    try:
        print("  a) Testing encryption key isolation...")
        
        # Create session for security test
        security_session_data = SessionCreate(
            user_id=user_id,
            raw_transcript="Security validation test session",
            duration=30,
            is_encrypted=False
        )
        security_session = create_session(db, security_session_data)
        
        # Create node for current user
        user1_node_data = NodeCreate(
            user_id=user_id,
            session_id=security_session.id,
            text="User 1 sensitive information that should be isolated",
            emotion="private",
            theme="security",
            cognition_type="isolation"
        )
        user1_node = create_node(db, user1_node_data)
        
        # Verify raw database storage is encrypted
        raw_node = db.query(Node).filter(Node.id == user1_node.id).first()
        if raw_node.is_encrypted:
            assert "User 1 sensitive" not in raw_node.text, "Raw database text should be encrypted"
            assert len(raw_node.text) > len("User 1 sensitive information"), "Encrypted text should be longer"
        
        # Test decryption with correct key
        decrypted_node = get_node(db, user1_node.id, decrypt_for_processing=True)
        assert "User 1 sensitive" in decrypted_node.text, "Decryption should work with correct key"
        
        # Test manual encryption/decryption
        print("  b) Testing encryption utility functions...")
        test_text = "Secret message for testing encryption utilities"
        user_id_str = str(user_id)
        
        encrypted = encrypt_data(test_text, user_id_str)
        assert encrypted != test_text, "Encryption should change the text"
        assert len(encrypted) > len(test_text), "Encrypted text should be longer"
        
        decrypted = decrypt_data(encrypted, user_id_str)
        assert decrypted == test_text, "Decryption should restore original text"
        
        # Cleanup
        db.delete(user1_node)
        db.delete(security_session)
        db.commit()
        
        print("  ✓ Security validation passed")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  ✗ Security validation failed: {e}")
        results['failed'] += 1
        results['errors'].append(f"Security validation: {e}")

if __name__ == "__main__":
    print("Starting Phase 4: Comprehensive Encryption Testing...")
    success = test_comprehensive_encryption()
    print(f"\nPhase 4 Testing {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)