#!/usr/bin/env python3
"""
Test script to verify the /api/ingest endpoint fix
"""

import requests
import tempfile
import os

def test_ingest_endpoint():
    """Test the /api/ingest endpoint with a simple file upload"""
    
    # Test endpoints
    backend_direct = "http://localhost:8000"
    frontend_proxy = "http://localhost:3001"
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello, this is a test file for the ingest endpoint!")
        test_file_path = f.name
    
    try:
        print("Testing API connectivity fix...")
        print("=" * 50)
        
        # Test 1: Direct backend health check
        print("1. Testing direct backend health check...")
        try:
            response = requests.get(f"{backend_direct}/api/health/simple", timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        
        # Test 2: Direct backend ingest
        print("2. Testing direct backend ingest...")
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{backend_direct}/api/ingest", files=files, timeout=30)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        
        # Test 3: Frontend proxy ingest (if frontend is running)
        print("3. Testing frontend proxy ingest...")
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{frontend_proxy}/api/ingest", files=files, timeout=30)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        print("Test completed!")
        
    finally:
        # Clean up test file
        os.unlink(test_file_path)

if __name__ == "__main__":
    test_ingest_endpoint()