#!/usr/bin/env python3
"""
Comprehensive test of upload endpoint with enhanced validation.
"""

import tempfile
import requests
import json
from pathlib import Path


def test_comprehensive_upload_validation():
    """Test comprehensive upload validation features."""
    base_url = "http://localhost:8000"
    upload_url = f"{base_url}/api/ingest"
    
    print("Testing comprehensive upload validation...")
    
    test_cases = [
        {
            "name": "Valid PDF file",
            "content": b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF',
            "filename": "valid.pdf",
            "content_type": "application/pdf",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Valid text file",
            "content": b'This is a valid text file.\nWith multiple lines of normal content.',
            "filename": "valid.txt",
            "content_type": "text/plain",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Valid markdown file",
            "content": b'# Test Markdown\n\nThis is **valid** markdown content.\n\n- Item 1\n- Item 2',
            "filename": "valid.md",
            "content_type": "text/markdown",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Script injection in text",
            "content": b'<script>alert("XSS attack")</script>\nSome normal text.',
            "filename": "malicious.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "PHP code injection",
            "content": b'<?php\necho "Hello";\nsystem($_GET["cmd"]);\n?>',
            "filename": "malicious.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "JavaScript protocol injection",
            "content": b'Click here: javascript:alert("XSS")\nNormal text.',
            "filename": "malicious.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Suspicious executable URL",
            "content": b'Download from: http://malicious.com/virus.exe\nOther content.',
            "filename": "suspicious.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Null bytes in text",
            "content": b'Normal text\x00with null byte',
            "filename": "null.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Executable file",
            "content": b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00',
            "filename": "malicious.exe",
            "content_type": "application/octet-stream",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Invalid file extension",
            "content": b'Some content',
            "filename": "test.js",
            "content_type": "application/javascript",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Empty file",
            "content": b'',
            "filename": "empty.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Path traversal filename",
            "content": b'Valid content',
            "filename": "../../../etc/passwd",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "Reserved filename",
            "content": b'Valid content',
            "filename": "CON.txt",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        },
        {
            "name": "PDF with JavaScript (should warn but pass)",
            "content": b'%PDF-1.4\n/JavaScript (alert("test"))\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF',
            "filename": "js_pdf.pdf",
            "content_type": "application/pdf",
            "expected_status": 201,
            "should_pass": True
        },
        {
            "name": "Mismatched content type",
            "content": b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF',
            "filename": "test.pdf",
            "content_type": "text/plain",
            "expected_status": 400,
            "should_pass": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_case['content'])
            temp_file.flush()
            
            try:
                with open(temp_file.name, 'rb') as file_obj:
                    files = {
                        'file': (
                            test_case['filename'], 
                            file_obj, 
                            test_case['content_type']
                        )
                    }
                    
                    response = requests.post(upload_url, files=files, timeout=30)
                    
                    # Add delay to avoid rate limiting
                    import time
                    time.sleep(2)
                    
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == test_case['expected_status']:
                        if test_case['should_pass']:
                            print("   ✓ PASS - Valid file accepted")
                        else:
                            print("   ✓ PASS - Invalid file rejected")
                            try:
                                error_detail = response.json().get('detail', 'No detail provided')
                                print(f"   Reason: {error_detail}")
                            except:
                                print("   Reason: Could not parse error response")
                        passed += 1
                    else:
                        print(f"   ✗ FAIL - Expected {test_case['expected_status']}, got {response.status_code}")
                        try:
                            print(f"   Response: {response.text}")
                        except:
                            print("   Response: Could not read response")
                        failed += 1
                        
            except Exception as e:
                print(f"   ✗ FAIL - Exception: {e}")
                failed += 1
            finally:
                Path(temp_file.name).unlink(missing_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced file validation is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the validation logic.")
    
    return failed == 0


if __name__ == "__main__":
    success = test_comprehensive_upload_validation()
    exit(0 if success else 1)