#!/usr/bin/env python3
"""Run comprehensive security tests."""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from tests.security.test_security_runner import run_security_tests


async def main():
    """Run security tests and display results."""
    print("🔒 Running Comprehensive Security Tests...")
    print("=" * 60)
    
    try:
        # Run all security tests
        report = await run_security_tests()
        
        # Display summary
        summary = report["summary"]
        print(f"\n📊 Security Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Warnings: {summary['warnings']} ⚠️")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   High Severity Failures: {summary['high_severity_failures']} 🚨")
        
        # Display detailed results
        print(f"\n📋 Detailed Results:")
        print("-" * 60)
        
        for result in report["results"]:
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "warning": "⚠️",
                "skipped": "⏭️"
            }.get(result["result"], "❓")
            
            severity_icon = {
                "HIGH": "🚨",
                "MEDIUM": "⚠️",
                "LOW": "ℹ️"
            }.get(result["severity"], "")
            
            print(f"{status_icon} {result['test_name']} {severity_icon}")
            print(f"   {result['message']}")
            
            if result.get("details"):
                print(f"   Details: {json.dumps(result['details'], indent=2)}")
            print()
        
        # Display recommendations
        if report["recommendations"]:
            print(f"💡 Security Recommendations:")
            print("-" * 60)
            for i, recommendation in enumerate(report["recommendations"], 1):
                print(f"{i}. {recommendation}")
            print()
        
        # Overall security status
        if summary["high_severity_failures"] > 0:
            print("🚨 CRITICAL: High severity security issues detected!")
            print("   Immediate action required before production deployment.")
            return 1
        elif summary["failed"] > 0:
            print("⚠️  WARNING: Some security tests failed.")
            print("   Review and address issues before production deployment.")
            return 1
        elif summary["success_rate"] < 90:
            print("⚠️  WARNING: Security test success rate below 90%.")
            print("   Consider additional security measures.")
            return 1
        else:
            print("✅ PASSED: All security tests completed successfully!")
            print("   System appears to have adequate security measures.")
            return 0
    
    except Exception as e:
        print(f"❌ Error running security tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)