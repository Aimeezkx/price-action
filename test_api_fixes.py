#!/usr/bin/env python3
"""
Test script to verify API connectivity fixes
"""
import requests
import json
import time
import sys

def test_health_endpoints():
    """Test health check endpoints"""
    base_url = "http://localhost:8000"
    
    print("🏥 Testing health endpoints...")
    
    # Test simple health check
    try:
        response = requests.get(f"{base_url}/api/health/simple", timeout=5)
        print(f"✅ Simple health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Simple health check failed: {e}")
    
    # Test deep health check
    try:
        response = requests.get(f"{base_url}/api/health/deep", timeout=10)
        print(f"✅ Deep health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   DB: {data.get('checks', {}).get('db')}")
            print(f"   Redis: {data.get('checks', {}).get('redis')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Deep health check failed: {e}")

def test_cors():
    """Test CORS headers"""
    base_url = "http://localhost:8000"
    
    print("\n🌐 Testing CORS headers...")
    
    try:
        response = requests.options(f"{base_url}/api/health/simple", 
                                  headers={
                                      'Origin': 'http://localhost:3001',
                                      'Access-Control-Request-Method': 'GET'
                                  })
        print(f"✅ CORS preflight: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        for header, value in cors_headers.items():
            if value:
                print(f"   {header}: {value}")
            else:
                print(f"   ❌ Missing: {header}")
                
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

def test_upload_endpoint():
    """Test file upload endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n📁 Testing upload endpoint...")
    
    # Create a small test file
    test_content = b"This is a test PDF content for upload testing."
    
    try:
        files = {'file': ('test.pdf', test_content, 'application/pdf')}
        response = requests.post(f"{base_url}/api/ingest", files=files, timeout=30)
        
        print(f"✅ Upload test: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   Filename: {data.get('filename')}")
            print(f"   Size: {data.get('size')} bytes")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")

def test_documents_endpoint():
    """Test documents listing endpoint"""
    base_url = "http://localhost:8000"
    
    print("\n📄 Testing documents endpoint...")
    
    try:
        response = requests.get(f"{base_url}/api/documents", timeout=10)
        print(f"✅ Documents list: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} documents")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Documents test failed: {e}")

def main():
    print("🔧 API Connectivity Fix Verification")
    print("=" * 50)
    
    # Wait a moment for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(2)
    
    test_health_endpoints()
    test_cors()
    test_upload_endpoint()
    test_documents_endpoint()
    
    print("\n✅ Test completed!")
    print("\nNext steps:")
    print("1. Check docker-compose logs if any tests failed")
    print("2. Open http://localhost:3001 to test frontend")
    print("3. Try uploading a document through the UI")

if __name__ == "__main__":
    main()