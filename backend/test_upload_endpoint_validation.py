#!/usr/bin/env python3
"""
Test the upload endpoint with enhanced validation.
"""

import tempfile
import requests
from pathlib import Path


def test_upload_endpoint():
    """Test the upload endpoint with various file types."""
    base_url = "http://localhost:8000"
    upload_url = f"{base_url}/api/ingest"
    
    print("Testing upload endpoint with enhanced validation...")
    
    # Test 1: Valid PDF file
    print("\n1. Testing valid PDF file...")
    pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(pdf_content)
        f.flush()
        
        try:
            with open(f.name, 'rb') as pdf_file:
                files = {'file': ('test.pdf', pdf_file, 'application/pdf')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 201:
                    print("✓ Valid PDF accepted")
                else:
                    print(f"✗ Valid PDF rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing valid PDF: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 2: Valid text file
    print("\n2. Testing valid text file...")
    text_content = b'This is a valid text file with normal content.\nIt has multiple lines.'
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(text_content)
        f.flush()
        
        try:
            with open(f.name, 'rb') as text_file:
                files = {'file': ('test.txt', text_file, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 201:
                    print("✓ Valid text file accepted")
                else:
                    print(f"✗ Valid text file rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing valid text: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 3: Malicious script content
    print("\n3. Testing malicious script content...")
    malicious_content = b'<script>alert("XSS")</script>\nSome normal text here.'
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(malicious_content)
        f.flush()
        
        try:
            with open(f.name, 'rb') as malicious_file:
                files = {'file': ('malicious.txt', malicious_file, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Malicious script content rejected")
                    print(f"  Reason: {response.json().get('detail', 'No detail')}")
                else:
                    print(f"✗ Malicious script content not rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing malicious script: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 4: Invalid file extension
    print("\n4. Testing invalid file extension...")
    exe_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
    
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
        f.write(exe_content)
        f.flush()
        
        try:
            with open(f.name, 'rb') as exe_file:
                files = {'file': ('malicious.exe', exe_file, 'application/octet-stream')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Executable file rejected")
                    print(f"  Reason: {response.json().get('detail', 'No detail')}")
                else:
                    print(f"✗ Executable file not rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing executable: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 5: Oversized file
    print("\n5. Testing oversized file...")
    large_content = b'A' * (101 * 1024 * 1024)  # 101MB
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(large_content)
        f.flush()
        
        try:
            with open(f.name, 'rb') as large_file:
                files = {'file': ('large.txt', large_file, 'text/plain')}
                response = requests.post(upload_url, files=files, timeout=30)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Oversized file rejected")
                    print(f"  Reason: {response.json().get('detail', 'No detail')}")
                else:
                    print(f"✗ Oversized file not rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing oversized file: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    # Test 6: Empty file
    print("\n6. Testing empty file...")
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'')  # Empty file
        f.flush()
        
        try:
            with open(f.name, 'rb') as empty_file:
                files = {'file': ('empty.txt', empty_file, 'text/plain')}
                response = requests.post(upload_url, files=files)
                print(f"Status: {response.status_code}")
                if response.status_code == 400:
                    print("✓ Empty file rejected")
                    print(f"  Reason: {response.json().get('detail', 'No detail')}")
                else:
                    print(f"✗ Empty file not rejected: {response.text}")
        except Exception as e:
            print(f"✗ Error testing empty file: {e}")
        finally:
            Path(f.name).unlink(missing_ok=True)
    
    print("\nUpload endpoint validation tests completed!")


if __name__ == "__main__":
    test_upload_endpoint()