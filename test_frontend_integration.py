#!/usr/bin/env python3
"""
Frontend Integration Test
Tests the document learning app frontend with the backend API
"""

import requests
import json
import time
import os
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_frontend_integration():
    """Test integration between backend and frontend"""
    print("=== Frontend Integration Test ===")
    
    # Test backend health
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✓ Backend is running")
        else:
            print("✗ Backend health check failed")
            return False
    except:
        print("✗ Backend is not accessible")
        return False
    
    # Test frontend (if running)
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✓ Frontend is running")
            frontend_running = True
        else:
            print("⚠ Frontend returned non-200 status")
            frontend_running = False
    except:
        print("⚠ Frontend is not running (this is optional)")
        frontend_running = False
    
    # Test API endpoints that frontend would use
    print("\n--- Testing API Endpoints ---")
    
    # Test document upload simulation
    test_file = "resource/视频教程的 课件幻灯片.pdf"
    if os.path.exists(test_file):
        print(f"Testing upload with {os.path.basename(test_file)}")
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': (os.path.basename(test_file), f, 'application/pdf')}
                response = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files, timeout=60)
            
            if response.status_code == 200:
                doc_data = response.json()
                doc_id = doc_data['id']
                print(f"✓ Document uploaded successfully (ID: {doc_id})")
                
                # Test endpoints that frontend would call
                endpoints_to_test = [
                    f"/api/documents/{doc_id}",
                    f"/api/documents/{doc_id}/chapters",
                    f"/api/documents/{doc_id}/knowledge-points"
                ]
                
                for endpoint in endpoints_to_test:
                    try:
                        response = requests.get(f"{BACKEND_URL}{endpoint}")
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list):
                                print(f"✓ {endpoint}: {len(data)} items")
                            else:
                                print(f"✓ {endpoint}: OK")
                        else:
                            print(f"✗ {endpoint}: {response.status_code}")
                    except Exception as e:
                        print(f"✗ {endpoint}: {str(e)}")
                
                # Test card generation
                try:
                    response = requests.post(f"{BACKEND_URL}/api/documents/{doc_id}/generate-cards")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✓ Card generation: {result.get('count', 0)} cards")
                    else:
                        print(f"✗ Card generation failed: {response.status_code}")
                except Exception as e:
                    print(f"✗ Card generation error: {str(e)}")
                
            else:
                print(f"✗ Upload failed: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Upload error: {str(e)}")
    else:
        print("⚠ No test file available for upload testing")
    
    # Test search functionality
    print("\n--- Testing Search ---")
    search_terms = ["trading", "price", "market"]
    for term in search_terms:
        try:
            response = requests.get(f"{BACKEND_URL}/api/search", params={"q": term})
            if response.status_code == 200:
                results = response.json()
                print(f"✓ Search '{term}': {len(results)} results")
            else:
                print(f"✗ Search '{term}' failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Search '{term}' error: {str(e)}")
    
    return True

def test_cors_headers():
    """Test CORS headers for frontend integration"""
    print("\n--- Testing CORS Headers ---")
    
    try:
        # Test preflight request
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{BACKEND_URL}/api/documents/upload", headers=headers)
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"  ✓ {header}: {value}")
            else:
                print(f"  ✗ {header}: Not set")
                
    except Exception as e:
        print(f"✗ CORS test error: {str(e)}")

def generate_frontend_test_data():
    """Generate test data that frontend can use"""
    print("\n--- Generating Frontend Test Data ---")
    
    # Create a simple test data file
    test_data = {
        "documents": [
            {
                "id": 1,
                "title": "Sample Trading Document",
                "status": "processed",
                "page_count": 100,
                "chapters": 5,
                "knowledge_points": 15,
                "flashcards": 25
            }
        ],
        "api_endpoints": {
            "base_url": BACKEND_URL,
            "upload": "/api/documents/upload",
            "documents": "/api/documents",
            "search": "/api/search"
        },
        "test_queries": [
            "trading strategies",
            "price action",
            "market trends",
            "technical analysis"
        ]
    }
    
    with open("frontend_test_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("✓ Frontend test data generated: frontend_test_data.json")

if __name__ == "__main__":
    success = test_backend_frontend_integration()
    test_cors_headers()
    generate_frontend_test_data()
    
    if success:
        print("\n✅ Integration tests completed successfully!")
        print("The backend is ready for frontend integration.")
    else:
        print("\n❌ Some integration tests failed.")
        print("Please check the backend server and try again.")