#!/usr/bin/env python3
"""
Test database connection and session management
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_database_connection():
    """Test database connection and basic operations"""
    try:
        from app.core.database import get_db, init_db, create_tables, engine
        from app.models import Document, ProcessingStatus
        from sqlalchemy.orm import Session
        
        print("Testing database connection...")
        
        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1
            print("✓ Database engine connection successful")
        
        # Test session creation
        db_gen = get_db()
        db = next(db_gen)
        assert isinstance(db, Session)
        print("✓ Database session creation successful")
        
        # Close the session
        db.close()
        
        print("✓ All database connection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

async def test_pgvector_support():
    """Test pgvector extension support"""
    try:
        from app.core.database import engine
        
        print("Testing pgvector extension...")
        
        # This will only work with PostgreSQL
        if "postgresql" in str(engine.url):
            with engine.connect() as conn:
                # Try to create vector extension
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                print("✓ pgvector extension available")
        else:
            print("⚠ Skipping pgvector test (not using PostgreSQL)")
            
        return True
        
    except Exception as e:
        print(f"❌ pgvector test failed: {e}")
        return False

async def main():
    """Run all database tests"""
    print("Running database tests...\n")
    
    # Test basic connection
    conn_success = await test_database_connection()
    
    # Test pgvector support
    vector_success = await test_pgvector_support()
    
    if conn_success:
        print("\n✅ Database tests completed successfully!")
    else:
        print("\n❌ Some database tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())