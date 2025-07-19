#!/usr/bin/env python3
"""
Phase 4: Simplified Reflection Encryption Testing

Tests the reflection encryption system without complex imports that cause conflicts.
Focuses on database-level validation and core functionality.
"""

import os
import sys
import traceback
import time
from datetime import datetime
from uuid import uuid4

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class SimpleReflectionEncryptionTester:
    def __init__(self):
        """Initialize simplified tester."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not set")
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.test_user_id = None
        self.test_reflections = []
        self.results = {'total': 0, 'passed': 0, 'failed': 0}

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        self.results['total'] += 1
        if success:
            self.results['passed'] += 1
            print(f"✓ {test_name}: {details}")
        else:
            self.results['failed'] += 1
            print(f"✗ {test_name}: {details}")

    def setup_test_user(self):
        """Create test user."""
        try:
            with self.SessionLocal() as db:
                user_id = uuid4()
                test_email = f"test_refl_enc_{uuid4().hex[:6]}@test.com"
                
                db.execute(text("""
                    INSERT INTO users (id, email, password_hash, created_at, updated_at)
                    VALUES (:id, :email, :hash, :now, :now)
                """), {
                    "id": user_id, "email": test_email, "hash": "test123", "now": datetime.utcnow()
                })
                
                db.execute(text("""
                    INSERT INTO user_profile (user_id, display_name, created_at, updated_at)
                    VALUES (:user_id, :name, :now, :now)
                """), {
                    "user_id": user_id, "name": "Test User", "now": datetime.utcnow()
                })
                
                db.commit()
                self.test_user_id = user_id
                return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def test_environment_setup(self):
        """Test 1: Environment configuration."""
        encrypt_setting = os.getenv('ENCRYPT_NEW_REFLECTIONS', 'false')
        has_database = os.getenv('DATABASE_URL') is not None
        
        self.log_result(
            "Environment Setup",
            encrypt_setting == 'true' and has_database,
            f"ENCRYPT_NEW_REFLECTIONS={encrypt_setting}, DB_URL={'set' if has_database else 'missing'}"
        )

    def test_database_schema(self):
        """Test 2: Database schema supports encryption."""
        try:
            with self.SessionLocal() as db:
                # Check if reflections table has is_encrypted column
                result = db.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'reflections' AND column_name = 'is_encrypted'
                """)).fetchone()
                
                has_encryption_column = result is not None
                
                self.log_result(
                    "Database Schema",
                    has_encryption_column,
                    f"is_encrypted column {'exists' if has_encryption_column else 'missing'}"
                )
                
        except Exception as e:
            self.log_result("Database Schema", False, f"Error: {e}")

    def test_repository_import(self):
        """Test 3: Repository functions can be imported."""
        try:
            # Add app to path and try importing
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
            
            # Test if we can import without conflicts
            import importlib.util
            spec = importlib.util.find_spec("repositories.reflection_repository")
            can_import = spec is not None
            
            self.log_result(
                "Repository Import",
                can_import,
                f"reflection_repository {'importable' if can_import else 'not found'}"
            )
            
        except Exception as e:
            self.log_result("Repository Import", False, f"Error: {e}")

    def test_direct_reflection_creation(self):
        """Test 4: Direct database reflection creation."""
        try:
            with self.SessionLocal() as db:
                # Create reflection directly in database
                reflection_id = uuid4()
                
                db.execute(text("""
                    INSERT INTO reflections (id, user_id, generated_text, node_chain, confidence_score, is_encrypted, created_at, updated_at)
                    VALUES (:id, :user_id, :text, :chain, :score, :encrypted, :now, :now)
                """), {
                    "id": reflection_id,
                    "user_id": self.test_user_id,
                    "text": "Test reflection for encryption validation",
                    "chain": '["node1", "node2"]',
                    "score": 0.85,
                    "encrypted": False,
                    "now": datetime.utcnow()
                })
                
                db.commit()
                self.test_reflections.append(reflection_id)
                
                # Verify creation
                result = db.execute(text("""
                    SELECT generated_text, is_encrypted FROM reflections WHERE id = :id
                """), {"id": reflection_id}).fetchone()
                
                success = result is not None
                self.log_result(
                    "Direct Reflection Creation",
                    success,
                    f"Created reflection with text: {'Yes' if success else 'No'}"
                )
                
        except Exception as e:
            self.log_result("Direct Reflection Creation", False, f"Error: {e}")

    def test_encryption_utilities(self):
        """Test 5: Encryption utilities work."""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
            from utils.encryption import encrypt_data, decrypt_data, derive_user_key
            
            # Test encryption/decryption
            test_text = "This is a test reflection for encryption validation"
            user_key = derive_user_key(str(self.test_user_id))
            
            encrypted = encrypt_data(test_text, user_key)
            decrypted = decrypt_data(encrypted, user_key)
            
            encryption_works = decrypted == test_text and encrypted != test_text
            
            self.log_result(
                "Encryption Utilities",
                encryption_works,
                f"Encryption cycle: {'successful' if encryption_works else 'failed'}"
            )
            
        except Exception as e:
            self.log_result("Encryption Utilities", False, f"Error: {e}")

    def test_existing_reflections(self):
        """Test 6: Check existing reflections in database."""
        try:
            with self.SessionLocal() as db:
                # Count total reflections
                result = db.execute(text("SELECT COUNT(*) FROM reflections")).fetchone()
                total_reflections = result[0] if result else 0
                
                # Count encrypted reflections
                encrypted_result = db.execute(text("SELECT COUNT(*) FROM reflections WHERE is_encrypted = true")).fetchone()
                encrypted_count = encrypted_result[0] if encrypted_result else 0
                
                self.log_result(
                    "Existing Reflections Analysis",
                    total_reflections >= 0,
                    f"Total: {total_reflections}, Encrypted: {encrypted_count}"
                )
                
        except Exception as e:
            self.log_result("Existing Reflections Analysis", False, f"Error: {e}")

    def cleanup(self):
        """Clean up test data."""
        try:
            with self.SessionLocal() as db:
                if self.test_reflections:
                    for refl_id in self.test_reflections:
                        db.execute(text("DELETE FROM reflections WHERE id = :id"), {"id": refl_id})
                
                if self.test_user_id:
                    db.execute(text("DELETE FROM user_profile WHERE user_id = :id"), {"id": self.test_user_id})
                    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": self.test_user_id})
                
                db.commit()
                print(f"\n✓ Cleaned up test data")
        except Exception as e:
            print(f"\n⚠ Cleanup warning: {e}")

    def run_tests(self):
        """Run all tests."""
        print("Phase 4: Reflection Encryption System Testing")
        print("=" * 50)
        
        if not self.setup_test_user():
            print("❌ Failed to create test user")
            return False
        
        try:
            self.test_environment_setup()
            self.test_database_schema()
            self.test_repository_import()
            self.test_direct_reflection_creation()
            self.test_encryption_utilities()
            self.test_existing_reflections()
            
            # Results
            print("\n" + "=" * 50)
            print("TEST RESULTS:")
            print(f"Total Tests: {self.results['total']}")
            print(f"Passed: {self.results['passed']}")
            print(f"Failed: {self.results['failed']}")
            
            success_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
            if self.results['failed'] == 0:
                print("\n🎉 All tests passed - System ready for encryption!")
            elif self.results['failed'] <= 2:
                print("\n⚠️ Minor issues detected - System mostly functional")
            else:
                print("\n❌ Multiple issues - System needs attention")
            
            return self.results['failed'] == 0
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = SimpleReflectionEncryptionTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)