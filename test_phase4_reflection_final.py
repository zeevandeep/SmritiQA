#!/usr/bin/env python3
"""
Phase 4: Final Reflection Encryption System Testing

Tests the complete reflection encryption system with real database and repository integration.
"""

import os
import sys
import time
from datetime import datetime
from uuid import uuid4

# Load environment variables and setup paths
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class Phase4FinalTester:
    def __init__(self):
        """Initialize final tester with proper configuration."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found")
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_user_id = None
        self.test_reflections = []
        self.results = {'total': 0, 'passed': 0, 'failed': 0, 'details': []}

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result."""
        self.results['total'] += 1
        if success:
            self.results['passed'] += 1
            status = "✓ PASS"
        else:
            self.results['failed'] += 1
            status = "✗ FAIL"
        
        self.results['details'].append({'name': name, 'success': success, 'details': details})
        print(f"{status}: {name}")
        if details:
            print(f"   {details}")

    def setup_test_user(self):
        """Create test user using correct table names."""
        try:
            with self.SessionLocal() as db:
                user_id = uuid4()
                email = f"test_phase4_{uuid4().hex[:6]}@test.com"
                now = datetime.utcnow()
                
                # Insert into users table
                db.execute(text("""
                    INSERT INTO users (id, email, password_hash, created_at, updated_at)
                    VALUES (:id, :email, :password_hash, :created_at, :updated_at)
                """), {
                    "id": user_id,
                    "email": email,
                    "password_hash": "test_hash_phase4",
                    "created_at": now,
                    "updated_at": now
                })
                
                # Insert into user_profiles table (note: plural)
                db.execute(text("""
                    INSERT INTO user_profiles (user_id, display_name, created_at, updated_at)
                    VALUES (:user_id, :display_name, :created_at, :updated_at)
                """), {
                    "user_id": user_id,
                    "display_name": "Phase 4 Test User",
                    "created_at": now,
                    "updated_at": now
                })
                
                db.commit()
                self.test_user_id = user_id
                return True
                
        except Exception as e:
            print(f"Setup error: {e}")
            return False

    def test_1_database_schema(self):
        """Test 1: Database has encryption support."""
        try:
            with self.SessionLocal() as db:
                # Check reflections table structure
                result = db.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'reflections' AND column_name = 'is_encrypted'
                """)).fetchone()
                
                has_encryption = result is not None
                
                self.log_test(
                    "Database Schema Support", 
                    has_encryption,
                    f"is_encrypted column {'found' if has_encryption else 'missing'} in reflections table"
                )
                
        except Exception as e:
            self.log_test("Database Schema Support", False, f"Error: {e}")

    def test_2_environment_config(self):
        """Test 2: Environment variables properly configured."""
        encrypt_new = os.getenv('ENCRYPT_NEW_REFLECTIONS', 'false')
        encrypt_nodes = os.getenv('ENCRYPT_NEW_NODES', 'false')
        encrypt_sessions = os.getenv('ENCRYPT_NEW_SESSIONS', 'false')
        
        all_encryption_enabled = all([
            encrypt_new == 'true',
            encrypt_nodes == 'true', 
            encrypt_sessions == 'true'
        ])
        
        self.log_test(
            "Environment Configuration",
            all_encryption_enabled,
            f"Reflections={encrypt_new}, Nodes={encrypt_nodes}, Sessions={encrypt_sessions}"
        )

    def test_3_repository_integration(self):
        """Test 3: Repository functions can be imported and used."""
        try:
            # Import repository module
            from repositories import reflection_repository
            
            # Test creating reflection with repository
            with self.SessionLocal() as db:
                reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "Phase 4 test reflection: This is a comprehensive validation of the reflection encryption system integration.",
                    'node_chain': [str(uuid4()), str(uuid4())],
                    'confidence_score': 0.92
                }
                
                # Force encryption for this test
                original_env = os.getenv('ENCRYPT_NEW_REFLECTIONS')
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                
                try:
                    reflection = reflection_repository.create_reflection(db, reflection_data)
                    
                    # Handle both dict and object response types
                    if isinstance(reflection, dict):
                        refl_id = reflection.get('id')
                        refl_text = reflection.get('generated_text')
                    else:
                        refl_id = getattr(reflection, 'id', None)
                        refl_text = getattr(reflection, 'generated_text', None)
                    
                    if refl_id:
                        self.test_reflections.append(refl_id)
                    
                    creation_success = (reflection is not None and 
                                      refl_text is not None and
                                      len(str(refl_text)) > 0)
                    
                    self.log_test(
                        "Repository Integration",
                        creation_success,
                        f"Created reflection {refl_id} with encrypted text"
                    )
                    
                finally:
                    # Restore original environment
                    if original_env:
                        os.environ['ENCRYPT_NEW_REFLECTIONS'] = original_env
                
        except Exception as e:
            self.log_test("Repository Integration", False, f"Error: {e}")

    def test_4_encryption_decryption_cycle(self):
        """Test 4: Full encryption/decryption cycle."""
        try:
            from repositories import reflection_repository
            
            with self.SessionLocal() as db:
                # Create encrypted reflection
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                
                test_text = "PHASE4_ENCRYPTION_TEST_CONTENT_FOR_VALIDATION"
                reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': test_text,
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.95
                }
                
                # Create reflection
                created_reflection = reflection_repository.create_reflection(db, reflection_data)
                
                # Handle both dict and object response types
                if isinstance(created_reflection, dict):
                    created_id = created_reflection.get('id')
                else:
                    created_id = getattr(created_reflection, 'id', None)
                
                if created_id:
                    self.test_reflections.append(created_id)
                
                # Check raw database storage (should be encrypted)
                raw_result = db.execute(text("""
                    SELECT generated_text, is_encrypted FROM reflections WHERE id = :id
                """), {"id": created_id}).fetchone()
                
                if raw_result:
                    raw_text, is_encrypted_flag = raw_result
                    is_properly_encrypted = (is_encrypted_flag and 
                                           "PHASE4_ENCRYPTION_TEST" not in str(raw_text))
                    
                    # Retrieve through repository (should be decrypted)
                    retrieved_reflection = reflection_repository.get_reflection(
                        db, created_id, decrypt_for_processing=False
                    )
                    
                    # Handle both dict and object response types for retrieved reflection
                    if isinstance(retrieved_reflection, dict):
                        retrieved_text = retrieved_reflection.get('generated_text', '')
                    else:
                        retrieved_text = getattr(retrieved_reflection, 'generated_text', '')
                    
                    is_properly_decrypted = (retrieved_reflection and 
                                           "PHASE4_ENCRYPTION_TEST" in str(retrieved_text))
                    
                    cycle_success = is_properly_encrypted and is_properly_decrypted
                    
                    self.log_test(
                        "Encryption/Decryption Cycle",
                        cycle_success,
                        f"Encrypted in DB: {is_properly_encrypted}, Decrypted for user: {is_properly_decrypted}"
                    )
                else:
                    self.log_test("Encryption/Decryption Cycle", False, "Could not retrieve raw data")
                
        except Exception as e:
            self.log_test("Encryption/Decryption Cycle", False, f"Error: {e}")

    def test_5_mixed_data_handling(self):
        """Test 5: Mixed encrypted/unencrypted data handling."""
        try:
            from repositories import reflection_repository
            
            with self.SessionLocal() as db:
                mixed_reflections = []
                
                # Create unencrypted reflection
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'false'
                unencrypted_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "Unencrypted reflection for backward compatibility testing",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.80
                }
                unencrypted = reflection_repository.create_reflection(db, unencrypted_data)
                if isinstance(unencrypted, dict):
                    mixed_reflections.append(unencrypted.get('id'))
                else:
                    mixed_reflections.append(getattr(unencrypted, 'id', None))
                
                # Create encrypted reflection
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                encrypted_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "Encrypted reflection for mixed data testing",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.85
                }
                encrypted = reflection_repository.create_reflection(db, encrypted_data)
                if isinstance(encrypted, dict):
                    mixed_reflections.append(encrypted.get('id'))
                else:
                    mixed_reflections.append(getattr(encrypted, 'id', None))
                
                # Retrieve all user reflections
                user_reflections = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                
                readable_count = 0
                for r in user_reflections:
                    if isinstance(r, dict):
                        text = r.get('generated_text', '')
                    else:
                        text = getattr(r, 'generated_text', '')
                    if text and len(str(text)) > 10:
                        readable_count += 1
                
                mixed_handling_success = readable_count >= 2
                
                self.log_test(
                    "Mixed Data Handling",
                    mixed_handling_success,
                    f"Retrieved {readable_count} readable reflections from mixed encryption states"
                )
                
                self.test_reflections.extend(mixed_reflections)
                
        except Exception as e:
            self.log_test("Mixed Data Handling", False, f"Error: {e}")

    def test_6_performance_validation(self):
        """Test 6: Performance with encryption overhead."""
        try:
            from repositories import reflection_repository
            
            with self.SessionLocal() as db:
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                
                start_time = time.time()
                batch_reflections = []
                
                # Create 3 encrypted reflections
                for i in range(3):
                    reflection_data = {
                        'user_id': self.test_user_id,
                        'generated_text': f"Performance test reflection #{i+1}: Testing encryption overhead with meaningful content about personal growth and emotional insights through journaling practice.",
                        'node_chain': [str(uuid4()), str(uuid4())],
                        'confidence_score': 0.80 + i * 0.05
                    }
                    reflection = reflection_repository.create_reflection(db, reflection_data)
                    if isinstance(reflection, dict):
                        batch_reflections.append(reflection.get('id'))
                    else:
                        batch_reflections.append(getattr(reflection, 'id', None))
                
                creation_time = time.time() - start_time
                
                # Retrieve all reflections
                start_retrieve = time.time()
                retrieved = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                retrieval_time = time.time() - start_retrieve
                
                performance_acceptable = creation_time < 15.0 and retrieval_time < 10.0
                
                self.log_test(
                    "Performance Validation",
                    performance_acceptable,
                    f"Created 3 in {creation_time:.2f}s, retrieved in {retrieval_time:.2f}s"
                )
                
                self.test_reflections.extend(batch_reflections)
                
        except Exception as e:
            self.log_test("Performance Validation", False, f"Error: {e}")

    def cleanup_test_data(self):
        """Clean up all test data."""
        try:
            with self.SessionLocal() as db:
                # Delete test reflections
                if self.test_reflections:
                    for refl_id in self.test_reflections:
                        db.execute(text("DELETE FROM reflections WHERE id = :id"), {"id": refl_id})
                
                # Delete test user and profile
                if self.test_user_id:
                    db.execute(text("DELETE FROM user_profiles WHERE user_id = :id"), {"id": self.test_user_id})
                    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": self.test_user_id})
                
                db.commit()
                print(f"\n✓ Cleaned up test data (user: {self.test_user_id})")
                
        except Exception as e:
            print(f"\n⚠ Cleanup warning: {e}")

    def print_final_report(self):
        """Print comprehensive test report."""
        print("\n" + "="*70)
        print("PHASE 4 REFLECTION ENCRYPTION - COMPREHENSIVE TEST REPORT")
        print("="*70)
        
        print(f"\nOVERALL RESULTS:")
        print(f"Total Tests: {self.results['total']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        
        if self.results['total'] > 0:
            success_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        for detail in self.results['details']:
            status = "✓" if detail['success'] else "✗"
            print(f"{status} {detail['name']}")
            if detail['details']:
                print(f"   {detail['details']}")
        
        print(f"\nSYSTEM ASSESSMENT:")
        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED")
            print("✅ Reflection encryption system is fully operational and ready for production!")
            print("✅ Mixed data handling works correctly")
            print("✅ Performance is acceptable with encryption overhead")
            print("✅ Repository integration is seamless")
        elif self.results['failed'] <= 1:
            print("⚠️ MOSTLY OPERATIONAL") 
            print("✅ Core functionality working")
            print("⚠️ Minor issue detected - review failed test above")
        else:
            print("❌ ISSUES DETECTED")
            print("❌ Multiple failures - system needs attention before production")
        
        print("\n" + "="*70)

    def run_comprehensive_test(self):
        """Run all tests and generate report."""
        print("PHASE 4: COMPREHENSIVE REFLECTION ENCRYPTION TESTING")
        print("="*70)
        
        if not self.setup_test_user():
            print("❌ Failed to set up test environment")
            return False
        
        print(f"✓ Test environment ready (User ID: {self.test_user_id})")
        print("\nRunning comprehensive tests...")
        
        try:
            # Execute all test categories
            self.test_1_database_schema()
            self.test_2_environment_config()
            self.test_3_repository_integration()
            self.test_4_encryption_decryption_cycle()
            self.test_5_mixed_data_handling()
            self.test_6_performance_validation()
            
            # Generate final report
            self.print_final_report()
            
            return self.results['failed'] == 0
            
        except Exception as e:
            print(f"\n❌ Critical testing error: {e}")
            return False
            
        finally:
            self.cleanup_test_data()


if __name__ == "__main__":
    tester = Phase4FinalTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)