#!/usr/bin/env python3
"""
Test database connection and document creation
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_async_db, init_db, create_tables
from app.models.document import Document, ProcessingStatus
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def test_database_connection():
    """Test database connection and basic operations"""
    print("Testing database connection...")
    print(f"Database URL: {settings.database_url}")
    
    try:
        # Initialize database
        await init_db()
        print("✓ Database initialized successfully")
        
        # Create tables
        await create_tables()
        print("✓ Database tables created successfully")
        
        # Test database session
        async for db in get_async_db():
            # Test creating a document record
            test_doc = Document(
                filename="test_document.pdf",
                file_type="pdf",
                file_path="/tmp/test.pdf",
                file_size=1024,
                status=ProcessingStatus.PENDING
            )
            
            db.add(test_doc)
            
            # Handle both async and sync sessions
            if hasattr(db, 'commit') and callable(getattr(db, 'commit')):
                if hasattr(db.commit, '__await__'):
                    await db.commit()
                    await db.refresh(test_doc)
                else:
                    db.commit()
                    db.refresh(test_doc)
            
            print(f"✓ Created test document with ID: {test_doc.id}")
            
            # Test querying the document
            stmt = select(Document).where(Document.id == test_doc.id)
            if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
                if hasattr(db.execute, '__await__'):
                    result = await db.execute(stmt)
                else:
                    result = db.execute(stmt)
            retrieved_doc = result.scalar_one_or_none()
            
            if retrieved_doc:
                print(f"✓ Retrieved document: {retrieved_doc.filename}")
            else:
                print("✗ Failed to retrieve document")
                return False
            
            # Clean up test document
            if hasattr(db, 'delete') and callable(getattr(db, 'delete')):
                if hasattr(db.delete, '__await__'):
                    await db.delete(test_doc)
                    await db.commit()
                else:
                    db.delete(test_doc)
                    db.commit()
            print("✓ Cleaned up test document")
            
            break
        
        print("✓ Database connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    sys.exit(0 if success else 1)