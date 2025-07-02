"""
Migration script to add refresh_tokens table for JWT authentication.

This table will store refresh tokens to enable secure, long-lived user sessions
while maintaining the ability to revoke tokens when needed.
"""

import os
import psycopg2
from datetime import datetime

def execute_migration():
    """Execute the database migration to add the refresh_tokens table."""
    try:
        # Get database connection
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'refresh_tokens'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("refresh_tokens table already exists. Skipping migration.")
            return True
        
        # Create refresh_tokens table
        cursor.execute("""
            CREATE TABLE refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add indexes for performance
        cursor.execute("""
            CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
        """)
        cursor.execute("""
            CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
        """)
        cursor.execute("""
            CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
        """)
        
        # Commit the changes
        conn.commit()
        print("✓ refresh_tokens table created successfully")
        print("✓ Indexes created for optimal performance")
        
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
    print("Running migration: Add refresh_tokens table")
    print("=" * 50)
    
    success = execute_migration()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Please check the error messages above.")