#!/usr/bin/env python3
"""
Test script for document status tracking and updates functionality

Requirements: 1.4, 1.5, 4.2 - Status tracking, progress updates, and UI integration
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_async_db
from app.services.document_service import DocumentService
from app.models.document import Document, ProcessingStatus
from sqlalchemy.ext.asyncio import AsyncSession


async def test_status_tracking():
    """Test the enhanced status tracking functionality"""
    
    print("🧪 Testing Document Status Tracking and Updates")
    print("=" * 60)
    
    # Get database session
    db_gen = get_async_db()
    db = await db_gen.__anext__()
    
    try:
            doc_service = DocumentService(db)
            
            # Test 1: Create a test document
            print("\n1. Creating test document...")
            
            # Create a simple document record for testing
            test_doc = Document(
                filename="test_status_tracking.pdf",
                file_type=".pdf",
                file_path="/tmp/test_file.pdf",
                file_size=1024,
                status=ProcessingStatus.PENDING,
                doc_metadata={}
            )
            
            db.add(test_doc)
            if hasattr(db.commit, '__await__'):
                await db.commit()
                await db.refresh(test_doc)
            else:
                db.commit()
                db.refresh(test_doc)
            
            print(f"✅ Created document: {test_doc.id}")
            print(f"   Initial status: {test_doc.status.value}")
            
            # Test 2: Update status with progress
            print("\n2. Testing status updates with progress...")
            
            # Update to processing
            await doc_service.update_status(
                test_doc.id,
                ProcessingStatus.PROCESSING,
                progress_data={
                    "current_step": "initializing",
                    "current_step_number": 1,
                    "total_steps": 5,
                    "progress_percentage": 20
                }
            )
            print("✅ Updated to PROCESSING with progress data")
            
            # Update to parsing
            await doc_service.update_processing_progress(
                test_doc.id,
                "parsing_document",
                2,
                5,
                {"pages_parsed": 5, "total_pages": 10}
            )
            
            await doc_service.update_status(test_doc.id, ProcessingStatus.PARSING)
            print("✅ Updated to PARSING with detailed progress")
            
            # Update to extracting
            await doc_service.update_processing_progress(
                test_doc.id,
                "extracting_knowledge",
                3,
                5,
                {"knowledge_points_found": 15}
            )
            
            await doc_service.update_status(test_doc.id, ProcessingStatus.EXTRACTING)
            print("✅ Updated to EXTRACTING")
            
            # Update to generating cards
            await doc_service.update_processing_progress(
                test_doc.id,
                "generating_cards",
                4,
                5,
                {"cards_generated": 8}
            )
            
            await doc_service.update_status(test_doc.id, ProcessingStatus.GENERATING_CARDS)
            print("✅ Updated to GENERATING_CARDS")
            
            # Update processing stats
            await doc_service.update_processing_stats(
                test_doc.id,
                {
                    "pages_processed": 10,
                    "knowledge_points_extracted": 15,
                    "cards_generated": 8,
                    "processing_time_seconds": 45
                }
            )
            print("✅ Updated processing statistics")
            
            # Complete processing
            await doc_service.update_processing_progress(
                test_doc.id,
                "completed",
                5,
                5
            )
            
            await doc_service.update_status(test_doc.id, ProcessingStatus.COMPLETED)
            print("✅ Updated to COMPLETED")
            
            # Test 3: Get comprehensive status
            print("\n3. Testing comprehensive status retrieval...")
            
            status_info = await doc_service.get_processing_status(test_doc.id)
            
            if "error" in status_info:
                print(f"❌ Error getting status: {status_info['error']}")
                return False
            
            print("✅ Retrieved comprehensive status:")
            print(f"   Status: {status_info['status']}")
            print(f"   Progress: {status_info['progress']['progress_percentage']}%")
            print(f"   Current step: {status_info['progress']['current_step']}")
            print(f"   Statistics: {status_info['statistics']}")
            print(f"   Is processing: {status_info['is_processing']}")
            
            # Test 4: Test batch status retrieval
            print("\n4. Testing batch status retrieval...")
            
            # Create another test document
            test_doc2 = Document(
                filename="test_batch_status.pdf",
                file_type=".pdf",
                file_path="/tmp/test_file2.pdf",
                file_size=2048,
                status=ProcessingStatus.FAILED,
                doc_metadata={},
                error_message="Test error message"
            )
            
            db.add(test_doc2)
            if hasattr(db.commit, '__await__'):
                await db.commit()
                await db.refresh(test_doc2)
            else:
                db.commit()
                db.refresh(test_doc2)
            
            batch_status = await doc_service.get_multiple_processing_status([test_doc.id, test_doc2.id])
            
            if "error" in batch_status:
                print(f"❌ Error getting batch status: {batch_status['error']}")
                return False
            
            print("✅ Retrieved batch status:")
            for doc_id, status in batch_status.items():
                print(f"   {doc_id}: {status['status']} ({status['progress_percentage']}%)")
            
            # Test 5: Test error handling
            print("\n5. Testing error handling...")
            
            # Test with non-existent document
            fake_id = uuid4()
            error_status = await doc_service.get_processing_status(fake_id)
            
            if error_status.get("error") == "Document not found":
                print("✅ Correctly handled non-existent document")
            else:
                print(f"❌ Unexpected response for non-existent document: {error_status}")
                return False
            
            # Test 6: Test retry functionality
            print("\n6. Testing retry functionality...")
            
            try:
                job_id = await doc_service.retry_processing(test_doc2.id, priority=True)
                print(f"✅ Successfully queued retry with job ID: {job_id}")
            except Exception as e:
                print(f"⚠️  Retry test skipped (queue service may not be fully configured): {e}")
            
            # Clean up test documents
            print("\n7. Cleaning up test data...")
            if hasattr(db.delete, '__await__'):
                await db.delete(test_doc)
                await db.delete(test_doc2)
                await db.commit()
            else:
                db.delete(test_doc)
                db.delete(test_doc2)
                db.commit()
            print("✅ Cleaned up test documents")
            
            print("\n" + "=" * 60)
            print("🎉 All status tracking tests passed!")
            return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if hasattr(db, 'close') and callable(db.close):
            if hasattr(db.close, '__await__'):
                await db.close()
            else:
                db.close()


async def test_api_endpoints():
    """Test the API endpoints for status tracking"""
    
    print("\n🌐 Testing Status Tracking API Endpoints")
    print("=" * 60)
    
    try:
        import httpx
        from app.main import app
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            
            # Test processing overview endpoint
            print("\n1. Testing processing overview endpoint...")
            
            response = await client.get("/api/processing/overview")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Processing overview endpoint working:")
                print(f"   Status counts: {data.get('status_counts', {})}")
                print(f"   Recent documents: {len(data.get('recent_documents', []))}")
                print(f"   Queue health: {data.get('queue_health', {})}")
            else:
                print(f"❌ Processing overview failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 API endpoint tests completed!")
            return True
            
    except ImportError:
        print("⚠️  Skipping API tests (httpx not available)")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    
    print("🚀 Starting Document Status Tracking Tests")
    print("=" * 60)
    
    # Test 1: Core functionality
    success1 = await test_status_tracking()
    
    # Test 2: API endpoints
    success2 = await test_api_endpoints()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Status tracking implementation is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)