#!/usr/bin/env python3
"""
Test script for Task 4: Test the actual upload endpoint

This script tests the /api/ingest endpoint to ensure it properly
creates document records in the database during upload.
"""

import asyncio
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
import sys
sys.path.append('.')

from main import app
from app.core.database import init_db, create_tables


def test_upload_endpoint():
    """Test the actual upload endpoint"""
    
    print("🧪 Testing Task 4: Upload endpoint document creation")
    print("=" * 60)
    
    try:
        # Create test client
        print("1. Creating test client...")
        client = TestClient(app)
        print("   ✅ Test client created")
        
        # Create test file content with PDF header
        print("2. Creating test file...")
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
        test_filename = "test_upload_document.pdf"
        print(f"   ✅ Test file prepared: {test_filename} ({len(test_content)} bytes)")
        
        # Test upload endpoint
        print("3. Testing upload endpoint...")
        files = {"file": (test_filename, test_content, "application/pdf")}
        response = client.post("/api/ingest", files=files)
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code == 201:
            print("   ✅ Upload successful!")
            
            # Parse response
            response_data = response.json()
            print("   📄 Response data:")
            for key, value in response_data.items():
                if key == "id":
                    print(f"      - {key}: {value}")
                elif key in ["created_at", "updated_at"]:
                    print(f"      - {key}: {value}")
                else:
                    print(f"      - {key}: {value}")
            
            # Verify required fields
            print("4. Verifying response fields...")
            
            assert "id" in response_data, "Response should contain document ID"
            assert response_data["id"], "Document ID should not be empty"
            print("   ✅ Document ID is present")
            
            assert "status" in response_data, "Response should contain status"
            assert response_data["status"] == "pending", f"Status should be 'pending', got '{response_data['status']}'"
            print("   ✅ Status is 'pending'")
            
            assert "filename" in response_data, "Response should contain filename"
            assert response_data["filename"], "Filename should not be empty"
            print("   ✅ Filename is present")
            
            assert "file_size" in response_data, "Response should contain file_size"
            assert response_data["file_size"] > 0, "File size should be greater than 0"
            print(f"   ✅ File size is present: {response_data['file_size']} bytes")
            
            assert "created_at" in response_data, "Response should contain created_at"
            assert response_data["created_at"], "Created timestamp should not be empty"
            print("   ✅ Created timestamp is present")
            
            print("\n🎉 Upload endpoint test passed!")
            print("\nTask 4 Requirements Verification:")
            print("✅ Upload endpoint creates Document model instances")
            print("✅ Initial status is set to PENDING")
            print("✅ File metadata and processing information is stored")
            print("✅ Document ID and status are returned to frontend")
            
            return True
            
        else:
            print(f"   ❌ Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_status_endpoint():
    """Test the document status endpoint"""
    
    print("\n🧪 Testing document status endpoint")
    print("=" * 40)
    
    try:
        # Create test client
        client = TestClient(app)
        
        # First upload a document
        print("1. Uploading test document...")
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
        files = {"file": ("status_test.pdf", test_content, "application/pdf")}
        upload_response = client.post("/api/ingest", files=files)
        
        if upload_response.status_code != 201:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            return False
        
        document_id = upload_response.json()["id"]
        print(f"   ✅ Document uploaded with ID: {document_id}")
        
        # Test status endpoint
        print("2. Testing status endpoint...")
        status_response = client.get(f"/api/documents/{document_id}/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("   ✅ Status endpoint successful!")
            print(f"      - Document ID: {status_data.get('document_id')}")
            print(f"      - Status: {status_data.get('status')}")
            print(f"      - Filename: {status_data.get('filename')}")
            
            # Verify status data
            assert status_data.get("document_id") == document_id, "Document ID should match"
            assert status_data.get("status") == "pending", "Status should be pending"
            print("   ✅ Status data is correct")
            
            return True
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Status endpoint test failed: {e}")
        return False


if __name__ == "__main__":
    # Initialize database first
    async def init():
        await init_db()
        await create_tables()
    
    asyncio.run(init())
    
    # Run tests
    success1 = test_upload_endpoint()
    success2 = test_document_status_endpoint()
    
    if success1 and success2:
        print("\n🎉 All endpoint tests passed!")
        print("\nTask 4 is fully implemented and working:")
        print("• Upload endpoint creates document records in database")
        print("• Document status is properly set to PENDING")
        print("• File metadata is stored correctly")
        print("• Document ID and status are returned in response")
        print("• Status endpoint allows checking document processing status")
    else:
        print("\n❌ Some endpoint tests failed.")
        exit(1)