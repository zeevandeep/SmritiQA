"""
Migration script to add encryption support to reflections table.

This migration adds the is_encrypted column to track encryption status
and updates the .env file to set ENCRYPT_NEW_REFLECTIONS=true.
"""

import os
import psycopg2
from datetime import datetime

def update_env_file():
    """Add ENCRYPT_NEW_REFLECTIONS=true to .env file if not already present."""
    env_file_path = ".env"
    
    if not os.path.exists(env_file_path):
        print("WARNING: .env file not found, skipping environment variable update")
        return False
    
    # Read current .env file
    with open(env_file_path, 'r') as f:
        env_content = f.read()
    
    # Check if ENCRYPT_NEW_REFLECTIONS is already set
    if "ENCRYPT_NEW_REFLECTIONS" in env_content:
        print("ENCRYPT_NEW_REFLECTIONS already exists in .env file")
        return True
    
    # Add ENCRYPT_NEW_REFLECTIONS=true to .env file
    if "# Encryption settings" in env_content:
        # Add to existing encryption settings section
        env_lines = env_content.split('\n')
        for i, line in enumerate(env_lines):
            if line.startswith("ENCRYPT_NEW_NODES"):
                # Find the last encryption setting line
                last_encryption_line = i
                while last_encryption_line + 1 < len(env_lines) and env_lines[last_encryption_line + 1].startswith("ENCRYPT_NEW_"):
                    last_encryption_line += 1
                # Insert after the last encryption setting
                env_lines.insert(last_encryption_line + 1, "ENCRYPT_NEW_REFLECTIONS=true")
                break
        
        with open(env_file_path, 'w') as f:
            f.write('\n'.join(env_lines))
    else:
        # Add new encryption settings section
        with open(env_file_path, 'a') as f:
            f.write("\n# Reflection encryption settings\n")
            f.write("ENCRYPT_NEW_REFLECTIONS=true\n")
    
    print("✓ Added ENCRYPT_NEW_REFLECTIONS=true to .env file")
    return True

def execute_migration():
    """Execute the database migration to add encryption support to reflections table."""
    try:
        # Get database connection
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL environment variable not found")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Adding encryption support to reflections table...")
        
        # Add is_encrypted column to reflections table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'reflections' 
            AND column_name = 'is_encrypted'
        """)
        
        if not cursor.fetchone():
            print("Adding is_encrypted column to reflections table...")
            cursor.execute("""
                ALTER TABLE reflections 
                ADD COLUMN is_encrypted BOOLEAN DEFAULT FALSE
            """)
            print("✓ is_encrypted column added to reflections table")
        else:
            print("is_encrypted column already exists in reflections table")
        
        # Commit the database changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Database migration completed successfully")
        
        # Update .env file
        update_env_file()
        
        print("\n" + "="*50)
        print("✓ REFLECTION ENCRYPTION MIGRATION COMPLETED")
        print("="*50)
        print("Summary:")
        print("- Added is_encrypted column to reflections table")
        print("- Updated .env file with ENCRYPT_NEW_REFLECTIONS=true")
        print("- Existing reflections remain unencrypted (is_encrypted=false)")
        print("- New reflections will be encrypted based on environment setting")
        
        return True
        
    except Exception as e:
        print(f"ERROR during migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting reflection encryption migration...")
    print(f"Timestamp: {datetime.now()}")
    
    success = execute_migration()
    
    if success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        exit(1)