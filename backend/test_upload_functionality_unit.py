#!/usr/bin/env python3
"""
Unit tests for upload functionality

This test focuses on testing the upload endpoint logic without requiring
a running server, testing the core functionality in isolation.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import asyncio
import sys
import os
import tempfile
import json
from pathlib import Path
from io import BytesIO
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import the main app and components
from main import app
from app.models.document import Document, ProcessingStatus
from app.services.document_service import DocumentService

def create_test_pdf(content: str = "Test PDF content") -> bytes:
    """Create a simple PDF file for testing"""
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(content) + 50}
>>
stream
BT
/F1 12 Tf
72 720 Td
({content}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{200 + len(content)}
%%EOF"""
    return pdf_content.encode('utf-8')

def create_test_txt() -> bytes:
    """Create a test TXT file"""
    content = """Test Text Document

This is a test text document for upload testing.
It contains multiple lines and paragraphs.

Key concepts:
- Document processing
- Text extraction
- Knowledge points
- Flashcard generation
"""
    return content.encode('utf-8')

class TestUploadFunctionality:
    """Test upload functionality with mocked dependencies"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_successful_pdf_upload_structure(self):
        """Test that PDF upload returns correct response structure"""
        pdf_content = create_test_pdf("Test PDF for structure validation")
        
        with patch('app.core.database.get_async_db') as mock_db, \
             patch('app.services.document_service.DocumentService') as mock_service:
            
            # Mock database session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_db.return_value = mock_session
            
            # Mock document service
            mock_doc_service = AsyncMock(spec=DocumentService)
            mock_service.return_value = mock_doc_service
            
            # Mock document creation
            mock_document = Mock(spec=Document)
            mock_document.id = "123e4567-e89b-12d3-a456-426614174000"
            mock_document.filename = "test.pdf"
            mock_document.status = ProcessingStatus.PENDING
            mock_document.created_at = "2024-01-01T00:00:00Z"
            mock_document.file_type = "pdf"
            mock_document.file_size = len(pdf_content)
            
            mock_doc_service.create_document.return_value = mock_document
            mock_doc_service.queue_for_processing.return_value = None
            
            # Test upload
            files = {
                'file': ('test.pdf', BytesIO(pdf_content), 'application/pdf')
            }
            
            response = self.client.post("/api/ingest", files=files)
            
            # Verify response structure
            assert response.status_code == 201
            data = response.json()
            
            # Check required fields
            required_fields = ['id', 'filename', 'status', 'created_at']
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify field values
            assert data['filename'] == "test.pdf"
            assert data['status'] in ['pending', 'processing']
            
            print("✓ PDF upload returns correct response structure")
    
    def test_successful_txt_upload_structure(self):
        """Test that TXT upload returns correct response structure"""
        txt_content = create_test_txt()
        
        with patch('app.core.database.get_async_db') as mock_db, \
             patch('app.services.document_service.DocumentService') as mock_service:
            
            # Mock database session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_db.return_value = mock_session
            
            # Mock document service
            mock_doc_service = AsyncMock(spec=DocumentService)
            mock_service.return_value = mock_doc_service
            
            # Mock document creation
            mock_document = Mock(spec=Document)
            mock_document.id = "123e4567-e89b-12d3-a456-426614174001"
            mock_document.filename = "test.txt"
            mock_document.status = ProcessingStatus.PENDING
            mock_document.created_at = "2024-01-01T00:00:00Z"
            mock_document.file_type = "txt"
            mock_document.file_size = len(txt_content)
            
            mock_doc_service.create_document.return_value = mock_document
            mock_doc_service.queue_for_processing.return_value = None
            
            # Test upload
            files = {
                'file': ('test.txt', BytesIO(txt_content), 'text/plain')
            }
            
            response = self.client.post("/api/ingest", files=files)
            
            # Verify response structure
            assert response.status_code == 201
            data = response.json()
            
            # Check required fields
            required_fields = ['id', 'filename', 'status', 'created_at']
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify field values
            assert data['filename'] == "test.txt"
            assert data['status'] in ['pending', 'processing']
            
            print("✓ TXT upload returns correct response structure")
    
    def test_empty_file_rejection(self):
        """Test that empty files are rejected"""
        files = {
            'file': ('empty.pdf', BytesIO(b''), 'application/pdf')
        }
        
        response = self.client.post("/api/ingest", files=files)
        
        # Should be rejected with 400 status
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        
        print("✓ Empty files are properly rejected")
    
    def test_no_file_rejection(self):
        """Test that requests without files are rejected"""
        response = self.client.post("/api/ingest")
        
        # Should be rejected with 422 status (Unprocessable Entity)
        assert response.status_code == 422
        
        print("✓ Requests without files are properly rejected")
    
    def test_invalid_file_extension_rejection(self):
        """Test that invalid file extensions are rejected"""
        invalid_content = b"This is not a valid file"
        
        files = {
            'file': ('test.exe', BytesIO(invalid_content), 'application/octet-stream')
        }
        
        with patch('app.utils.security.SecurityValidator') as mock_validator:
            # Mock security validator to reject the file
            mock_validator_instance = Mock()
            mock_validator_instance.validate_upload_file.return_value = {
                'is_secure': False,
                'issues': ['Invalid file extension']
            }
            mock_validator.return_value = mock_validator_instance
            
            response = self.client.post("/api/ingest", files=files)
            
            # Should be rejected with 400 status
            assert response.status_code == 400
            data = response.json()
            assert 'error' in data
            
            print("✓ Invalid file extensions are properly rejected")
    
    def test_large_file_handling(self):
        """Test handling of large files"""
        # Create a large file (simulate 15MB)
        large_content = b"A" * (15 * 1024 * 1024)
        
        files = {
            'file': ('large.pdf', BytesIO(large_content), 'application/pdf')
        }
        
        response = self.client.post("/api/ingest", files=files)
        
        # Should either be rejected (413) or accepted (201)
        # Both are valid depending on server configuration
        assert response.status_code in [201, 413]
        
        if response.status_code == 413:
            data = response.json()
            assert 'error' in data
            print("✓ Large files are properly rejected")
        else:
            print("✓ Large files are accepted (server allows large files)")
    
    def test_document_service_integration(self):
        """Test that document service is properly called"""
        pdf_content = create_test_pdf("Test PDF for service integration")
        
        with patch('app.core.database.get_async_db') as mock_db, \
             patch('app.services.document_service.DocumentService') as mock_service:
            
            # Mock database session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_db.return_value = mock_session
            
            # Mock document service
            mock_doc_service = AsyncMock(spec=DocumentService)
            mock_service.return_value = mock_doc_service
            
            # Mock document creation
            mock_document = Mock(spec=Document)
            mock_document.id = "123e4567-e89b-12d3-a456-426614174000"
            mock_document.filename = "test.pdf"
            mock_document.status = ProcessingStatus.PENDING
            mock_document.created_at = "2024-01-01T00:00:00Z"
            
            mock_doc_service.create_document.return_value = mock_document
            mock_doc_service.queue_for_processing.return_value = None
            
            # Test upload
            files = {
                'file': ('test.pdf', BytesIO(pdf_content), 'application/pdf')
            }
            
            response = self.client.post("/api/ingest", files=files)
            
            # Verify service was called
            assert response.status_code == 201
            mock_doc_service.create_document.assert_called_once()
            mock_doc_service.queue_for_processing.assert_called_once()
            
            print("✓ Document service is properly integrated")
    
    def test_error_handling_structure(self):
        """Test that errors return proper structure"""
        # Test with invalid file to trigger error handling
        files = {
            'file': ('test.exe', BytesIO(b"invalid"), 'application/octet-stream')
        }
        
        with patch('app.utils.security.SecurityValidator') as mock_validator:
            # Mock security validator to reject the file
            mock_validator_instance = Mock()
            mock_validator_instance.validate_upload_file.return_value = {
                'is_secure': False,
                'issues': ['Invalid file extension']
            }
            mock_validator.return_value = mock_validator_instance
            
            response = self.client.post("/api/ingest", files=files)
            
            # Verify error response structure
            assert response.status_code == 400
            data = response.json()
            
            # Check error structure
            assert 'error' in data
            assert 'message' in data
            
            print("✓ Error responses have proper structure")
    
    def test_supported_file_types(self):
        """Test all supported file types"""
        test_cases = [
            ('test.pdf', create_test_pdf(), 'application/pdf'),
            ('test.txt', create_test_txt(), 'text/plain'),
            ('test.md', b"# Test Markdown\n\nContent", 'text/markdown'),
        ]
        
        for filename, content, content_type in test_cases:
            with patch('app.core.database.get_async_db') as mock_db, \
                 patch('app.services.document_service.DocumentService') as mock_service:
                
                # Mock database session
                mock_session = AsyncMock(spec=AsyncSession)
                mock_db.return_value = mock_session
                
                # Mock document service
                mock_doc_service = AsyncMock(spec=DocumentService)
                mock_service.return_value = mock_doc_service
                
                # Mock document creation
                mock_document = Mock(spec=Document)
                mock_document.id = f"123e4567-e89b-12d3-a456-42661417400{hash(filename) % 10}"
                mock_document.filename = filename
                mock_document.status = ProcessingStatus.PENDING
                mock_document.created_at = "2024-01-01T00:00:00Z"
                
                mock_doc_service.create_document.return_value = mock_document
                mock_doc_service.queue_for_processing.return_value = None
                
                # Test upload
                files = {
                    'file': (filename, BytesIO(content), content_type)
                }
                
                response = self.client.post("/api/ingest", files=files)
                
                # Verify successful upload
                assert response.status_code == 201, f"Failed to upload {filename}"
                data = response.json()
                assert data['filename'] == filename
                
        print("✓ All supported file types can be uploaded")

def run_tests():
    """Run all tests"""
    print("=" * 80)
    print("UPLOAD FUNCTIONALITY UNIT TESTS")
    print("=" * 80)
    print()
    
    test_instance = TestUploadFunctionality()
    
    tests = [
        test_instance.test_successful_pdf_upload_structure,
        test_instance.test_successful_txt_upload_structure,
        test_instance.test_empty_file_rejection,
        test_instance.test_no_file_rejection,
        test_instance.test_invalid_file_extension_rejection,
        test_instance.test_large_file_handling,
        test_instance.test_document_service_integration,
        test_instance.test_error_handling_structure,
        test_instance.test_supported_file_types,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_instance.setup_method()
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAIL: {test.__name__} - {e}")
            failed += 1
    
    print()
    print("-" * 50)
    print(f"Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All upload functionality unit tests passed!")
        return True
    else:
        print(f"❌ {failed} tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)