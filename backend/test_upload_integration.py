#!/usr/bin/env python3
"""
Test upload endpoint integration using FastAPI TestClient
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os
from io import BytesIO

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app
from app.core.database import get_async_db, init_db, create_tables
from app.models.document import Document
from sqlalchemy import select


async def test_upload_integration():
    """Test upload endpoint integration"""
    print("Testing upload endpoint integration...")
    
    try:
        # Initialize database
        await init_db()
        await create_tables()
        print("✓ Database initialized")
        
        # Create test client
        client = TestClient(app)
        
        # Test data
        test_content = b"This is a test PDF content for integration testing."
        
        # Create test file
        files = {
            'file': ('test_integration.pdf', BytesIO(test_content), 'application/pdf')
        }
        
        # Make upload request
        response = client.post('/api/ingest', files=files)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 201:
            print("✓ Upload request successful")
            result = response.json()
            print(f"  - Document ID: {result.get('id')}")
            print(f"  - Filename: {result.get('filename')}")
            print(f"  - Status: {result.get('status')}")
            
            # Verify document was created in database
            document_id = result.get('id')
            if document_id:
                async for db in get_async_db():
                    stmt = select(Document).where(Document.id == document_id)
                    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
                        if hasattr(db.execute, '__await__'):
                            db_result = await db.execute(stmt)
                        else:
                            db_result = db.execute(stmt)
                    doc = db_result.scalar_one_or_none()
                    
                    if doc:
                        print("✓ Document found in database")
                        print(f"  - DB Filename: {doc.filename}")
                        print(f"  - DB Status: {doc.status}")
                        print(f"  - DB File size: {doc.file_size}")
                        print(f"  - DB File path: {doc.file_path}")
                        
                        # Clean up
                        if os.path.exists(doc.file_path):
                            os.remove(doc.file_path)
                            print("✓ Cleaned up uploaded file")
                        
                        # Clean up database record
                        if hasattr(db, 'delete') and callable(getattr(db, 'delete')):
                            if hasattr(db.delete, '__await__'):
                                await db.delete(doc)
                                await db.commit()
                            else:
                                db.delete(doc)
                                db.commit()
                        print("✓ Cleaned up database record")
                    else:
                        print("✗ Document not found in database")
                        return False
                    break
            
            return True
        else:
            print(f"✗ Upload request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"✗ Upload integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_upload_integration())
    sys.exit(0 if success else 1)