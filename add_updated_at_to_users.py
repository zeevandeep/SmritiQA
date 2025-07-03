"""
Script to add updated_at column to the users table.

This migration adds the updated_at field to support Google OAuth user creation
and general user record tracking.
"""
import os
import psycopg2
from urllib.parse import urlparse

def execute_migration():
    """Execute the database migration to add the updated_at column."""
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    conn = None
    cursor = None
    
    try:
        # Parse database URL
        url = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Remove leading slash
        )
        
        cursor = conn.cursor()
        
        print("Checking if updated_at column exists in users table...")
        
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """)
        
        if cursor.fetchone():
            print("updated_at column already exists in users table")
            return True
        
        print("Adding updated_at column to users table...")
        
        # Add the updated_at column with default value
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
        """)
        
        # Update existing records to have updated_at = created_at
        cursor.execute("""
            UPDATE users 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """)
        
        # Commit the changes
        conn.commit()
        
        print("Successfully added updated_at column to users table")
        print("Set existing records' updated_at to their created_at timestamp")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"Verification: Column {result[0]} added with type {result[1]}, nullable: {result[2]}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to add updated_at column: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting migration to add updated_at column to users table...")
    success = execute_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        exit(1)