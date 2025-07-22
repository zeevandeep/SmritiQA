"""
Migration script to add encryption support to nodes table.

This migration adds the is_encrypted column to track encryption status
and updates the .env file to set ENCRYPT_NEW_NODES=true.
"""

import os
import psycopg2
from datetime import datetime

def update_env_file():
    """Add ENCRYPT_NEW_NODES=true to .env file if not already present."""
    env_file_path = ".env"
    
    if not os.path.exists(env_file_path):
        print("WARNING: .env file not found, skipping environment variable update")
        return False
    
    # Read current .env file
    with open(env_file_path, 'r') as f:
        env_content = f.read()
    
    # Check if ENCRYPT_NEW_NODES is already set
    if "ENCRYPT_NEW_NODES" in env_content:
        print("ENCRYPT_NEW_NODES already exists in .env file")
        return True
    
    # Add ENCRYPT_NEW_NODES=true to .env file
    with open(env_file_path, 'a') as f:
        f.write("\n# Node encryption settings\n")
        f.write("ENCRYPT_NEW_NODES=true\n")
    
    print("✓ Added ENCRYPT_NEW_NODES=true to .env file")
    return True

def execute_migration():
    """Execute the database migration to add encryption support to nodes table."""
    try:
        # Get database connection
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Adding encryption support to nodes table...")
        
        # Add is_encrypted column to nodes table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'nodes' 
            AND column_name = 'is_encrypted'
        """)
        
        if not cursor.fetchone():
            print("Adding is_encrypted column to nodes table...")
            cursor.execute("""
                ALTER TABLE nodes 
                ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE
            """)
            print("✓ is_encrypted column added to nodes table")
        else:
            print("is_encrypted column already exists in nodes table")
        
        # Commit the database changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Database migration completed successfully")
        
        # Update .env file
        env_success = update_env_file()
        
        if env_success:
            print("✓ Environment variable configuration completed")
        else:
            print("WARNING: Environment variable configuration failed")
        
        print("\n" + "=" * 60)
        print("Node encryption migration completed!")
        print("Database: is_encrypted column added to nodes table")
        print("Environment: ENCRYPT_NEW_NODES=true added to .env")
        print("=" * 60)
        
        return True
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting node encryption migration...")
    success = execute_migration()
    exit(0 if success else 1)