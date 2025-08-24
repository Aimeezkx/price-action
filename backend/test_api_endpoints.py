#!/usr/bin/env python3
"""
Test API endpoints to verify they work
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient

def test_endpoints():
    """Test key API endpoints"""
    try:
        print("🔍 Testing API endpoints...")
        
        # Import the app
        from main import app
        
        # Create test client
        client = TestClient(app)
        
        # Test root endpoint
        print("\n📍 Testing root endpoint...")
        response = client.get("/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test health endpoint
        print("\n📍 Testing health endpoint...")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
        
        # Test documents endpoint (this was the failing one)
        print("\n📍 Testing documents endpoint...")
        response = client.get("/api/documents")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("✅ Documents endpoint is working!")
        else:
            print(f"   Error: {response.text}")
            print("❌ Documents endpoint still failing")
        
        # Test OpenAPI docs
        print("\n📍 Testing OpenAPI docs...")
        response = client.get("/docs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API docs are available")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing API Endpoints\n")
    
    success = test_endpoints()
    
    if success:
        print("\n🎉 API endpoint tests completed!")
        print("💡 The /api/documents endpoint should now work in the frontend")
    else:
        print("\n❌ API endpoint tests failed")

if __name__ == "__main__":
    main()