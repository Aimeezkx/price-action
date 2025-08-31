#!/usr/bin/env python3
"""
系统功能综合测试
测试核心功能是否正常运行
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path
import json

def print_status(message, status="INFO"):
    """打印状态信息"""
    symbols = {
        "INFO": "🔍",
        "SUCCESS": "✅", 
        "WARNING": "⚠️",
        "ERROR": "❌",
        "PROGRESS": "🚀"
    }
    print(f"{symbols.get(status, '📋')} {message}")

def run_command(cmd, description, cwd=None, timeout=30):
    """运行命令并返回结果"""
    print_status(f"运行: {description}", "PROGRESS")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd, timeout=timeout
        )
        if result.returncode == 0:
            print_status(f"{description} - 成功", "SUCCESS")
            return True, result.stdout
        else:
            print_status(f"{description} - 失败: {result.stderr[:200]}", "WARNING")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print_status(f"{description} - 超时", "ERROR")
        return False, "命令执行超时"
    except Exception as e:
        print_status(f"{description} - 异常: {str(e)}", "ERROR")
        return False, str(e)

def test_backend_basic():
    """测试后端基础功能"""
    print_status("测试后端基础功能", "INFO")
    
    backend_dir = Path(__file__).parent / "backend"
    
    # 测试数据库连接
    success, output = run_command(
        "python test_database_connection.py",
        "数据库连接测试",
        cwd=backend_dir
    )
    
    if not success:
        return False
    
    # 测试API端点
    success, output = run_command(
        "python test_simple_endpoints.py", 
        "API端点测试",
        cwd=backend_dir
    )
    
    return success

def test_basic_imports():
    """测试基础模块导入"""
    print_status("测试基础模块导入", "INFO")
    
    backend_dir = Path(__file__).parent / "backend"
    
    test_code = """
import sys
sys.path.insert(0, '.')
try:
    from app.models.document import Document, ProcessingStatus
    from app.core.database import get_db
    from app.core.config import settings
    print("✅ 所有基础模块导入成功")
    exit(0)
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)
"""
    
    success, output = run_command(
        f'python -c "{test_code}"',
        "基础模块导入测试",
        cwd=backend_dir
    )
    
    return success

def test_api_functionality():
    """测试API功能"""
    print_status("测试API功能", "INFO")
    
    backend_dir = Path(__file__).parent / "backend"
    
    test_code = """
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

# 测试根端点
response = client.get('/')
assert response.status_code == 200
print("✅ 根端点正常")

# 测试健康检查
response = client.get('/api/health/simple')
assert response.status_code == 200
print("✅ 健康检查端点正常")

# 测试文档列表
response = client.get('/api/documents')
assert response.status_code == 200
print("✅ 文档列表端点正常")

# 测试队列信息
response = client.get('/api/queue/info')
assert response.status_code == 200
print("✅ 队列信息端点正常")

# 测试上传端点
test_file = io.BytesIO(b'test content')
files = {'file': ('test.txt', test_file, 'text/plain')}
response = client.post('/api/test-upload', files=files)
assert response.status_code == 200
print("✅ 上传端点正常")

print("🎉 所有API测试通过")
"""
    
    success, output = run_command(
        f'python -c "{test_code}"',
        "API功能测试",
        cwd=backend_dir
    )
    
    return success

def test_frontend_build():
    """测试前端构建"""
    print_status("测试前端构建", "INFO")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # 检查依赖
    success, output = run_command(
        "npm ls --depth=0",
        "检查前端依赖",
        cwd=frontend_dir,
        timeout=60
    )
    
    if not success:
        print_status("前端依赖可能有问题，但继续测试", "WARNING")
    
    # 测试构建
    success, output = run_command(
        "npm run build",
        "前端构建测试",
        cwd=frontend_dir,
        timeout=120
    )
    
    return success

def generate_summary_report(results):
    """生成测试总结报告"""
    print_status("生成测试报告", "INFO")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
        "test_results": results
    }
    
    # 保存报告
    with open("system_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印总结
    print("\n" + "="*60)
    print_status("系统功能测试总结", "INFO")
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {report['success_rate']:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "SUCCESS" if result['success'] else "ERROR"
        print_status(f"{test_name}: {'通过' if result['success'] else '失败'}", status)
        if not result['success'] and result.get('error'):
            print(f"   错误: {result['error'][:100]}...")
    
    if report['success_rate'] >= 80:
        print_status("系统功能整体运行良好! 🎉", "SUCCESS")
    elif report['success_rate'] >= 60:
        print_status("系统功能基本正常，有少量问题需要关注", "WARNING")
    else:
        print_status("系统存在较多问题，需要修复", "ERROR")
    
    return report

def main():
    """主测试函数"""
    print_status("开始系统功能综合测试", "PROGRESS")
    print("="*60)
    
    # 定义测试用例
    test_cases = [
        ("基础模块导入", test_basic_imports),
        ("后端基础功能", test_backend_basic),
        ("API功能", test_api_functionality),
        ("前端构建", test_frontend_build),
    ]
    
    results = {}
    
    # 执行测试
    for test_name, test_func in test_cases:
        print(f"\n{'-'*40}")
        try:
            success = test_func()
            results[test_name] = {
                "success": success,
                "error": None if success else "测试失败"
            }
        except Exception as e:
            print_status(f"{test_name} 执行异常: {str(e)}", "ERROR")
            results[test_name] = {
                "success": False,
                "error": str(e)
            }
    
    # 生成报告
    print(f"\n{'-'*40}")
    report = generate_summary_report(results)
    
    return report['success_rate'] >= 60

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)