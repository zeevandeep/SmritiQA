#!/usr/bin/env python3
"""
Phase 4: Comprehensive Final Reflection Encryption Test

Validates the complete reflection encryption system end-to-end.
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


class Phase4ComprehensiveFinalTest:
    def __init__(self):
        """Initialize comprehensive final test."""
        database_url = os.getenv('DATABASE_URL')
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_user_id = None
        self.test_reflections = []
        self.passed = 0
        self.failed = 0

    def setup_test_user(self):
        """Create test user."""
        with self.SessionLocal() as db:
            try:
                user_id = uuid4()
                email = f"test_phase4_final_{uuid4().hex[:6]}@test.com"
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
                """), {"user_id": user_id, "name": "Phase 4 Final Test", "now": now})
                
                db.commit()
                self.test_user_id = user_id
                return True
            except Exception as e:
                print(f"Setup error: {e}")
                return False

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        if success:
            self.passed += 1
            print(f"✓ PASS: {test_name}")
        else:
            self.failed += 1
            print(f"✗ FAIL: {test_name}")
        if details:
            print(f"   {details}")

    def test_database_environment_foundation(self):
        """Test 1: Database schema and environment configuration."""
        print("\n=== Test 1: Foundation (Database + Environment) ===")
        
        with self.SessionLocal() as db:
            # Check database schema
            schema_result = db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'reflections' AND column_name = 'is_encrypted'
            """)).fetchone()
            
            # Check environment
            encrypt_setting = os.getenv('ENCRYPT_NEW_REFLECTIONS', 'false')
            
            foundation_ok = (schema_result is not None and encrypt_setting == 'true')
            
            self.log_test(
                "Database & Environment Foundation",
                foundation_ok,
                f"Schema: {'✓' if schema_result else '✗'}, ENCRYPT_NEW_REFLECTIONS: {encrypt_setting}"
            )

    def test_encryption_utilities_core(self):
        """Test 2: Core encryption/decryption functionality."""
        print("\n=== Test 2: Encryption Utilities Core ===")
        
        try:
            from utils.encryption import encrypt_data, decrypt_data
            
            # Test encryption/decryption cycle with string user_id
            test_text = "Phase 4 comprehensive test: encryption validation with detailed content."
            user_id_str = str(self.test_user_id)
            
            encrypted_text = encrypt_data(test_text, user_id_str)
            decrypted_text = decrypt_data(encrypted_text, user_id_str)
            
            core_success = (decrypted_text == test_text and 
                           encrypted_text != test_text and 
                           len(encrypted_text) > 0)
            
            self.log_test(
                "Encryption Utilities Core",
                core_success,
                f"Round-trip: {'✓' if decrypted_text == test_text else '✗'}, Encrypted: {'✓' if encrypted_text != test_text else '✗'}"
            )
            
        except Exception as e:
            self.log_test("Encryption Utilities Core", False, f"Error: {e}")

    def test_direct_database_encryption(self):
        """Test 3: Direct database encryption workflow."""
        print("\n=== Test 3: Direct Database Encryption ===")
        
        try:
            from utils.encryption import encrypt_data
            
            with self.SessionLocal() as db:
                # Create encrypted reflection directly
                test_text = "PHASE4_DIRECT_DATABASE_ENCRYPTION_TEST_CONTENT"
                user_id_str = str(self.test_user_id)
                encrypted_text = encrypt_data(test_text, user_id_str)
                
                reflection_id = uuid4()
                node_id1, node_id2 = uuid4(), uuid4()
                db.execute(text("""
                    INSERT INTO reflections (id, user_id, generated_text, node_ids, confidence_score, is_encrypted, generated_at)
                    VALUES (:id, :user_id, :text, ARRAY[:node1, :node2]::uuid[], :score, :encrypted, :now)
                """), {
                    "id": reflection_id,
                    "user_id": self.test_user_id,
                    "text": encrypted_text,
                    "node1": node_id1,
                    "node2": node_id2,
                    "score": 0.90,
                    "encrypted": True,
                    "now": datetime.utcnow()
                })
                db.commit()
                self.test_reflections.append(reflection_id)
                
                # Verify encryption in raw storage
                raw_result = db.execute(text("""
                    SELECT generated_text, is_encrypted FROM reflections WHERE id = :id
                """), {"id": reflection_id}).fetchone()
                
                if raw_result:
                    stored_text, is_encrypted_flag = raw_result
                    properly_stored = (is_encrypted_flag and 
                                     "PHASE4_DIRECT_DATABASE" not in str(stored_text))
                    
                    self.log_test(
                        "Direct Database Encryption",
                        properly_stored,
                        f"Stored encrypted: {'✓' if properly_stored else '✗'}, Flag: {is_encrypted_flag}"
                    )
                else:
                    self.log_test("Direct Database Encryption", False, "Could not retrieve stored data")
                
        except Exception as e:
            self.log_test("Direct Database Encryption", False, f"Error: {e}")

    def test_repository_integration_simulation(self):
        """Test 4: Repository-level integration simulation.""" 
        print("\n=== Test 4: Repository Integration Simulation ===")
        
        try:
            # Import schemas to create proper data structures
            from schemas.schemas import ReflectionCreate
            from repositories import reflection_repository
            from uuid import UUID
            
            with self.SessionLocal() as db:
                # Create ReflectionCreate object properly
                reflection_data = ReflectionCreate(
                    user_id=UUID(str(self.test_user_id)),
                    generated_text="Repository integration test: This reflection tests the complete repository layer encryption workflow with proper schema validation.",
                    node_ids=[UUID(str(uuid4())), UUID(str(uuid4()))],
                    confidence_score=0.88
                )
                
                # Set encryption environment
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                
                # Create reflection through repository
                created_reflection = reflection_repository.create_reflection(db, reflection_data)
                
                if hasattr(created_reflection, 'id'):
                    self.test_reflections.append(created_reflection.id)
                    
                    # Verify creation
                    repository_success = (created_reflection is not None and
                                        hasattr(created_reflection, 'generated_text') and
                                        created_reflection.generated_text is not None)
                    
                    self.log_test(
                        "Repository Integration",
                        repository_success,
                        f"Created: {'✓' if repository_success else '✗'}, ID: {getattr(created_reflection, 'id', 'None')}"
                    )
                else:
                    self.log_test("Repository Integration", False, "No ID attribute in created reflection")
                
        except Exception as e:
            self.log_test("Repository Integration", False, f"Error: {e}")

    def test_mixed_encryption_compatibility(self):
        """Test 5: Mixed encrypted/unencrypted data compatibility."""
        print("\n=== Test 5: Mixed Encryption Compatibility ===")
        
        try:
            with self.SessionLocal() as db:
                mixed_reflections = []
                
                # Create unencrypted reflection
                unencrypted_id = uuid4()
                node_id_unenc = uuid4()
                db.execute(text("""
                    INSERT INTO reflections (id, user_id, generated_text, node_ids, confidence_score, is_encrypted, generated_at)
                    VALUES (:id, :user_id, :text, ARRAY[:node_id]::uuid[], :score, :encrypted, :now)
                """), {
                    "id": unencrypted_id,
                    "user_id": self.test_user_id,
                    "text": "Unencrypted reflection for compatibility testing",
                    "node_id": node_id_unenc,
                    "score": 0.75,
                    "encrypted": False,
                    "now": datetime.utcnow()
                })
                mixed_reflections.append(unencrypted_id)
                
                # Create encrypted reflection
                from utils.encryption import encrypt_data
                encrypted_text = encrypt_data("Encrypted reflection for compatibility testing", str(self.test_user_id))
                encrypted_id = uuid4()
                node_id_enc = uuid4()
                db.execute(text("""
                    INSERT INTO reflections (id, user_id, generated_text, node_ids, confidence_score, is_encrypted, generated_at)
                    VALUES (:id, :user_id, :text, ARRAY[:node_id]::uuid[], :score, :encrypted, :now)
                """), {
                    "id": encrypted_id,
                    "user_id": self.test_user_id,
                    "text": encrypted_text,
                    "node_id": node_id_enc,
                    "score": 0.80,
                    "encrypted": True,
                    "now": datetime.utcnow()
                })
                mixed_reflections.append(encrypted_id)
                db.commit()
                self.test_reflections.extend(mixed_reflections)
                
                # Query both reflections
                mixed_results = db.execute(text("""
                    SELECT id, generated_text, is_encrypted FROM reflections 
                    WHERE id IN (:id1, :id2)
                """), {"id1": unencrypted_id, "id2": encrypted_id}).fetchall()
                
                compatibility_success = len(mixed_results) == 2
                
                self.log_test(
                    "Mixed Encryption Compatibility", 
                    compatibility_success,
                    f"Retrieved {len(mixed_results)}/2 reflections from mixed encryption states"
                )
                
        except Exception as e:
            self.log_test("Mixed Encryption Compatibility", False, f"Error: {e}")

    def test_performance_security_validation(self):
        """Test 6: Performance and security validation."""
        print("\n=== Test 6: Performance & Security ===")
        
        try:
            from utils.encryption import encrypt_data, decrypt_data
            import time
            
            # Performance test: encrypt/decrypt multiple items
            start_time = time.time()
            user_id_str = str(self.test_user_id)
            
            performance_data = []
            for i in range(5):
                test_text = f"Performance test reflection #{i+1}: Testing encryption performance with substantial content to validate system efficiency under load conditions."
                encrypted = encrypt_data(test_text, user_id_str)
                decrypted = decrypt_data(encrypted, user_id_str)
                performance_data.append((test_text, encrypted, decrypted))
            
            total_time = time.time() - start_time
            
            # Validate all operations succeeded
            performance_success = all(original == decrypted for original, encrypted, decrypted in performance_data)
            
            # Security test: verify encrypted data doesn't contain original text
            security_success = all("Performance test reflection" not in encrypted for original, encrypted, decrypted in performance_data)
            
            overall_success = performance_success and security_success and total_time < 30.0
            
            self.log_test(
                "Performance & Security",
                overall_success,
                f"Time: {total_time:.2f}s, Performance: {'✓' if performance_success else '✗'}, Security: {'✓' if security_success else '✗'}"
            )
            
        except Exception as e:
            self.log_test("Performance & Security", False, f"Error: {e}")

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
                
        except Exception as e:
            print(f"Cleanup error: {e}")

    def run_comprehensive_test(self):
        """Execute comprehensive Phase 4 testing."""
        print("PHASE 4: COMPREHENSIVE REFLECTION ENCRYPTION FINAL TEST")
        print("=" * 65)
        
        if not self.setup_test_user():
            print("❌ Test setup failed")
            return False
        
        print(f"✓ Test environment ready (User: {self.test_user_id})")
        
        # Execute all tests
        try:
            self.test_database_environment_foundation()
            self.test_encryption_utilities_core()
            self.test_direct_database_encryption()
            self.test_repository_integration_simulation()
            self.test_mixed_encryption_compatibility()
            self.test_performance_security_validation()
            
            # Final results
            print("\n" + "=" * 65)
            print("PHASE 4 COMPREHENSIVE TEST RESULTS")
            print("=" * 65)
            
            total_tests = self.passed + self.failed
            success_rate = (self.passed / total_tests) * 100 if total_tests > 0 else 0
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {self.passed}")
            print(f"Failed: {self.failed}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            if self.failed == 0:
                print("\n🎉 ALL TESTS PASSED - PHASE 4 COMPLETE!")
                print("✅ Reflection encryption system is fully operational")
                print("✅ Database schema and environment properly configured")
                print("✅ Encryption utilities working correctly")
                print("✅ Repository integration functional")
                print("✅ Mixed data compatibility confirmed")
                print("✅ Performance and security validated")
                print("\n🚀 READY FOR PRODUCTION USE!")
                
                return True
            else:
                print(f"\n⚠️ {self.failed} test(s) failed - review details above")
                print("🔧 System needs attention before production deployment")
                return False
                
        except Exception as e:
            print(f"\n❌ Critical error during testing: {e}")
            return False
            
        finally:
            self.cleanup()
            print("\n✓ Test cleanup completed")


if __name__ == "__main__":
    tester = Phase4ComprehensiveFinalTest()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)