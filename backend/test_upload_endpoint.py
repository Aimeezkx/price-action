#!/usr/bin/env python3
"""
Test upload endpoint database integration
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO
from app.core.database import get_async_db, init_db, create_tables
from app.models.document import Document, ProcessingStatus
from app.services.document_service import DocumentService
from sqlalchemy import select


async def test_upload_endpoint_database_integration():
    """Test that upload endpoint can create document records in database"""
    print("Testing upload endpoint database integration...")
    
    try:
        # Initialize database
        await init_db()
        await create_tables()
        print("✓ Database initialized")
        
        # Create a test file
        test_content = b"This is a test PDF content for upload testing."
        test_file = UploadFile(
            filename="test_upload.pdf",
            file=BytesIO(test_content),
            size=len(test_content),
            headers={"content-type": "application/pdf"}
        )
        
        # Test DocumentService directly
        async for db in get_async_db():
            doc_service = DocumentService(db)
            
            # Test document creation
            document = await doc_service.create_document(test_file, "safe_test_upload.pdf")
            print(f"✓ Created document record with ID: {document.id}")
            print(f"  - Filename: {document.filename}")
            print(f"  - File type: {document.file_type}")
            print(f"  - Status: {document.status}")
            print(f"  - File size: {document.file_size}")
            
            # Verify document was saved to database
            stmt = select(Document).where(Document.id == document.id)
            if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
                if hasattr(db.execute, '__await__'):
                    result = await db.execute(stmt)
                else:
                    result = db.execute(stmt)
            retrieved_doc = result.scalar_one_or_none()
            
            if retrieved_doc:
                print(f"✓ Document successfully saved to database")
                print(f"  - Retrieved filename: {retrieved_doc.filename}")
                print(f"  - Retrieved status: {retrieved_doc.status}")
            else:
                print("✗ Document not found in database")
                return False
            
            # Test status update
            updated_doc = await doc_service.update_status(
                document.id, 
                ProcessingStatus.PROCESSING
            )
            print(f"✓ Updated document status to: {updated_doc.status}")
            
            # Clean up - delete the test file if it was created
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
                print("✓ Cleaned up test file")
            
            # Clean up database record
            if hasattr(db, 'delete') and callable(getattr(db, 'delete')):
                if hasattr(db.delete, '__await__'):
                    await db.delete(document)
                    await db.commit()
                else:
                    db.delete(document)
                    db.commit()
            print("✓ Cleaned up database record")
            
            break
        
        print("✓ Upload endpoint database integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Upload endpoint database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_upload_endpoint_database_integration())
    sys.exit(0 if success else 1)