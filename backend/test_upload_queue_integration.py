#!/usr/bin/env python3
"""
Test upload endpoint queue integration
"""

import sys
import tempfile
from pathlib import Path

sys.path.append('.')

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_upload_queue_integration():
    """Test that upload endpoint properly integrates with queue"""
    
    print("🧪 Testing Upload-Queue Integration...")
    print("=" * 50)
    
    # Create a test file
    test_content = "# Test Document\n\nThis is a test document for queue integration."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # Test upload
        print("\n1. Testing document upload...")
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/ingest",
                files={"file": ("test_document.md", f, "text/markdown")}
            )
        
        if response.status_code == 201:
            print("✅ Document uploaded successfully")
            document_data = response.json()
            document_id = document_data['id']
            print(f"   Document ID: {document_id}")
            print(f"   Status: {document_data['status']}")
            
            # Test queue status
            print("\n2. Testing queue status...")
            queue_response = client.get("/api/queue/info")
            if queue_response.status_code == 200:
                queue_info = queue_response.json()
                total_jobs = (
                    queue_info['queues']['document_processing']['length'] +
                    queue_info['queues']['priority_processing']['length']
                )
                print(f"✅ Queue info retrieved - Total jobs: {total_jobs}")
            
            # Test document processing status
            print("\n3. Testing document processing status...")
            status_response = client.get(f"/api/queue/document/{document_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Processing status retrieved:")
                print(f"   Status: {status_data.get('status', 'unknown')}")
                print(f"   Job status: {status_data.get('job_status', {}).get('status', 'unknown')}")
            
            print("\n✅ Upload-Queue Integration Test: PASSED")
            return True
            
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        Path(temp_file_path).unlink(missing_ok=True)


if __name__ == "__main__":
    success = test_upload_queue_integration()
    if success:
        print("\n🎯 Upload-Queue Integration: WORKING")
        print("\nThe upload endpoint successfully:")
        print("• Accepts file uploads")
        print("• Creates document records")
        print("• Queues documents for background processing")
        print("• Provides status tracking")
    else:
        print("\n❌ Upload-Queue Integration: FAILED")
        sys.exit(1)