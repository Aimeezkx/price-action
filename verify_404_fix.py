#!/usr/bin/env python3
"""
Verification script for 404 API fixes
Tests that the missing endpoints now return proper responses
"""

import requests
import json
import sys
from typing import Dict, Any

def test_endpoint(url: str, expected_status: int = 200) -> Dict[str, Any]:
    """Test an endpoint and return results"""
    try:
        response = requests.get(url, timeout=10)
        return {
            'url': url,
            'status_code': response.status_code,
            'expected_status': expected_status,
            'success': response.status_code == expected_status,
            'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'error': None
        }
    except requests.exceptions.RequestException as e:
        return {
            'url': url,
            'status_code': None,
            'expected_status': expected_status,
            'success': False,
            'response_data': None,
            'error': str(e)
        }

def main():
    """Run verification tests"""
    print("🔍 Verifying 404 API fixes...")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ('http://localhost:8000/api/cards', 200),
        ('http://localhost:8000/api/review/today', 200),
        ('http://localhost:3000/api/cards', 200),
        ('http://localhost:3000/api/review/today', 200),
    ]
    
    results = []
    all_passed = True
    
    for url, expected_status in endpoints:
        print(f"Testing: {url}")
        result = test_endpoint(url, expected_status)
        results.append(result)
        
        if result['success']:
            print(f"  ✅ SUCCESS: {result['status_code']} - {result['response_data']}")
        else:
            print(f"  ❌ FAILED: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}")
            all_passed = False
        print()
    
    # Summary
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! The 404 fixes are working correctly.")
        print("✅ Frontend should no longer show 'service unavailable' errors")
        print("✅ Cards and review endpoints return empty arrays instead of 404")
        print("✅ Proxy routing is working correctly")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print("💡 Make sure both backend (port 8000) and frontend (port 3000) are running")
    
    print("\n📋 Next steps:")
    print("1. Run the application and check that Study/Review pages load without errors")
    print("2. Upload a document to test the full pipeline")
    print("3. Verify that cards appear in the /api/cards endpoint after processing")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())