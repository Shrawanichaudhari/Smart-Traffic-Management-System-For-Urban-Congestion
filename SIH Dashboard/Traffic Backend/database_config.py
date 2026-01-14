# database_config.py - Database configuration and connection management
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
    "postgresql://username:password@localhost:5432/traffic_simulation"
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
        """
        Create all tables defined in models and set up TigerData hypertables.
        """
        from models import Base
        Base.metadata.create_all(bind=self.engine)
        logging.info("Database tables created successfully")
        
        # Set up TigerData hypertables for time-series data
        self._setup_hypertables()
    
    def _setup_hypertables(self):
        """
        Set up TigerData hypertables for time-series data.
        This converts regular tables to hypertables optimized for time-series data.
        """
        try:
            with get_db_context() as db:
                # Convert traffic_data table to a hypertable
                db.execute("""
                    SELECT create_hypertable('traffic_data', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Convert performance_metrics table to a hypertable
                db.execute("""
                    SELECT create_hypertable('performance_metrics', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Convert signal_states table to a hypertable
                db.execute("""
                    SELECT create_hypertable('signal_states', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Convert emergency_events table to a hypertable
                db.execute("""
                    SELECT create_hypertable('emergency_events', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Create a new table for raw JSON traffic data
                db.execute("""
                    CREATE TABLE IF NOT EXISTS raw_traffic_data (
                        id SERIAL PRIMARY KEY,
                        simulation_id VARCHAR(50) NOT NULL,
                        intersection_id VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        data JSONB NOT NULL
                    )
                """)
                
                # Convert raw_traffic_data to a hypertable
                db.execute("""
                    SELECT create_hypertable('raw_traffic_data', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Create a new table for calculated metrics
                db.execute("""
                    CREATE TABLE IF NOT EXISTS calculated_metrics (
                        id SERIAL PRIMARY KEY,
                        simulation_id VARCHAR(50) NOT NULL,
                        intersection_id VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        metric_type VARCHAR(50) NOT NULL,
                        value NUMERIC(12, 4) NOT NULL,
                        calculation_period VARCHAR(20) NOT NULL
                    )
                """)
                
                # Convert calculated_metrics to a hypertable
                db.execute("""
                    SELECT create_hypertable('calculated_metrics', 'timestamp', 
                                          if_not_exists => TRUE,
                                          chunk_time_interval => INTERVAL '1 hour')
                """)
                
                # Create indexes for better query performance
                db.execute("CREATE INDEX IF NOT EXISTS idx_raw_traffic_simulation_id ON raw_traffic_data (simulation_id)")
                db.execute("CREATE INDEX IF NOT EXISTS idx_raw_traffic_intersection_id ON raw_traffic_data (intersection_id)")
                db.execute("CREATE INDEX IF NOT EXISTS idx_calculated_metrics_simulation_id ON calculated_metrics (simulation_id)")
                db.execute("CREATE INDEX IF NOT EXISTS idx_calculated_metrics_intersection_id ON calculated_metrics (intersection_id)")
                db.execute("CREATE INDEX IF NOT EXISTS idx_calculated_metrics_metric_type ON calculated_metrics (metric_type)")
                
                logging.info("TigerData hypertables and indexes set up successfully")
        except Exception as e:
            logging.error(f"Error setting up TigerData hypertables: {e}")
            raise
    
    def drop_tables(self):
        """
        Drop all tables (use with caution!).
        """
        from models import Base
        Base.metadata.drop_all(bind=self.engine)
        logging.warning("All database tables dropped")
    
    def get_connection_info(self):
        """
        Get database connection information.
        """
        return {
            "url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "hidden",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin(),
            "database_type": "TigerData (TimescaleDB successor)"
        }
    
    async def health_check(self) -> bool:
        """
        Perform a database health check.
        Returns True if database is accessible, False otherwise.
        """
        try:
            with get_db_context() as db:
                # Simple query to check database connection
                db.execute("SELECT 1")
                return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()