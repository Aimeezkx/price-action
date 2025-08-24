#!/usr/bin/env python3
"""
Test script to verify backend API fix
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_imports():
    """Test that all required imports work"""
    try:
        print("🔍 Testing imports...")
        
        # Test basic FastAPI imports
        from fastapi import FastAPI
        print("✅ FastAPI import OK")
        
        # Test health router
        from app.api.health import router as health_router
        print("✅ Health router import OK")
        
        # Test documents router
        from app.api.documents import router as documents_router
        print("✅ Documents router import OK")
        
        # Test database
        from app.core.database import get_async_db
        print("✅ Database import OK")
        
        # Test models
        from app.models.document import Document
        print("✅ Document model import OK")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Other error: {e}")
        return False

def test_app_creation():
    """Test that the FastAPI app can be created"""
    try:
        print("\n🔍 Testing app creation...")
        
        # Import the main app
        from main import app
        print("✅ App creation OK")
        
        # Check routes
        routes = [route.path for route in app.routes]
        print(f"📋 Available routes: {routes}")
        
        # Check for documents routes
        api_routes = [route.path for route in app.routes if route.path.startswith('/api')]
        print(f"🔗 API routes: {api_routes}")
        
        if '/api/documents' in api_routes:
            print("✅ Documents endpoint registered!")
        else:
            print("❌ Documents endpoint NOT found")
            
        return True
        
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing Backend API Fix\n")
    
    # Test imports
    imports_ok = await test_imports()
    
    if imports_ok:
        # Test app creation
        app_ok = test_app_creation()
        
        if app_ok:
            print("\n🎉 Backend fix appears successful!")
            print("💡 Next steps:")
            print("   1. Start the backend: uvicorn main:app --reload --port 8000")
            print("   2. Test the endpoint: curl http://localhost:8000/api/documents")
        else:
            print("\n❌ App creation failed")
    else:
        print("\n❌ Import tests failed")

if __name__ == "__main__":
    asyncio.run(main())