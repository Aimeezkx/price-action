#!/usr/bin/env python3
"""
测试简单的API端点
"""

import asyncio
import httpx
import sys
from pathlib import Path

async def test_api_endpoints():
    """测试API端点"""
    print("Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    timeout = 5.0
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/docs", "API documentation")
    ]
    
    async with httpx.AsyncClient() as client:
        for endpoint, description in endpoints:
            try:
                response = await client.get(f"{base_url}{endpoint}", timeout=timeout)
                if response.status_code == 200:
                    print(f"✓ {description} ({endpoint}): OK")
                else:
                    print(f"✗ {description} ({endpoint}): Status {response.status_code}")
                    return False
            except httpx.TimeoutException:
                print(f"⚠ {description} ({endpoint}): Timeout (server may not be running)")
                return False
            except httpx.ConnectError:
                print(f"⚠ {description} ({endpoint}): Connection error (server may not be running)")
                return False
            except Exception as e:
                print(f"✗ {description} ({endpoint}): Error - {e}")
                return False
    
    print("✓ API endpoint tests completed successfully")
    return True

async def main():
    """主函数"""
    success = await test_api_endpoints()
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)