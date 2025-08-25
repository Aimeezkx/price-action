#!/usr/bin/env python3
"""
Test the actual upload API endpoint
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os
import requests
import time
from io import BytesIO

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_async_db, init_db, create_tables
from app.models.document import Document
from sqlalchemy import select


async def test_api_upload_endpoint():
    """Test the actual API upload endpoint"""
    print("Testing API upload endpoint...")
    
    try:
        # Initialize database first
        await init_db()
        await create_tables()
        print("✓ Database initialized")
        
        # Start the server in the background (we'll assume it's running)
        # In a real test, you'd start the server programmatically
        
        # Test data
        test_content = b"This is a test PDF content for API upload testing."
        
        # Create a test file
        files = {
            'file': ('test_api_upload.pdf', BytesIO(test_content), 'application/pdf')
        }
        
        # Make upload request
        try:
            response = requests.post(
                'http://localhost:8000/api/ingest',
                files=files,
                timeout=10
            )
            
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
                
        except requests.exceptions.ConnectionError:
            print("✗ Could not connect to server at http://localhost:8000")
            print("  Please start the server with: python main.py")
            return False
        except Exception as e:
            print(f"✗ Request failed: {e}")
            return False
        
    except Exception as e:
        print(f"✗ API upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api_upload_endpoint())
    sys.exit(0 if success else 1)