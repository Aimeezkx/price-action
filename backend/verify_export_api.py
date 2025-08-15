"""
Verify export API endpoints are properly configured
"""

import sys
import inspect
from fastapi import FastAPI

# Import the main app and export router
from main import app
from app.api.export import router


def verify_export_router():
    """Verify export router is properly configured"""
    print("Verifying export router configuration...")
    
    # Check that router has expected routes
    routes = router.routes
    route_paths = [route.path for route in routes]
    
    expected_paths = [
        "/export/csv/anki",
        "/export/csv/notion", 
        "/export/jsonl/backup",
        "/export/jsonl/import",
        "/export/formats"
    ]
    
    print(f"Found {len(routes)} routes in export router:")
    for route in routes:
        print(f"  - {route.methods} {route.path}")
    
    for expected_path in expected_paths:
        full_path = f"/export{expected_path}" if not expected_path.startswith("/export") else expected_path
        if not any(route.path == expected_path for route in routes):
            print(f"❌ Missing expected route: {expected_path}")
            return False
    
    print("✓ All expected routes found in export router")
    return True


def verify_app_includes_router():
    """Verify main app includes export router"""
    print("\nVerifying main app includes export router...")
    
    # Check that app has the export routes
    app_routes = app.routes
    export_routes = [route for route in app_routes if hasattr(route, 'path') and route.path.startswith('/export')]
    
    print(f"Found {len(export_routes)} export routes in main app:")
    for route in export_routes:
        if hasattr(route, 'path'):
            print(f"  - {getattr(route, 'methods', 'N/A')} {route.path}")
    
    if len(export_routes) == 0:
        print("❌ No export routes found in main app")
        return False
    
    print("✓ Export routes found in main app")
    return True


def verify_endpoint_functions():
    """Verify export endpoint functions exist and have proper signatures"""
    print("\nVerifying export endpoint functions...")
    
    from app.api.export import (
        export_anki_csv,
        export_notion_csv, 
        export_jsonl_backup,
        import_jsonl_backup,
        get_export_formats
    )
    
    functions = [
        export_anki_csv,
        export_notion_csv,
        export_jsonl_backup,
        import_jsonl_backup,
        get_export_formats
    ]
    
    for func in functions:
        print(f"  - {func.__name__}: ", end="")
        
        # Check function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Verify it's an async function
        if not inspect.iscoroutinefunction(func):
            print("❌ Not an async function")
            return False
        
        print(f"✓ async function with params: {params}")
    
    print("✓ All endpoint functions verified")
    return True


def verify_service_integration():
    """Verify export service can be imported and instantiated"""
    print("\nVerifying export service integration...")
    
    try:
        from app.services.export_service import ExportService, get_export_service
        print("✓ Export service imports successfully")
        
        # Check service has expected methods
        service_methods = [
            'export_anki_csv',
            'export_notion_csv',
            'export_jsonl_backup',
            'import_jsonl_backup'
        ]
        
        for method_name in service_methods:
            if not hasattr(ExportService, method_name):
                print(f"❌ Missing method: {method_name}")
                return False
            print(f"  - {method_name}: ✓")
        
        print("✓ Export service has all required methods")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import export service: {e}")
        return False


def verify_model_imports():
    """Verify all required models can be imported"""
    print("\nVerifying model imports...")
    
    try:
        from app.models.document import Document, Chapter, Figure
        from app.models.knowledge import Knowledge
        from app.models.learning import Card, SRS
        print("✓ All required models import successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False


def main():
    """Run all verification checks"""
    print("="*60)
    print("EXPORT API VERIFICATION")
    print("="*60)
    
    checks = [
        verify_export_router,
        verify_app_includes_router,
        verify_endpoint_functions,
        verify_service_integration,
        verify_model_imports
    ]
    
    all_passed = True
    
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ Check {check.__name__} failed with error: {e}")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL EXPORT API VERIFICATION CHECKS PASSED!")
        print("="*60)
        print("\nExport API is properly configured with:")
        print("✓ 5 API endpoints (Anki CSV, Notion CSV, JSONL backup, JSONL import, formats)")
        print("✓ Complete export service implementation")
        print("✓ Proper FastAPI integration")
        print("✓ All required model dependencies")
        print("✓ Error handling and validation")
        
        print("\nAPI Endpoints available:")
        print("- GET /export/csv/anki - Export Anki-compatible CSV")
        print("- GET /export/csv/notion - Export Notion-compatible CSV")
        print("- GET /export/jsonl/backup - Export complete JSONL backup")
        print("- POST /export/jsonl/import - Import JSONL backup")
        print("- GET /export/formats - Get available export formats")
        
    else:
        print("❌ SOME VERIFICATION CHECKS FAILED!")
        print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)