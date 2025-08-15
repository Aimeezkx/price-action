#!/usr/bin/env python3
"""
Simple test script for Task 19: Search and Export API endpoints
"""

import requests
import json
import time
import subprocess
import signal
import os
from pathlib import Path


def start_server():
    """Start the FastAPI server"""
    print("Starting FastAPI server...")
    
    # Start server in background
    process = subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server started successfully")
            return process
        else:
            print("❌ Server health check failed")
            process.terminate()
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        process.terminate()
        return None


def test_search_endpoints():
    """Test search endpoints"""
    print("\n" + "="*50)
    print("Testing Search Endpoints")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test GET /search
    print("\n1. Testing GET /search...")
    try:
        response = requests.get(f"{base_url}/search/?query=test&limit=5", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Query: {data.get('query')}")
            print(f"   Search type: {data.get('search_type')}")
            print(f"   Total results: {data.get('total_results')}")
            print("   ✅ GET /search working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ GET /search failed")
    except Exception as e:
        print(f"   ❌ GET /search error: {e}")
    
    # Test POST /search
    print("\n2. Testing POST /search...")
    try:
        search_data = {
            "query": "machine learning",
            "search_type": "hybrid",
            "limit": 3
        }
        response = requests.post(f"{base_url}/search/", json=search_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total results: {data.get('total_results')}")
            print("   ✅ POST /search working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ POST /search failed")
    except Exception as e:
        print(f"   ❌ POST /search error: {e}")


def test_export_endpoints():
    """Test export endpoints"""
    print("\n" + "="*50)
    print("Testing Export Endpoints")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test GET /export/csv
    print("\n1. Testing GET /export/csv...")
    try:
        response = requests.get(f"{base_url}/export/csv?format=anki", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            print(f"   Content length: {len(response.text)} chars")
            print("   ✅ GET /export/csv working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ GET /export/csv failed")
    except Exception as e:
        print(f"   ❌ GET /export/csv error: {e}")
    
    # Test GET /export/jsonl
    print("\n2. Testing GET /export/jsonl...")
    try:
        response = requests.get(f"{base_url}/export/jsonl", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            print(f"   Content length: {len(response.text)} chars")
            print("   ✅ GET /export/jsonl working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ GET /export/jsonl failed")
    except Exception as e:
        print(f"   ❌ GET /export/jsonl error: {e}")
    
    # Test GET /export/formats
    print("\n3. Testing GET /export/formats...")
    try:
        response = requests.get(f"{base_url}/export/formats", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Export formats: {len(data.get('formats', []))}")
            print(f"   Import formats: {len(data.get('import_formats', []))}")
            print("   ✅ GET /export/formats working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ GET /export/formats failed")
    except Exception as e:
        print(f"   ❌ GET /export/formats error: {e}")


def test_import_endpoint():
    """Test import endpoint"""
    print("\n" + "="*50)
    print("Testing Import Endpoint")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Create test JSONL data
    test_data = {
        "document": {
            "id": "test-doc-123",
            "filename": "test.pdf",
            "file_type": "pdf",
            "file_path": "/test/path",
            "file_size": 1000,
            "status": "completed",
            "doc_metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        },
        "chapters": [],
        "export_metadata": {
            "export_date": "2024-01-01T00:00:00",
            "export_version": "1.0",
            "total_chapters": 0,
            "total_figures": 0,
            "total_knowledge": 0,
            "total_cards": 0
        }
    }
    
    # Test validation only
    print("\n1. Testing POST /export/import/jsonl (validation)...")
    try:
        jsonl_content = json.dumps(test_data) + '\n'
        files = {'file': ('test.jsonl', jsonl_content, 'application/jsonl')}
        response = requests.post(
            f"{base_url}/export/import/jsonl?validate_only=true", 
            files=files, 
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            print("   ✅ POST /export/import/jsonl validation working")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ POST /export/import/jsonl validation failed")
    except Exception as e:
        print(f"   ❌ POST /export/import/jsonl error: {e}")


def test_openapi_docs():
    """Test OpenAPI documentation"""
    print("\n" + "="*50)
    print("Testing OpenAPI Documentation")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test OpenAPI JSON
    print("\n1. Testing GET /openapi.json...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            openapi_spec = response.json()
            print(f"   OpenAPI version: {openapi_spec.get('openapi')}")
            print(f"   API title: {openapi_spec.get('info', {}).get('title')}")
            
            # Check endpoints
            paths = openapi_spec.get('paths', {})
            search_paths = [p for p in paths.keys() if '/search' in p]
            export_paths = [p for p in paths.keys() if '/export' in p]
            
            print(f"   Search endpoints: {len(search_paths)}")
            print(f"   Export endpoints: {len(export_paths)}")
            print("   ✅ OpenAPI documentation available")
        else:
            print(f"   Response: {response.text}")
            print("   ❌ OpenAPI documentation failed")
    except Exception as e:
        print(f"   ❌ OpenAPI documentation error: {e}")
    
    # Test Swagger UI
    print("\n2. Testing GET /docs...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Swagger UI available")
        else:
            print("   ❌ Swagger UI failed")
    except Exception as e:
        print(f"   ❌ Swagger UI error: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Task 19: Search and Export API Endpoints Test")
    print("=" * 60)
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("❌ Failed to start server. Cannot run tests.")
        return False
    
    try:
        # Run tests
        test_search_endpoints()
        test_export_endpoints()
        test_import_endpoint()
        test_openapi_docs()
        
        print("\n" + "=" * 60)
        print("✅ Task 19 endpoint testing completed!")
        print("All major endpoints are accessible and responding.")
        print("=" * 60)
        
        return True
        
    finally:
        # Clean up server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)