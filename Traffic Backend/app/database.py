# database.py - Database configuration and connection management
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://traffic_user:traffic_pass@localhost:5432/traffic_simulation"
)

# Create engine with connection pooling for high-frequency inserts
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Increased for high-frequency inserts
    max_overflow=30,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints.
    Yields a database session and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI.
    Useful for batch processing and background tasks.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise
    finally:
        db.close()

class DatabaseManager:
    """
    Database manager class for handling batch operations and optimizations.
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all tables defined in models."""
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
        logging.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        from .models import Base
        Base.metadata.drop_all(bind=self.engine)
        logging.warning("All database tables dropped")
    
    def get_connection_info(self):
        """Get database connection information."""
        return {
            "url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "hidden",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin()
        }
    
    async def health_check(self) -> bool:
        """
        Perform a database health check.
        Returns True if database is accessible, False otherwise.
        """
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return False

# Initialize database manager
db_manager = DatabaseManager()

# Logging configuration for database operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger for database operations
db_logger = logging.getLogger("database")

# Environment-specific configurations
if os.getenv("ENVIRONMENT") == "production":
    # Production optimizations
    engine.execution_options(
        autocommit=False,
        isolation_level="READ_COMMITTED"
    )
elif os.getenv("ENVIRONMENT") == "development":
    # Development settings - more verbose logging
    engine.echo = True
