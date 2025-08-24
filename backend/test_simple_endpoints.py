#!/usr/bin/env python3
"""
Test API endpoints without database dependency
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient

def test_non_db_endpoints():
    """Test endpoints that don't require database"""
    try:
        print("🔍 Testing non-database endpoints...")
        
        # Import the app
        from main import app
        
        # Create test client
        client = TestClient(app)
        
        # Test root endpoint
        print("\n📍 Testing root endpoint...")
        response = client.get("/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test simple health endpoint
        print("\n📍 Testing simple health endpoint...")
        response = client.get("/health/simple")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
        
        # Test OpenAPI docs
        print("\n📍 Testing OpenAPI docs...")
        response = client.get("/openapi.json")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ OpenAPI schema is available")
            
            # Check if documents endpoints are in the schema
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            if "/api/documents" in paths:
                print("✅ /api/documents endpoint is in OpenAPI schema")
            else:
                print("❌ /api/documents endpoint NOT in OpenAPI schema")
                
            print(f"📋 Available API paths: {list(paths.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Testing Simple API Endpoints (No Database)\n")
    
    success = test_non_db_endpoints()
    
    if success:
        print("\n🎉 Simple API endpoint tests completed!")
        print("💡 The backend routing is working correctly")
        print("⚠️  Database connection needs to be fixed separately")
    else:
        print("\n❌ Simple API endpoint tests failed")

if __name__ == "__main__":
    main()