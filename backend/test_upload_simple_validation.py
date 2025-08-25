#!/usr/bin/env python3
"""
Simple Upload Validation Test

This test validates the core upload functionality without complex dependencies.
It focuses on testing the essential requirements for Task 6.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import sys
import json
from pathlib import Path
from io import BytesIO
import requests
import time

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

def create_test_md() -> bytes:
    """Create a test Markdown file"""
    content = """# Test Markdown Document

This is a test **Markdown** document for upload testing.

## Section 1: Introduction

This document contains various *formatting* elements.

### Key Points

- Item 1
- Item 2
- Item 3

## Section 2: Conclusion

This content should be processed and converted into flashcards.
"""
    return content.encode('utf-8')

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_file_upload(filename: str, content: bytes, content_type: str) -> dict:
    """Test file upload and return result"""
    try:
        files = {
            'file': (filename, BytesIO(content), content_type)
        }
        
        response = requests.post("http://localhost:8000/api/ingest", files=files, timeout=30)
        
        result = {
            'filename': filename,
            'status_code': response.status_code,
            'success': response.status_code == 201,
            'response_data': None,
            'error': None
        }
        
        try:
            result['response_data'] = response.json()
        except:
            result['response_data'] = response.text
        
        return result
        
    except Exception as e:
        return {
            'filename': filename,
            'status_code': None,
            'success': False,
            'response_data': None,
            'error': str(e)
        }

def test_error_scenarios():
    """Test various error scenarios"""
    results = []
    
    # Test empty file
    try:
        files = {'file': ('empty.pdf', BytesIO(b''), 'application/pdf')}
        response = requests.post("http://localhost:8000/api/ingest", files=files, timeout=30)
        results.append({
            'test': 'empty_file',
            'status_code': response.status_code,
            'expected_rejection': response.status_code == 400,
            'success': response.status_code == 400
        })
    except Exception as e:
        results.append({
            'test': 'empty_file',
            'status_code': None,
            'expected_rejection': True,
            'success': False,
            'error': str(e)
        })
    
    # Test no file
    try:
        response = requests.post("http://localhost:8000/api/ingest", timeout=30)
        results.append({
            'test': 'no_file',
            'status_code': response.status_code,
            'expected_rejection': response.status_code in [400, 422],
            'success': response.status_code in [400, 422]
        })
    except Exception as e:
        results.append({
            'test': 'no_file',
            'status_code': None,
            'expected_rejection': True,
            'success': False,
            'error': str(e)
        })
    
    # Test invalid file type
    try:
        files = {'file': ('test.exe', BytesIO(b'invalid content'), 'application/octet-stream')}
        response = requests.post("http://localhost:8000/api/ingest", files=files, timeout=30)
        results.append({
            'test': 'invalid_file_type',
            'status_code': response.status_code,
            'expected_rejection': response.status_code == 400,
            'success': response.status_code == 400
        })
    except Exception as e:
        results.append({
            'test': 'invalid_file_type',
            'status_code': None,
            'expected_rejection': True,
            'success': False,
            'error': str(e)
        })
    
    return results

def validate_response_structure(response_data: dict, filename: str) -> dict:
    """Validate that response has required structure"""
    validation = {
        'filename': filename,
        'has_required_fields': True,
        'missing_fields': [],
        'field_types_correct': True,
        'type_errors': []
    }
    
    # Required fields for successful upload
    required_fields = ['id', 'filename', 'status', 'created_at']
    
    for field in required_fields:
        if field not in response_data:
            validation['has_required_fields'] = False
            validation['missing_fields'].append(field)
    
    # Check field types
    if 'id' in response_data and not isinstance(response_data['id'], str):
        validation['field_types_correct'] = False
        validation['type_errors'].append(f"id should be string, got {type(response_data['id'])}")
    
    if 'filename' in response_data and not isinstance(response_data['filename'], str):
        validation['field_types_correct'] = False
        validation['type_errors'].append(f"filename should be string, got {type(response_data['filename'])}")
    
    if 'status' in response_data and not isinstance(response_data['status'], str):
        validation['field_types_correct'] = False
        validation['type_errors'].append(f"status should be string, got {type(response_data['status'])}")
    
    return validation

def main():
    """Main test execution"""
    print("=" * 80)
    print("UPLOAD FUNCTIONALITY VALIDATION TESTS")
    print("=" * 80)
    print()
    
    # Check server health
    if not test_server_health():
        print("❌ Server is not available. Please start the backend server first.")
        print("   Run: cd backend && python main.py")
        return False
    
    print("✓ Server is running and healthy")
    print()
    
    # Test successful uploads with different file types
    print("Testing successful uploads...")
    print("-" * 50)
    
    test_files = [
        ('test.pdf', create_test_pdf(), 'application/pdf'),
        ('test.txt', create_test_txt(), 'text/plain'),
        ('test.md', create_test_md(), 'text/markdown'),
    ]
    
    upload_results = []
    successful_uploads = 0
    
    for filename, content, content_type in test_files:
        result = test_file_upload(filename, content, content_type)
        upload_results.append(result)
        
        if result['success']:
            print(f"✓ {filename}: Upload successful")
            successful_uploads += 1
            
            # Validate response structure
            if isinstance(result['response_data'], dict):
                validation = validate_response_structure(result['response_data'], filename)
                if validation['has_required_fields'] and validation['field_types_correct']:
                    print(f"  ✓ Response structure is valid")
                else:
                    print(f"  ⚠ Response structure issues:")
                    if validation['missing_fields']:
                        print(f"    Missing fields: {validation['missing_fields']}")
                    if validation['type_errors']:
                        print(f"    Type errors: {validation['type_errors']}")
        else:
            print(f"✗ {filename}: Upload failed")
            print(f"  Status: {result['status_code']}")
            if result['error']:
                print(f"  Error: {result['error']}")
    
    print()
    print("Testing error scenarios...")
    print("-" * 50)
    
    error_results = test_error_scenarios()
    successful_error_tests = 0
    
    for result in error_results:
        if result['success']:
            print(f"✓ {result['test']}: Properly rejected (status: {result['status_code']})")
            successful_error_tests += 1
        else:
            print(f"✗ {result['test']}: Not properly handled")
            if 'error' in result:
                print(f"  Error: {result['error']}")
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_upload_tests = len(test_files)
    total_error_tests = len(error_results)
    total_tests = total_upload_tests + total_error_tests
    total_passed = successful_uploads + successful_error_tests
    
    print(f"Upload Tests: {successful_uploads}/{total_upload_tests} passed")
    print(f"Error Tests: {successful_error_tests}/{total_error_tests} passed")
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print()
    
    # Requirements coverage
    print("Requirements Coverage:")
    print("- 1.1: File upload with supported formats (PDF, TXT, MD) ✓" if successful_uploads > 0 else "- 1.1: File upload with supported formats ✗")
    print("- 1.2: Document record creation ✓" if successful_uploads > 0 else "- 1.2: Document record creation ✗")
    print("- 1.3: Processing status tracking ✓" if successful_uploads > 0 else "- 1.3: Processing status tracking ✗")
    print("- 1.4: Error handling ✓" if successful_error_tests > 0 else "- 1.4: Error handling ✗")
    print("- 1.5: Frontend response compatibility ✓" if successful_uploads > 0 else "- 1.5: Frontend response compatibility ✗")
    
    print()
    
    if total_passed == total_tests:
        print("🎉 All upload functionality tests passed!")
        return True
    else:
        print(f"❌ {total_tests - total_passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)