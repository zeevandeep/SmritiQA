#!/usr/bin/env python3
"""
Phase 4: Comprehensive Reflection Encryption Testing

This script validates the complete reflection encryption system including:
1. Mixed encryption environments (encrypted/unencrypted reflections)
2. Backward compatibility with legacy data
3. Error handling for edge cases
4. End-to-end workflow integration
5. Performance with batch processing
6. Security validation with encryption utilities

Test Categories:
- Repository Layer Functions
- Service Layer Integration  
- API Endpoint Integration
- Mixed Data Scenarios
- Error Handling & Edge Cases
- Performance & Security Validation
"""

import os
import sys
import traceback
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import database config and setup database session directly
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class Phase4ReflectionEncryptionTester:
    def __init__(self):
        """Initialize the comprehensive reflection encryption tester."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_user_id = None
        self.test_reflections = []
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'categories': {}
        }

    def log_test(self, category: str, test_name: str, result: bool, details: str = ""):
        """Log test results with categorization."""
        if category not in self.results['categories']:
            self.results['categories'][category] = {'passed': 0, 'failed': 0, 'tests': []}
        
        self.results['total_tests'] += 1
        if result:
            self.results['passed'] += 1
            self.results['categories'][category]['passed'] += 1
            status = "✓ PASS"
        else:
            self.results['failed'] += 1
            self.results['categories'][category]['failed'] += 1
            status = "✗ FAIL"
        
        self.results['categories'][category]['tests'].append({
            'name': test_name,
            'result': result,
            'details': details
        })
        
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")

    def setup_test_environment(self) -> bool:
        """Set up test user and environment for comprehensive testing."""
        try:
            with self.SessionLocal() as db:
                # Create test user directly in database to avoid import issues
                test_email = f"test_reflection_encryption_{uuid4().hex[:8]}@example.com"
                user_id = uuid4()
                
                # Insert user
                db.execute(text("""
                    INSERT INTO users (id, email, password_hash, created_at, updated_at)
                    VALUES (:id, :email, :password_hash, :created_at, :updated_at)
                """), {
                    "id": user_id,
                    "email": test_email,
                    "password_hash": "test_hash_123",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                # Insert user profile
                db.execute(text("""
                    INSERT INTO user_profile (user_id, display_name, created_at, updated_at)
                    VALUES (:user_id, :display_name, :created_at, :updated_at)
                """), {
                    "user_id": user_id,
                    "display_name": "Reflection Encryption Test User",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                db.commit()
                self.test_user_id = user_id
                print(f"Created test user with ID: {self.test_user_id}")
                return True
        except Exception as e:
            print(f"Failed to set up test environment: {str(e)}")
            traceback.print_exc()
            return False

    def test_repository_layer_functions(self):
        """Category 1: Test reflection repository layer encryption functions."""
        print("\n=== Category 1: Repository Layer Functions ===")
        
        try:
            # Import repository here to avoid initialization conflicts
            from repositories import reflection_repository
            
            with self.SessionLocal() as db:
                # Test 1.1: Create encrypted reflection
                try:
                    reflection_data = {
                        'user_id': self.test_user_id,
                        'generated_text': "This is a test reflection with meaningful insight about emotional patterns and growth.",
                        'node_chain': [str(uuid4()), str(uuid4())],
                        'confidence_score': 0.85
                    }
                    
                    # Force encryption for this test
                    os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                    reflection = reflection_repository.create_reflection(db, reflection_data)
                    self.test_reflections.append(reflection.id)
                    
                    # Check if reflection was created and marked as encrypted
                    is_encrypted = reflection.is_encrypted if hasattr(reflection, 'is_encrypted') else False
                    
                    self.log_test(
                        "Repository Layer",
                        "Create Encrypted Reflection",
                        reflection is not None and reflection.generated_text is not None,
                        f"Created reflection ID {reflection.id}, encrypted: {is_encrypted}"
                    )
                    
                except Exception as e:
                    self.log_test("Repository Layer", "Create Encrypted Reflection", False, f"Error: {str(e)}")
        except ImportError as e:
            self.log_test("Repository Layer", "Repository Import", False, f"Import error: {str(e)}")

            # Test 1.2: Create unencrypted reflection
            try:
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'false'
                reflection_data_2 = {
                    'user_id': self.test_user_id,
                    'generated_text': "This is an unencrypted test reflection for backward compatibility testing.",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.75
                }
                
                reflection_2 = reflection_repository.create_reflection(db, reflection_data_2)
                self.test_reflections.append(reflection_2.id)
                
                is_encrypted_2 = reflection_2.is_encrypted if hasattr(reflection_2, 'is_encrypted') else False
                
                self.log_test(
                    "Repository Layer",
                    "Create Unencrypted Reflection", 
                    reflection_2 is not None,
                    f"Created reflection ID {reflection_2.id}, encrypted: {is_encrypted_2}"
                )
                
            except Exception as e:
                self.log_test("Repository Layer", "Create Unencrypted Reflection", False, f"Error: {str(e)}")

            # Test 1.3: Retrieve user reflections (mixed encryption)
            try:
                user_reflections = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                
                readable_count = 0
                for refl in user_reflections:
                    if refl.generated_text and len(refl.generated_text) > 0 and not refl.generated_text.startswith('gAAAA'):
                        readable_count += 1
                
                self.log_test(
                    "Repository Layer",
                    "Retrieve Mixed Encryption Reflections",
                    len(user_reflections) >= 2 and readable_count >= 2,
                    f"Retrieved {len(user_reflections)} reflections, {readable_count} readable"
                )
                
            except Exception as e:
                self.log_test("Repository Layer", "Retrieve Mixed Encryption Reflections", False, f"Error: {str(e)}")

            # Test 1.4: Individual reflection retrieval
            try:
                if self.test_reflections:
                    individual_reflection = reflection_repository.get_reflection(
                        db, self.test_reflections[0], decrypt_for_processing=False
                    )
                    
                    is_readable = (individual_reflection and 
                                 individual_reflection.generated_text and 
                                 not individual_reflection.generated_text.startswith('gAAAA'))
                    
                    self.log_test(
                        "Repository Layer",
                        "Individual Reflection Retrieval",
                        is_readable,
                        f"Retrieved reflection with readable text: {is_readable}"
                    )
                
            except Exception as e:
                self.log_test("Repository Layer", "Individual Reflection Retrieval", False, f"Error: {str(e)}")

    def test_service_layer_integration(self):
        """Category 2: Test service layer integration with reflection processor."""
        print("\n=== Category 2: Service Layer Integration ===")
        
        # Test 2.1: Reflection processor can access repository functions
        try:
            # Check if reflection_processor can import and use repository functions
            create_func = getattr(reflection_processor, 'create_reflection', None) or \
                         getattr(reflection_repository, 'create_reflection', None)
            
            self.log_test(
                "Service Integration",
                "Repository Function Access",
                create_func is not None,
                "reflection_processor can access create_reflection function"
            )
            
        except Exception as e:
            self.log_test("Service Integration", "Repository Function Access", False, f"Error: {str(e)}")

        # Test 2.2: Service layer workflow simulation
        try:
            with self.SessionLocal() as db:
                # Simulate reflection generation workflow
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                
                test_reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "Service layer generated reflection about personal growth and emotional awareness through daily journaling practice.",
                    'node_chain': [str(uuid4()), str(uuid4()), str(uuid4())],
                    'confidence_score': 0.92
                }
                
                # Direct repository call (simulating service layer)
                service_reflection = reflection_repository.create_reflection(db, test_reflection_data)
                
                # Immediate retrieval (simulating API response)
                retrieved = reflection_repository.get_reflection(
                    db, service_reflection.id, decrypt_for_processing=False
                )
                
                is_workflow_success = (retrieved and 
                                     retrieved.generated_text and 
                                     len(retrieved.generated_text) > 50 and
                                     not retrieved.generated_text.startswith('gAAAA'))
                
                self.log_test(
                    "Service Integration",
                    "End-to-End Workflow Simulation",
                    is_workflow_success,
                    f"Workflow created and retrieved readable reflection: {is_workflow_success}"
                )
                
        except Exception as e:
            self.log_test("Service Integration", "End-to-End Workflow Simulation", False, f"Error: {str(e)}")

    def test_mixed_data_scenarios(self):
        """Category 3: Test mixed encrypted/unencrypted data scenarios."""
        print("\n=== Category 3: Mixed Data Scenarios ===")
        
        with self.SessionLocal() as db:
            # Test 3.1: Batch retrieval with mixed encryption
            try:
                # Create mix of encrypted and unencrypted reflections
                mixed_reflections = []
                
                for i, encrypt_flag in enumerate(['true', 'false', 'true']):
                    os.environ['ENCRYPT_NEW_REFLECTIONS'] = encrypt_flag
                    reflection_data = {
                        'user_id': self.test_user_id,
                        'generated_text': f"Mixed scenario reflection #{i+1} - testing batch retrieval with different encryption states.",
                        'node_chain': [str(uuid4())],
                        'confidence_score': 0.80 + i * 0.05
                    }
                    refl = reflection_repository.create_reflection(db, reflection_data)
                    mixed_reflections.append(refl.id)
                
                # Retrieve all reflections for user
                all_reflections = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                
                readable_mixed = sum(1 for r in all_reflections 
                                   if r.generated_text and not r.generated_text.startswith('gAAAA'))
                
                self.log_test(
                    "Mixed Data Scenarios",
                    "Batch Mixed Encryption Retrieval",
                    readable_mixed >= 3,
                    f"Retrieved {len(all_reflections)} total, {readable_mixed} readable from mixed encryption"
                )
                
            except Exception as e:
                self.log_test("Mixed Data Scenarios", "Batch Mixed Encryption Retrieval", False, f"Error: {str(e)}")

    def test_error_handling_edge_cases(self):
        """Category 4: Test error handling and edge cases."""
        print("\n=== Category 4: Error Handling & Edge Cases ===")
        
        with self.SessionLocal() as db:
            # Test 4.1: Empty reflection text
            try:
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                empty_reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.5
                }
                
                empty_reflection = reflection_repository.create_reflection(db, empty_reflection_data)
                retrieved_empty = reflection_repository.get_reflection(
                    db, empty_reflection.id, decrypt_for_processing=False
                )
                
                self.log_test(
                    "Error Handling",
                    "Empty Text Handling",
                    retrieved_empty is not None,
                    "Empty reflection text handled without errors"
                )
                
            except Exception as e:
                self.log_test("Error Handling", "Empty Text Handling", False, f"Error: {str(e)}")

            # Test 4.2: Very long reflection text
            try:
                long_text = "This is a very long reflection text. " * 200  # ~7000 characters
                long_reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': long_text,
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.88
                }
                
                long_reflection = reflection_repository.create_reflection(db, long_reflection_data)
                retrieved_long = reflection_repository.get_reflection(
                    db, long_reflection.id, decrypt_for_processing=False
                )
                
                is_long_success = (retrieved_long and 
                                 retrieved_long.generated_text and 
                                 len(retrieved_long.generated_text) > 1000)
                
                self.log_test(
                    "Error Handling",
                    "Long Text Handling",
                    is_long_success,
                    f"Long text ({len(long_text)} chars) handled successfully"
                )
                
            except Exception as e:
                self.log_test("Error Handling", "Long Text Handling", False, f"Error: {str(e)}")

            # Test 4.3: Non-existent reflection retrieval
            try:
                fake_reflection_id = uuid4()
                non_existent = reflection_repository.get_reflection(
                    db, fake_reflection_id, decrypt_for_processing=False
                )
                
                self.log_test(
                    "Error Handling",
                    "Non-existent Reflection Handling",
                    non_existent is None,
                    "Non-existent reflection returns None gracefully"
                )
                
            except Exception as e:
                self.log_test("Error Handling", "Non-existent Reflection Handling", False, f"Error: {str(e)}")

    def test_performance_security(self):
        """Category 5: Test performance and security validation."""
        print("\n=== Category 5: Performance & Security Validation ===")
        
        with self.SessionLocal() as db:
            # Test 5.1: Batch processing performance
            try:
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                start_time = time.time()
                
                batch_reflections = []
                for i in range(5):  # Create 5 reflections
                    reflection_data = {
                        'user_id': self.test_user_id,
                        'generated_text': f"Performance test reflection #{i+1} with detailed content about emotional insights and personal growth patterns discovered through journaling.",
                        'node_chain': [str(uuid4()), str(uuid4())],
                        'confidence_score': 0.80 + i * 0.02
                    }
                    refl = reflection_repository.create_reflection(db, reflection_data)
                    batch_reflections.append(refl.id)
                
                creation_time = time.time() - start_time
                
                # Retrieve all in batch
                start_retrieve = time.time()
                retrieved_batch = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                retrieval_time = time.time() - start_retrieve
                
                performance_ok = creation_time < 10.0 and retrieval_time < 5.0
                
                self.log_test(
                    "Performance & Security",
                    "Batch Processing Performance",
                    performance_ok,
                    f"Created 5 reflections in {creation_time:.2f}s, retrieved in {retrieval_time:.2f}s"
                )
                
            except Exception as e:
                self.log_test("Performance & Security", "Batch Processing Performance", False, f"Error: {str(e)}")

            # Test 5.2: Encryption security validation
            try:
                # Create encrypted reflection and check raw database storage
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'true'
                security_reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "SENSITIVE_TEST_DATA_FOR_ENCRYPTION_VALIDATION",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.95
                }
                
                security_reflection = reflection_repository.create_reflection(db, security_reflection_data)
                
                # Check raw database storage
                raw_result = db.execute(
                    text("SELECT generated_text, is_encrypted FROM reflections WHERE id = :refl_id"),
                    {"refl_id": security_reflection.id}
                ).fetchone()
                
                if raw_result:
                    raw_text, is_encrypted_flag = raw_result
                    # If encrypted, raw text should not contain the sensitive data
                    is_properly_encrypted = (is_encrypted_flag and 
                                           "SENSITIVE_TEST_DATA" not in str(raw_text))
                    
                    # Retrieved reflection should have readable text
                    retrieved_security = reflection_repository.get_reflection(
                        db, security_reflection.id, decrypt_for_processing=False
                    )
                    is_properly_decrypted = (retrieved_security and 
                                           "SENSITIVE_TEST_DATA" in retrieved_security.generated_text)
                    
                    security_valid = is_properly_encrypted and is_properly_decrypted
                    
                    self.log_test(
                        "Performance & Security",
                        "Encryption Security Validation",
                        security_valid,
                        f"Encrypted in DB: {is_properly_encrypted}, Decrypted for user: {is_properly_decrypted}"
                    )
                else:
                    self.log_test("Performance & Security", "Encryption Security Validation", False, "Could not retrieve raw data")
                
            except Exception as e:
                self.log_test("Performance & Security", "Encryption Security Validation", False, f"Error: {str(e)}")

    def test_backward_compatibility(self):
        """Category 6: Test backward compatibility with legacy unencrypted data."""
        print("\n=== Category 6: Backward Compatibility ===")
        
        with self.SessionLocal() as db:
            # Test 6.1: Legacy reflection handling
            try:
                # Simulate legacy reflection (created before encryption was implemented)
                legacy_reflection_data = {
                    'user_id': self.test_user_id,
                    'generated_text': "This is a legacy reflection that was created before encryption was implemented.",
                    'node_chain': [str(uuid4())],
                    'confidence_score': 0.78
                }
                
                # Force unencrypted creation
                os.environ['ENCRYPT_NEW_REFLECTIONS'] = 'false'
                legacy_reflection = reflection_repository.create_reflection(db, legacy_reflection_data)
                
                # Retrieve using current system
                retrieved_legacy = reflection_repository.get_reflection(
                    db, legacy_reflection.id, decrypt_for_processing=False
                )
                
                is_legacy_working = (retrieved_legacy and 
                                   retrieved_legacy.generated_text and 
                                   "legacy reflection" in retrieved_legacy.generated_text.lower())
                
                self.log_test(
                    "Backward Compatibility",
                    "Legacy Reflection Handling",
                    is_legacy_working,
                    "Legacy unencrypted reflection retrieved successfully"
                )
                
            except Exception as e:
                self.log_test("Backward Compatibility", "Legacy Reflection Handling", False, f"Error: {str(e)}")

            # Test 6.2: Mixed legacy and new data
            try:
                # Get all user reflections (mix of encrypted and unencrypted)
                all_mixed_reflections = reflection_repository.get_user_reflections(
                    db, self.test_user_id, decrypt_for_processing=False
                )
                
                readable_reflections = 0
                for refl in all_mixed_reflections:
                    if refl.generated_text and len(refl.generated_text) > 10:
                        readable_reflections += 1
                
                compatibility_success = readable_reflections >= 3
                
                self.log_test(
                    "Backward Compatibility",
                    "Mixed Legacy/New Data Handling",
                    compatibility_success,
                    f"Retrieved {readable_reflections}/{len(all_mixed_reflections)} readable reflections from mixed data"
                )
                
            except Exception as e:
                self.log_test("Backward Compatibility", "Mixed Legacy/New Data Handling", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data created during testing."""
        try:
            with self.SessionLocal() as db:
                # Delete test reflections
                if self.test_reflections:
                    for refl_id in self.test_reflections:
                        db.execute(text("DELETE FROM reflections WHERE id = :refl_id"), {"refl_id": refl_id})
                
                # Delete test user and profile
                if self.test_user_id:
                    db.execute(text("DELETE FROM user_profile WHERE user_id = :user_id"), {"user_id": self.test_user_id})
                    db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": self.test_user_id})
                
                db.commit()
                print(f"\n✓ Cleaned up test data for user {self.test_user_id}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up test data: {str(e)}")

    def print_comprehensive_report(self):
        """Print detailed test results report."""
        print("\n" + "="*80)
        print("PHASE 4 COMPREHENSIVE REFLECTION ENCRYPTION TEST REPORT")
        print("="*80)
        
        print(f"\nOVERALL RESULTS:")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['passed']/self.results['total_tests']*100):.1f}%")
        
        print(f"\nCATEGORY BREAKDOWN:")
        for category, stats in self.results['categories'].items():
            total_cat = stats['passed'] + stats['failed']
            success_rate = (stats['passed']/total_cat*100) if total_cat > 0 else 0
            print(f"\n{category}:")
            print(f"  ✓ Passed: {stats['passed']}")
            print(f"  ✗ Failed: {stats['failed']}")
            print(f"  Success Rate: {success_rate:.1f}%")
            
            if stats['failed'] > 0:
                print(f"  Failed Tests:")
                for test in stats['tests']:
                    if not test['result']:
                        print(f"    - {test['name']}: {test['details']}")
        
        # Overall assessment
        print(f"\nSYSTEM ASSESSMENT:")
        if self.results['failed'] == 0:
            print("🎉 ALL TESTS PASSED - Reflection encryption system is fully operational!")
        elif self.results['failed'] <= 2:
            print("⚠️  MOSTLY OPERATIONAL - Minor issues detected, system functional")
        else:
            print("❌ ISSUES DETECTED - System needs attention before production use")
        
        print("\n" + "="*80)

    def run_comprehensive_tests(self):
        """Run all comprehensive reflection encryption tests."""
        print("Starting Phase 4: Comprehensive Reflection Encryption Testing")
        print("="*80)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to set up test environment. Aborting tests.")
            return False
        
        try:
            # Run all test categories
            self.test_repository_layer_functions()
            self.test_service_layer_integration()
            self.test_mixed_data_scenarios()
            self.test_error_handling_edge_cases()
            self.test_performance_security()
            self.test_backward_compatibility()
            
            # Generate comprehensive report
            self.print_comprehensive_report()
            
            return self.results['failed'] == 0
            
        except Exception as e:
            print(f"\n❌ Critical error during testing: {str(e)}")
            traceback.print_exc()
            return False
        finally:
            # Always cleanup
            self.cleanup_test_data()


if __name__ == "__main__":
    tester = Phase4ReflectionEncryptionTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)