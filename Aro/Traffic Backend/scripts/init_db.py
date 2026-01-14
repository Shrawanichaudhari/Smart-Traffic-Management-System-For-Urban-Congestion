#!/usr/bin/env python3
"""
Database initialization script for Traffic Analytics API.
Run this script to create all database tables and initial data.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import db_manager
from app.models import Base

def main():
    """Initialize the database with tables and sample data."""
    print("🚀 Initializing Traffic Analytics Database...")
    
    try:
        # Create all tables
        print("📊 Creating database tables...")
        db_manager.create_tables()
        print("✅ Database tables created successfully!")
        
        # Get connection info
        conn_info = db_manager.get_connection_info()
        print(f"📡 Database connection: {conn_info['url']}")
        print(f"📊 Pool size: {conn_info['pool_size']}")
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
