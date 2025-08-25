#!/usr/bin/env python3
"""
Test script for document status tracking API endpoints

Requirements: 1.4, 1.5, 4.2 - Status tracking, progress updates, and UI integration
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_async_db
from app.models.document import Document, ProcessingStatus


async def test_api_endpoints():
    """Test the API endpoints for status tracking"""
    
    print("🌐 Testing Status Tracking API Endpoints")
    print("=" * 60)
    
    # Get database session
    db_gen = get_async_db()
    db = await db_gen.__anext__()
    
    try:
        # Create test documents
        test_doc1 = Document(
            filename="test_api_1.pdf",
            file_type=".pdf",
            file_path="/tmp/test_api_1.pdf",
            file_size=1024,
            status=ProcessingStatus.COMPLETED,
            doc_metadata={
                "processing_progress": {
                    "current_step": "completed",
                    "progress_percentage": 100
                }
            }
        )
        
        test_doc2 = Document(
            filename="test_api_2.pdf",
            file_type=".pdf",
            file_path="/tmp/test_api_2.pdf",
            file_size=2048,
            status=ProcessingStatus.PROCESSING,
            doc_metadata={
                "processing_progress": {
                    "current_step": "parsing",
                    "progress_percentage": 45
                }
            }
        )
        
        db.add(test_doc1)
        db.add(test_doc2)
        
        if hasattr(db.commit, '__await__'):
            await db.commit()
            await db.refresh(test_doc1)
            await db.refresh(test_doc2)
        else:
            db.commit()
            db.refresh(test_doc1)
            db.refresh(test_doc2)
        
        print(f"✅ Created test documents: {test_doc1.id}, {test_doc2.id}")
        
        # Test the API endpoints by importing and calling them directly
        from app.api.documents import get_document_status, get_multiple_document_status, get_processing_overview
        
        # Test 1: Single document status
        print("\n1. Testing single document status endpoint...")
        
        status_response = await get_document_status(test_doc1.id, db)
        
        print("✅ Single document status response:")
        print(f"   Document ID: {status_response['document_id']}")
        print(f"   Status: {status_response['status']}")
        print(f"   Progress: {status_response['progress']['progress_percentage']}%")
        print(f"   Is processing: {status_response['is_processing']}")
        
        # Test 2: Batch document status
        print("\n2. Testing batch document status endpoint...")
        
        batch_response = await get_multiple_document_status([test_doc1.id, test_doc2.id], db)
        
        print("✅ Batch document status response:")
        print(f"   Document count: {batch_response['count']}")
        for doc_id, status in batch_response['documents'].items():
            print(f"   {doc_id}: {status['status']} ({status['progress_percentage']}%)")
        
        # Test 3: Processing overview
        print("\n3. Testing processing overview endpoint...")
        
        overview_response = await get_processing_overview(db)
        
        print("✅ Processing overview response:")
        print(f"   Status counts: {overview_response['status_counts']}")
        print(f"   Recent documents: {len(overview_response['recent_documents'])}")
        print(f"   Queue health available: {'queue_health' in overview_response}")
        
        # Clean up
        print("\n4. Cleaning up test data...")
        if hasattr(db.delete, '__await__'):
            await db.delete(test_doc1)
            await db.delete(test_doc2)
            await db.commit()
        else:
            db.delete(test_doc1)
            db.delete(test_doc2)
            db.commit()
        print("✅ Cleaned up test documents")
        
        print("\n" + "=" * 60)
        print("🎉 All API endpoint tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if hasattr(db, 'close') and callable(db.close):
            if hasattr(db.close, '__await__'):
                await db.close()
            else:
                db.close()


async def main():
    """Run API endpoint tests"""
    
    print("🚀 Starting Document Status Tracking API Tests")
    print("=" * 60)
    
    success = await test_api_endpoints()
    
    if success:
        print("\n🎉 All API tests passed! Status tracking API endpoints are working correctly.")
        return 0
    else:
        print("\n❌ Some API tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)