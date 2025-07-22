"""
Migration script to add encryption support to sessions table.

This migration adds the is_encrypted column to track encryption status
and creates the migration_errors table for tracking encryption failures.
"""

import os
import psycopg2
from datetime import datetime

def execute_migration():
    """Execute the database migration to add encryption support."""
    try:
        # Get database connection
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Adding encryption support to sessions table...")
        
        # Add is_encrypted column to sessions table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sessions' 
            AND column_name = 'is_encrypted'
        """)
        
        if not cursor.fetchone():
            print("Adding is_encrypted column to sessions table...")
            cursor.execute("""
                ALTER TABLE sessions 
                ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE
            """)
            print("✓ is_encrypted column added to sessions table")
        else:
            print("is_encrypted column already exists in sessions table")
        
        # Create migration_errors table
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'migration_errors'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Creating migration_errors table...")
            cursor.execute("""
                CREATE TABLE migration_errors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    session_id UUID NOT NULL,
                    error_type VARCHAR(100) NOT NULL,
                    error_message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Add indexes for performance
            cursor.execute("""
                CREATE INDEX idx_migration_errors_user_id ON migration_errors(user_id);
            """)
            cursor.execute("""
                CREATE INDEX idx_migration_errors_session_id ON migration_errors(session_id);
            """)
            cursor.execute("""
                CREATE INDEX idx_migration_errors_created_at ON migration_errors(created_at);
            """)
            
            print("✓ migration_errors table created with indexes")
        else:
            print("migration_errors table already exists")
        
        # Commit the changes
        conn.commit()
        print("✓ Database migration completed successfully")
        
        return True
        
    except Exception as e:
        print(f"ERROR during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Running migration: Add encryption support")
    print("=" * 50)
    
    success = execute_migration()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Please check the error messages above.")