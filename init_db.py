"""
Database initialization script.
Creates all tables based on the SQLAlchemy models.
"""
from app.db.database import create_tables, engine
from app.models.models import Base

def main():
    """Initialize database tables."""
    print("Creating database tables...")
    try:
        # Import all models to ensure they're registered with Base
        from app.models import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    main()