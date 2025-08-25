#!/usr/bin/env python3
"""
Test validation edge cases without hitting rate limits.
"""

import tempfile
import requests
import time
from pathlib import Path


def test_specific_validation_cases():
    """Test specific validation cases that were failing."""
    base_url = "http://localhost:8000"
    upload_url = f"{base_url}/api/ingest"
    
    print("Testing specific validation edge cases...")
    
    # Test empty file
    print("\n1. Testing empty file...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'')
        f.flush()
        
        try:
            time.sleep(3)  # Wait to avoid rate limit
            with open(f.name, 'rb') as file_obj:
                files = {'file': ('empty.txt', file_obj, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Empty file correctly rejected")
                elif response.status_code == 429:
                    print("⚠️ Rate limited - validation logic not tested")
                else:
                    print(f"✗ Unexpected status: {response.status_code}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test path traversal
    print("\n2. Testing path traversal filename...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'Valid content')
        f.flush()
        
        try:
            time.sleep(3)  # Wait to avoid rate limit
            with open(f.name, 'rb') as file_obj:
                files = {'file': ('../../../etc/passwd', file_obj, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Path traversal correctly rejected")
                elif response.status_code == 429:
                    print("⚠️ Rate limited - validation logic not tested")
                else:
                    print(f"✗ Unexpected status: {response.status_code}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test reserved filename
    print("\n3. Testing reserved filename...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'Valid content')
        f.flush()
        
        try:
            time.sleep(3)  # Wait to avoid rate limit
            with open(f.name, 'rb') as file_obj:
                files = {'file': ('CON.txt', file_obj, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Reserved filename correctly rejected")
                elif response.status_code == 429:
                    print("⚠️ Rate limited - validation logic not tested")
                else:
                    print(f"✗ Unexpected status: {response.status_code}")
        finally:
            Path(f.name).unlink(missing_ok=True)


def test_validation_functions_directly():
    """Test validation functions directly without HTTP requests."""
    print("\n" + "="*60)
    print("Testing validation functions directly...")
    
    from app.utils.file_validation import FileValidator
    from app.utils.security import SecurityValidator
    
    validator = FileValidator()
    security_validator = SecurityValidator()
    
    # Test 1: Empty file
    print("\n1. Testing empty file validation...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'')
        f.flush()
        
        try:
            result = validator.validate_file_upload(Path(f.name))
            print(f"Valid: {result.is_valid}")
            print(f"Error: {result.error_message}")
            if not result.is_valid and "too small" in result.error_message.lower():
                print("✓ Empty file correctly rejected by FileValidator")
            else:
                print("✗ Empty file validation failed")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 2: Path traversal filename
    print("\n2. Testing path traversal filename validation...")
    
    class MockUploadFile:
        def __init__(self, filename, content, content_type, size):
            self.filename = filename
            self.content = content
            self.content_type = content_type
            self.size = size
    
    upload_file = MockUploadFile('../../../etc/passwd', b'content', 'text/plain', 7)
    result = security_validator.validate_upload_file(upload_file)
    
    print(f"Secure: {result['is_secure']}")
    print(f"Issues: {result['issues']}")
    if not result['is_secure'] and any('path traversal' in issue.lower() for issue in result['issues']):
        print("✓ Path traversal correctly rejected by SecurityValidator")
    else:
        print("✗ Path traversal validation failed")
    
    # Test 3: Reserved filename
    print("\n3. Testing reserved filename validation...")
    upload_file = MockUploadFile('CON.txt', b'content', 'text/plain', 7)
    result = security_validator.validate_upload_file(upload_file)
    
    print(f"Secure: {result['is_secure']}")
    print(f"Issues: {result['issues']}")
    if not result['is_secure'] and any('reserved filename' in issue.lower() for issue in result['issues']):
        print("✓ Reserved filename correctly rejected by SecurityValidator")
    else:
        print("✗ Reserved filename validation failed")
    
    # Test 4: Script content in text file
    print("\n4. Testing script content validation...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'<script>alert("XSS")</script>')
        f.flush()
        
        try:
            result = validator.validate_file_upload(Path(f.name))
            print(f"Valid: {result.is_valid}")
            print(f"Error: {result.error_message}")
            if not result.is_valid and ("malicious" in result.error_message.lower() or "dangerous" in result.error_message.lower()):
                print("✓ Script content correctly rejected by FileValidator")
            else:
                print("✗ Script content validation failed")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 5: Valid file should pass
    print("\n5. Testing valid file...")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'This is valid text content with normal characters.')
        f.flush()
        
        try:
            result = validator.validate_file_upload(Path(f.name))
            print(f"Valid: {result.is_valid}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            if result.warnings:
                print(f"Warnings: {result.warnings}")
            
            if result.is_valid:
                print("✓ Valid file correctly accepted by FileValidator")
            else:
                print("✗ Valid file incorrectly rejected")
        finally:
            Path(f.name).unlink(missing_ok=True)


if __name__ == "__main__":
    # Test HTTP endpoint (may hit rate limits)
    test_specific_validation_cases()
    
    # Test validation functions directly (no rate limits)
    test_validation_functions_directly()
    
    print("\n" + "="*60)
    print("Validation testing completed!")