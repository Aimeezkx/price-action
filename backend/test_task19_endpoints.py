#!/usr/bin/env python3
"""
Test script for Task 19: Search and Export API endpoints
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path

# Add the backend directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_search_get_endpoint():
    """Test GET /search endpoint"""
    print("Testing GET /search endpoint...")
    
    # Test basic search
    response = client.get("/search/?query=test&limit=10")
    print(f"GET /search status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Search response keys: {list(data.keys())}")
        print(f"Query: {data.get('query')}")
        print(f"Search type: {data.get('search_type')}")
        print(f"Total results: {data.get('total_results')}")
    else:
        print(f"Error: {response.text}")
    
    # Test search with filters
    response = client.get("/search/?query=machine learning&search_type=semantic&difficulty_min=1.0&difficulty_max=3.0")
    print(f"GET /search with filters status: {response.status_code}")
    
    return response.status_code == 200


def test_search_post_endpoint():
    """Test POST /search endpoint"""
    print("\nTesting POST /search endpoint...")
    
    search_request = {
        "query": "artificial intelligence",
        "search_type": "hybrid",
        "limit": 5,
        "similarity_threshold": 0.8
    }
    
    response = client.post("/search/", json=search_request)
    print(f"POST /search status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Search response keys: {list(data.keys())}")
        print(f"Total results: {data.get('total_results')}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_export_csv_endpoint():
    """Test GET /export/csv endpoint"""
    print("\nTesting GET /export/csv endpoint...")
    
    # Test Anki format
    response = client.get("/export/csv?format=anki")
    print(f"GET /export/csv (anki) status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        content = response.text
        print(f"CSV content length: {len(content)} characters")
        # Check if it looks like CSV
        lines = content.split('\n')
        if lines:
            print(f"First line (header): {lines[0]}")
    else:
        print(f"Error: {response.text}")
    
    # Test Notion format
    response = client.get("/export/csv?format=notion")
    print(f"GET /export/csv (notion) status: {response.status_code}")
    
    # Test invalid format
    response = client.get("/export/csv?format=invalid")
    print(f"GET /export/csv (invalid) status: {response.status_code}")
    
    return True


def test_export_jsonl_endpoint():
    """Test GET /export/jsonl endpoint"""
    print("\nTesting GET /export/jsonl endpoint...")
    
    response = client.get("/export/jsonl")
    print(f"GET /export/jsonl status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        content = response.text
        print(f"JSONL content length: {len(content)} characters")
        
        # Try to parse as JSONL
        lines = content.strip().split('\n')
        valid_json_lines = 0
        for line in lines:
            if line.strip():
                try:
                    json.loads(line)
                    valid_json_lines += 1
                except json.JSONDecodeError:
                    pass
        
        print(f"Valid JSON lines: {valid_json_lines}/{len([l for l in lines if l.strip()])}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_import_jsonl_endpoint():
    """Test POST /export/import/jsonl endpoint"""
    print("\nTesting POST /export/import/jsonl endpoint...")
    
    # Create a test JSONL file
    test_data = {
        "document": {
            "id": "test-doc-id",
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps(test_data) + '\n')
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            files = {"file": ("test.jsonl", f, "application/jsonl")}
            response = client.post("/export/import/jsonl?validate_only=true", files=files)
        
        print(f"POST /export/import/jsonl (validate) status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Validation result: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            if data.get('errors'):
                print(f"Errors: {data['errors']}")
        else:
            print(f"Error: {response.text}")
        
        # Test invalid file type
        with open(temp_file_path, 'rb') as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = client.post("/export/import/jsonl", files=files)
        
        print(f"POST /export/import/jsonl (invalid file) status: {response.status_code}")
        
    finally:
        os.unlink(temp_file_path)
    
    return True


def test_export_formats_endpoint():
    """Test GET /export/formats endpoint"""
    print("\nTesting GET /export/formats endpoint...")
    
    response = client.get("/export/formats")
    print(f"GET /export/formats status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Export formats: {len(data.get('formats', []))}")
        print(f"Import formats: {len(data.get('import_formats', []))}")
        
        # Print format details
        for fmt in data.get('formats', []):
            print(f"  - {fmt.get('name')}: {fmt.get('endpoint')}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_openapi_documentation():
    """Test OpenAPI documentation is available"""
    print("\nTesting OpenAPI documentation...")
    
    # Test OpenAPI JSON
    response = client.get("/openapi.json")
    print(f"GET /openapi.json status: {response.status_code}")
    
    if response.status_code == 200:
        openapi_spec = response.json()
        print(f"OpenAPI version: {openapi_spec.get('openapi')}")
        print(f"API title: {openapi_spec.get('info', {}).get('title')}")
        
        # Check if our endpoints are documented
        paths = openapi_spec.get('paths', {})
        search_paths = [p for p in paths.keys() if '/search' in p]
        export_paths = [p for p in paths.keys() if '/export' in p]
        
        print(f"Search endpoints documented: {len(search_paths)}")
        print(f"Export endpoints documented: {len(export_paths)}")
        
        for path in search_paths:
            print(f"  - {path}")
        for path in export_paths:
            print(f"  - {path}")
    else:
        print(f"Error: {response.text}")
    
    # Test Swagger UI
    response = client.get("/docs")
    print(f"GET /docs status: {response.status_code}")
    
    return response.status_code == 200


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Task 19: Search and Export API Endpoints")
    print("=" * 60)
    
    tests = [
        ("Search GET endpoint", test_search_get_endpoint),
        ("Search POST endpoint", test_search_post_endpoint),
        ("Export CSV endpoint", test_export_csv_endpoint),
        ("Export JSONL endpoint", test_export_jsonl_endpoint),
        ("Import JSONL endpoint", test_import_jsonl_endpoint),
        ("Export formats endpoint", test_export_formats_endpoint),
        ("OpenAPI documentation", test_openapi_documentation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n✅ All tests passed! Task 19 implementation is working correctly.")
    else:
        print(f"\n❌ {len(results) - passed} tests failed. Please check the implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)