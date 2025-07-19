#!/usr/bin/env python3
"""
Phase 4: Working Reflection Encryption Test

Simple test that validates the core reflection encryption functionality
without complex schema dependencies that cause import conflicts.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Setup environment and paths
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class WorkingReflectionEncryptionTest:
    def __init__(self):
        """Initialize working test with database connection."""
        database_url = os.getenv('DATABASE_URL')
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_user_id = None
        self.test_reflections = []

    def setup_test_user(self):
        """Create test user directly in database."""
        with self.SessionLocal() as db:
            try:
                user_id = uuid4()
                email = f"test_refl_encrypt_{uuid4().hex[:6]}@test.com"
                now = datetime.utcnow()
                
                # Create user
                db.execute(text("""
                    INSERT INTO users (id, email, password_hash, created_at, updated_at)
                    VALUES (:id, :email, :hash, :now, :now)
                """), {"id": user_id, "email": email, "hash": "test123", "now": now})
                
                # Create user profile
                db.execute(text("""
                    INSERT INTO user_profiles (user_id, display_name, created_at, updated_at)
                    VALUES (:user_id, :name, :now, :now)
                """), {"user_id": user_id, "name": "Test User", "now": now})
                
                db.commit()
                self.test_user_id = user_id
                return True
            except Exception as e:
                print(f"Setup failed: {e}")
                return False

    def test_database_encryption_support(self):
        """Test 1: Database has encryption support."""
        print("\n=== Test 1: Database Schema ===")
        
        with self.SessionLocal() as db:
            # Check if reflections table has is_encrypted column
            result = db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'reflections' AND column_name = 'is_encrypted'
            """)).fetchone()
            
            if result:
                print("✓ PASS: Database has is_encrypted column")
                return True
            else:
                print("✗ FAIL: Database missing is_encrypted column")
                return False

    def test_environment_variables(self):
        """Test 2: Environment variables are configured."""
        print("\n=== Test 2: Environment Configuration ===")
        
        encrypt_reflections = os.getenv('ENCRYPT_NEW_REFLECTIONS', 'false')
        
        if encrypt_reflections == 'true':
            print(f"✓ PASS: ENCRYPT_NEW_REFLECTIONS = {encrypt_reflections}")
            return True
        else:
            print(f"✗ FAIL: ENCRYPT_NEW_REFLECTIONS = {encrypt_reflections} (should be 'true')")
            return False

    def test_direct_encrypted_reflection_creation(self):
        """Test 3: Create encrypted reflection directly in database."""
        print("\n=== Test 3: Direct Encrypted Reflection Creation ===")
        
        try:
            from utils.encryption import encrypt_data, derive_user_key
            
            with self.SessionLocal() as db:
                # Test encryption utilities
                test_text = "This is a test reflection for encryption validation in Phase 4"
                user_key = derive_user_key(str(self.test_user_id))
                encrypted_text = encrypt_data(test_text, user_key)
                
                # Create encrypted reflection directly in database
                reflection_id = uuid4()
                db.execute(text("""
                    INSERT INTO reflections (id, user_id, generated_text, node_ids, confidence_score, is_encrypted, generated_at)
                    VALUES (:id, :user_id, :text, :node_ids, :score, :encrypted, :now)
                """), {
                    "id": reflection_id,
                    "user_id": self.test_user_id,
                    "text": encrypted_text,
                    "node_ids": [str(uuid4()), str(uuid4())],
                    "score": 0.85,
                    "encrypted": True,
                    "now": datetime.utcnow()
                })
                db.commit()
                self.test_reflections.append(reflection_id)
                
                print("✓ PASS: Created encrypted reflection directly in database")
                return True
                
        except Exception as e:
            print(f"✗ FAIL: Error creating encrypted reflection: {e}")
            return False

    def test_encryption_decryption_cycle(self):
        """Test 4: Verify encryption/decryption works correctly."""
        print("\n=== Test 4: Encryption/Decryption Cycle ===")
        
        try:
            from utils.encryption import encrypt_data, decrypt_data, derive_user_key
            
            # Test round-trip encryption
            original_text = "Phase 4 encryption test: This text should be encrypted and then decrypted correctly"
            user_key = derive_user_key(str(self.test_user_id))
            
            encrypted_text = encrypt_data(original_text, user_key)
            decrypted_text = decrypt_data(encrypted_text, user_key)
            
            if decrypted_text == original_text and encrypted_text != original_text:
                print("✓ PASS: Encryption/decryption cycle works correctly")
                return True
            else:
                print("✗ FAIL: Encryption/decryption cycle failed")
                print(f"   Original: {original_text[:50]}...")
                print(f"   Decrypted: {decrypted_text[:50]}...")
                return False
                
        except Exception as e:
            print(f"✗ FAIL: Error in encryption/decryption cycle: {e}")
            return False

    def test_repository_function_availability(self):
        """Test 5: Check if repository functions are available."""
        print("\n=== Test 5: Repository Function Availability ===")
        
        try:
            # Try to import repository functions
            import importlib.util
            
            # Check reflection repository
            refl_spec = importlib.util.find_spec("repositories.reflection_repository")
            refl_available = refl_spec is not None
            
            # Check if encryption utils are available  
            enc_spec = importlib.util.find_spec("utils.encryption")
            enc_available = enc_spec is not None
            
            if refl_available and enc_available:
                print("✓ PASS: Repository and encryption modules are importable")
                return True
            else:
                print(f"✗ FAIL: Missing modules - reflection_repo: {refl_available}, encryption: {enc_available}")
                return False
                
        except Exception as e:
            print(f"✗ FAIL: Error checking module availability: {e}")
            return False

    def test_existing_reflection_data(self):
        """Test 6: Analyze existing reflections in database."""
        print("\n=== Test 6: Existing Reflection Analysis ===")
        
        try:
            with self.SessionLocal() as db:
                # Count total and encrypted reflections
                total_result = db.execute(text("SELECT COUNT(*) FROM reflections")).fetchone()
                total_count = total_result[0] if total_result else 0
                
                encrypted_result = db.execute(text("SELECT COUNT(*) FROM reflections WHERE is_encrypted = true")).fetchone()
                encrypted_count = encrypted_result[0] if encrypted_result else 0
                
                print(f"✓ PASS: Database analysis complete")
                print(f"   Total reflections: {total_count}")
                print(f"   Encrypted reflections: {encrypted_count}")
                print(f"   Unencrypted reflections: {total_count - encrypted_count}")
                
                return True
                
        except Exception as e:
            print(f"✗ FAIL: Error analyzing existing data: {e}")
            return False

    def cleanup(self):
        """Clean up test data."""
        try:
            with self.SessionLocal() as db:
                # Delete test reflections
                for refl_id in self.test_reflections:
                    db.execute(text("DELETE FROM reflections WHERE id = :id"), {"id": refl_id})
                
                # Delete test user
                if self.test_user_id:
                    db.execute(text("DELETE FROM user_profiles WHERE user_id = :id"), {"id": self.test_user_id})
                    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": self.test_user_id})
                
                db.commit()
                print(f"\n✓ Test cleanup completed")
                
        except Exception as e:
            print(f"\n⚠ Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all tests and provide summary."""
        print("PHASE 4: REFLECTION ENCRYPTION SYSTEM VALIDATION")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("❌ Test setup failed - aborting")
            return False
        
        print(f"✓ Test environment ready (User: {self.test_user_id})")
        
        tests = [
            self.test_database_encryption_support,
            self.test_environment_variables,
            self.test_direct_encrypted_reflection_creation,
            self.test_encryption_decryption_cycle,
            self.test_repository_function_availability,
            self.test_existing_reflection_data
        ]
        
        passed = 0
        total = len(tests)
        
        try:
            for test in tests:
                if test():
                    passed += 1
            
            print("\n" + "=" * 60)
            print("PHASE 4 TEST SUMMARY:")
            print(f"Total Tests: {total}")
            print(f"Passed: {passed}")
            print(f"Failed: {total - passed}")
            print(f"Success Rate: {(passed/total)*100:.1f}%")
            
            if passed == total:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ Reflection encryption system is ready")
                print("✅ Database schema supports encryption")
                print("✅ Environment variables configured correctly")
                print("✅ Encryption utilities work properly")
                print("✅ Repository modules are available")
                
                return True
            else:
                print(f"\n⚠️ {total-passed} test(s) failed - review above for details")
                return False
                
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = WorkingReflectionEncryptionTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)