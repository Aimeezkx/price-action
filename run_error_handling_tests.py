#!/usr/bin/env python3
"""
Simple Error Handling Test Runner

This script provides a simple way to run the error handling and recovery tests.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_backend_error_tests():
    """Run backend error handling tests"""
    print("🔧 Running Backend Error Handling Tests...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    try:
        # Run pytest for error handling tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/error_handling/", 
            "-v", 
            "--tb=short",
            "--durations=10"
        ], cwd=backend_dir, capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run backend tests: {e}")
        return False


def run_frontend_error_tests():
    """Run frontend error handling tests"""
    print("🌐 Running Frontend Error Handling Tests...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    try:
        # Run vitest for frontend error handling tests
        result = subprocess.run([
            "npm", "run", "test", 
            "--", 
            "src/tests/error-handling/",
            "--run"
        ], cwd=frontend_dir, capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run frontend tests: {e}")
        return False


def run_comprehensive_error_tests():
    """Run comprehensive error handling test suite"""
    print("🚀 Running Comprehensive Error Handling Test Suite...")
    
    try:
        # Run the comprehensive test suite
        result = subprocess.run([
            sys.executable, 
            "backend/tests/error_handling/run_error_tests.py"
        ], capture_output=True, text=True)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run comprehensive tests: {e}")
        return False


def main():
    """Main function"""
    print("🧪 Error Handling and Recovery Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Run backend tests
    if not run_backend_error_tests():
        all_passed = False
        print("❌ Backend error handling tests failed")
    else:
        print("✅ Backend error handling tests passed")
    
    print()
    
    # Run frontend tests
    if not run_frontend_error_tests():
        all_passed = False
        print("❌ Frontend error handling tests failed")
    else:
        print("✅ Frontend error handling tests passed")
    
    print()
    
    # Run comprehensive tests
    if not run_comprehensive_error_tests():
        all_passed = False
        print("❌ Comprehensive error handling tests failed")
    else:
        print("✅ Comprehensive error handling tests passed")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All error handling tests passed!")
        sys.exit(0)
    else:
        print("💥 Some error handling tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()