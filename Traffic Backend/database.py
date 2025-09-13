"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database URL - using SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic_data.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_connection_info(self):
        """Get database connection information"""
        return {
            "database_url": DATABASE_URL,
            "engine_info": str(self.engine),
            "connection_pool": {
                "size": getattr(self.engine.pool, 'size', 'N/A'),
                "checked_in": getattr(self.engine.pool, 'checkedin', 'N/A'),
                "checked_out": getattr(self.engine.pool, 'checkedout', 'N/A'),
                "overflow": getattr(self.engine.pool, 'overflow', 'N/A'),
            }
        }

    async def health_check(self):
        """Check if database is healthy"""
        try:
            with self.get_db_context() as db:
                db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @contextmanager
    def get_db_context(self):
        """Context manager for database sessions"""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()

    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

# Create database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager  
def get_db_context():
    """Alias for compatibility"""
    return db_manager.get_db_context()