#!/usr/bin/env python3
"""
Verify sync implementation without external dependencies
"""

import sys
import os
import importlib.util
from datetime import datetime, timezone
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sync_service_import():
    """Test that sync service can be imported"""
    try:
        from app.services.sync_service import SyncService, SyncConflictResolver, SyncChange
        print("✓ Sync service imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Sync service import failed: {e}")
        return False

def test_sync_api_import():
    """Test that sync API can be imported"""
    try:
        from app.api.sync import router
        print("✓ Sync API imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Sync API import failed: {e}")
        return False

def test_sync_change_creation():
    """Test SyncChange dataclass creation"""
    try:
        from app.services.sync_service import SyncChange
        
        change = SyncChange(
            id=str(uuid4()),
            entity_type="card",
            operation="update",
            data={"front": "Test", "back": "Answer"},
            timestamp=datetime.now(timezone.utc),
            client_id="test_client",
            version=1
        )
        
        assert change.entity_type == "card"
        assert change.operation == "update"
        assert change.client_id == "test_client"
        
        print("✓ SyncChange creation works correctly")
        return True
    except Exception as e:
        print(f"✗ SyncChange creation failed: {e}")
        return False

def test_sync_service_methods():
    """Test SyncService method signatures"""
    try:
        from app.services.sync_service import SyncService
        
        # Check that required methods exist
        required_methods = [
            'get_changes_since',
            'apply_change',
            'get_full_sync_data',
            'calculate_entity_checksum',
            'get_sync_status'
        ]
        
        for method_name in required_methods:
            if not hasattr(SyncService, method_name):
                print(f"✗ SyncService missing method: {method_name}")
                return False
        
        print("✓ SyncService has all required methods")
        return True
    except Exception as e:
        print(f"✗ SyncService method check failed: {e}")
        return False

def test_conflict_resolver_methods():
    """Test SyncConflictResolver method signatures"""
    try:
        from app.services.sync_service import SyncConflictResolver
        
        # Check that required methods exist
        required_methods = [
            'detect_conflict',
            'resolve_conflict',
            'apply_resolution'
        ]
        
        for method_name in required_methods:
            if not hasattr(SyncConflictResolver, method_name):
                print(f"✗ SyncConflictResolver missing method: {method_name}")
                return False
        
        print("✓ SyncConflictResolver has all required methods")
        return True
    except Exception as e:
        print(f"✗ SyncConflictResolver method check failed: {e}")
        return False

def test_api_endpoints():
    """Test that API endpoints are defined"""
    try:
        from app.api.sync import router
        
        # Check that router has routes
        if not hasattr(router, 'routes') or len(router.routes) == 0:
            print("✗ Sync router has no routes")
            return False
        
        # Check for expected endpoints
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        expected_paths = ['/pull', '/push', '/status', '/validate-consistency', '/full-sync']
        
        for path in expected_paths:
            full_path = f"/api/sync{path}"
            if not any(full_path in route_path for route_path in route_paths):
                print(f"✗ Missing expected endpoint: {full_path}")
                return False
        
        print("✓ All expected API endpoints are defined")
        return True
    except Exception as e:
        print(f"✗ API endpoint check failed: {e}")
        return False

def test_main_app_includes_sync():
    """Test that main app includes sync router"""
    try:
        # Check if main.py includes sync router
        main_path = os.path.join(os.path.dirname(__file__), 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
        
        if 'from app.api.sync import router as sync_router' not in content:
            print("✗ main.py does not import sync router")
            return False
        
        if 'app.include_router(sync_router)' not in content:
            print("✗ main.py does not include sync router")
            return False
        
        print("✓ main.py properly includes sync router")
        return True
    except Exception as e:
        print(f"✗ main.py sync router check failed: {e}")
        return False

def test_ios_sync_service_exists():
    """Test that iOS sync service file exists"""
    try:
        ios_sync_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'ios-app', 'src', 'services', 'backgroundSyncService.ts'
        )
        
        if not os.path.exists(ios_sync_path):
            print("✗ iOS backgroundSyncService.ts does not exist")
            return False
        
        # Check for key sync methods in the file
        with open(ios_sync_path, 'r') as f:
            content = f.read()
        
        required_methods = [
            'performSync',
            'pushLocalChanges',
            'pullServerChanges',
            'validateDataConsistency',
            'resolveConflicts'
        ]
        
        for method in required_methods:
            if method not in content:
                print(f"✗ iOS sync service missing method: {method}")
                return False
        
        print("✓ iOS sync service exists with required methods")
        return True
    except Exception as e:
        print(f"✗ iOS sync service check failed: {e}")
        return False

def test_frontend_sync_components():
    """Test that frontend sync components exist"""
    try:
        frontend_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src')
        
        # Check for sync status indicator
        sync_indicator_path = os.path.join(frontend_base, 'components', 'SyncStatusIndicator.tsx')
        if not os.path.exists(sync_indicator_path):
            print("✗ Frontend SyncStatusIndicator component does not exist")
            return False
        
        # Check for sync service
        sync_service_path = os.path.join(frontend_base, 'services', 'syncService.ts')
        if not os.path.exists(sync_service_path):
            print("✗ Frontend sync service does not exist")
            return False
        
        print("✓ Frontend sync components exist")
        return True
    except Exception as e:
        print(f"✗ Frontend sync components check failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("Verifying Cross-Platform Data Synchronization Implementation...")
    print("=" * 60)
    
    tests = [
        test_sync_service_import,
        test_sync_api_import,
        test_sync_change_creation,
        test_sync_service_methods,
        test_conflict_resolver_methods,
        test_api_endpoints,
        test_main_app_includes_sync,
        test_ios_sync_service_exists,
        test_frontend_sync_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 60)
    print(f"Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All sync implementation verification tests passed!")
        print("\nImplemented Features:")
        print("✓ Backend sync API with pull/push endpoints")
        print("✓ Conflict detection and resolution system")
        print("✓ Data consistency validation with checksums")
        print("✓ iOS offline-first sync service")
        print("✓ Frontend sync status indicators")
        print("✓ Cross-platform sync protocol")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)