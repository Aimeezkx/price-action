#!/usr/bin/env python3
"""
验收标准验证脚本
系统性验证所有REQUIREMENTS_AND_TASKS.md中的验收标准
"""

import os
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any

class AcceptanceCriteriaValidator:
    """验收标准验证器"""
    
    def __init__(self):
        self.workspace = Path("/Users/kaixinzheng/quant trading/priceaction/price-action")
        self.results = {}
        
    def print_status(self, message: str, status: str = "INFO"):
        """打印状态信息"""
        symbols = {"INFO": "🔍", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"{symbols.get(status, '📋')} {message}")
        
    def run_command(self, cmd: str, cwd: str = None, timeout: int = 30) -> tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                cwd=cwd or self.workspace, timeout=timeout
            )
            return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)
    
    def validate_typescript_config(self) -> Dict[str, Any]:
        """验证TypeScript配置标准"""
        self.print_status("验证TypeScript配置标准", "INFO")
        
        # 检查tsconfig.json内容
        tsconfig_path = self.workspace / "frontend" / "tsconfig.json"
        
        try:
            with open(tsconfig_path) as f:
                import json
                config = json.load(f)
            
            checks = {
                "moduleResolution_valid": config.get("compilerOptions", {}).get("moduleResolution") == "node",
                "no_invalid_options": "allowImportingTsExtensions" not in config.get("compilerOptions", {}),
                "config_syntax_valid": True  # 如果能解析JSON就是有效的
            }
            
            # 测试TypeScript编译器
            success, output = self.run_command(
                "npx tsc --noEmit --skipLibCheck",
                cwd=self.workspace / "frontend"
            )
            
            checks["compiler_no_config_errors"] = success
            
            return {
                "passed": all(checks.values()),
                "details": checks,
                "error": None if success else output
            }
            
        except Exception as e:
            return {"passed": False, "details": {}, "error": str(e)}
    
    def validate_frontend_build(self) -> Dict[str, Any]:
        """验证前端构建标准"""
        self.print_status("验证前端构建标准", "INFO")
        
        frontend_path = self.workspace / "frontend"
        
        # 清理之前的构建
        self.run_command("rm -rf dist", cwd=frontend_path)
        
        # 尝试构建
        success, output = self.run_command("npm run build", cwd=frontend_path, timeout=120)
        
        # 检查构建输出
        dist_exists = (frontend_path / "dist").exists()
        has_index = (frontend_path / "dist" / "index.html").exists()
        
        return {
            "passed": success and dist_exists and has_index,
            "details": {
                "build_success": success,
                "dist_directory_exists": dist_exists,
                "index_html_exists": has_index
            },
            "error": None if success else output
        }
    
    def validate_component_syntax(self) -> Dict[str, Any]:
        """验证组件语法标准"""
        self.print_status("验证组件语法标准", "INFO")
        
        # 检查UserAcceptanceDashboard组件
        dashboard_path = self.workspace / "frontend" / "src" / "components" / "UserAcceptance" / "UserAcceptanceDashboard.tsx"
        
        try:
            with open(dashboard_path) as f:
                content = f.read()
                
            # 检查是否还有语法错误的模式
            syntax_issues = [
                "'error' not in" in content,  # 应该已修复为 !('error' in)
                "} not in {" in content,      # 类似的语法错误
            ]
            
            # 使用TypeScript编译器验证特定文件
            success, output = self.run_command(
                f"npx tsc --noEmit --skipLibCheck {dashboard_path}",
                cwd=self.workspace / "frontend"
            )
            
            return {
                "passed": success and not any(syntax_issues),
                "details": {
                    "no_syntax_patterns": not any(syntax_issues),
                    "typescript_validates": success
                },
                "error": None if success else output
            }
            
        except Exception as e:
            return {"passed": False, "details": {}, "error": str(e)}
    
    def validate_accessibility_tests(self) -> Dict[str, Any]:
        """验证可访问性测试标准"""
        self.print_status("验证可访问性测试标准", "INFO")
        
        # 检查axe-core依赖
        package_json_path = self.workspace / "frontend" / "package.json"
        
        try:
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            dev_deps = package_data.get("devDependencies", {})
            axe_core_installed = "axe-core" in dev_deps
            
            # 尝试运行可访问性相关测试
            success, output = self.run_command(
                "npm list axe-core",
                cwd=self.workspace / "frontend"
            )
            
            return {
                "passed": axe_core_installed and success,
                "details": {
                    "axe_core_in_package_json": axe_core_installed,
                    "axe_core_installed": success
                },
                "error": None if success else output
            }
            
        except Exception as e:
            return {"passed": False, "details": {}, "error": str(e)}
    
    def validate_test_syntax(self) -> Dict[str, Any]:
        """验证测试文件语法标准"""
        self.print_status("验证测试文件语法标准", "INFO")
        
        # 检查关键测试文件是否存在语法错误
        test_files = [
            "src/test/integration/api-integration.test.ts",
            "src/test/upload-integration.test.ts",
            "src/test/performance/frontend-performance.test.ts"
        ]
        
        results = {}
        all_passed = True
        
        for test_file in test_files:
            file_path = self.workspace / "frontend" / test_file
            if file_path.exists():
                success, output = self.run_command(
                    f"npx tsc --noEmit --skipLibCheck {file_path}",
                    cwd=self.workspace / "frontend"
                )
                results[test_file] = success
                if not success:
                    all_passed = False
            else:
                results[test_file] = False
                all_passed = False
        
        return {
            "passed": all_passed,
            "details": results,
            "error": "Some test files have syntax errors" if not all_passed else None
        }
    
    def validate_spacy_installation(self) -> Dict[str, Any]:
        """验证spaCy安装标准"""
        self.print_status("验证spaCy安装标准", "INFO")
        
        # 测试spaCy模型加载
        success, output = self.run_command(
            'python -c "import spacy; nlp = spacy.load(\'en_core_web_sm\'); print(\'SUCCESS: spaCy model loaded\')"',
            cwd=self.workspace / "backend"
        )
        
        return {
            "passed": success and "SUCCESS" in output,
            "details": {
                "spacy_loads": success,
                "model_available": "SUCCESS" in output
            },
            "error": None if success else output
        }
    
    def validate_system_functionality(self) -> Dict[str, Any]:
        """验证系统功能标准"""
        self.print_status("验证系统功能标准", "INFO")
        
        # 测试后端基础功能
        backend_success, backend_output = self.run_command(
            "python test_database_connection.py",
            cwd=self.workspace / "backend"
        )
        
        # 测试API端点
        api_success, api_output = self.run_command(
            "python test_simple_endpoints.py",
            cwd=self.workspace / "backend"
        )
        
        return {
            "passed": backend_success and api_success,
            "details": {
                "database_connection": backend_success,
                "api_endpoints": api_success
            },
            "error": None if (backend_success and api_success) else f"Backend: {backend_output}, API: {api_output}"
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行全面验证"""
        self.print_status("开始全面验收标准验证", "INFO")
        
        validations = [
            ("TypeScript配置", self.validate_typescript_config),
            ("前端构建", self.validate_frontend_build), 
            ("组件语法", self.validate_component_syntax),
            ("可访问性测试", self.validate_accessibility_tests),
            ("测试文件语法", self.validate_test_syntax),
            ("spaCy安装", self.validate_spacy_installation),
            ("系统功能", self.validate_system_functionality),
        ]
        
        results = {}
        overall_success = True
        
        for name, validator in validations:
            self.print_status(f"验证: {name}", "INFO")
            result = validator()
            results[name] = result
            
            if result["passed"]:
                self.print_status(f"{name} - 通过", "SUCCESS")
            else:
                self.print_status(f"{name} - 失败: {result.get('error', '未知错误')}", "ERROR")
                overall_success = False
        
        # 生成总结报告
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_success": overall_success,
            "total_validations": len(validations),
            "passed_validations": sum(1 for r in results.values() if r["passed"]),
            "failed_validations": sum(1 for r in results.values() if not r["passed"]),
            "results": results
        }
        
        # 保存结果
        with open(self.workspace / "validation_results.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary

def main():
    """主函数"""
    validator = AcceptanceCriteriaValidator()
    results = validator.run_comprehensive_validation()
    
    print("\n" + "="*60)
    print("📊 验收标准验证总结")
    print("="*60)
    print(f"总验证项: {results['total_validations']}")
    print(f"通过验证: {results['passed_validations']}")
    print(f"失败验证: {results['failed_validations']}")
    print(f"总体状态: {'✅ 通过' if results['overall_success'] else '❌ 失败'}")
    
    if not results['overall_success']:
        print("\n失败的验证项:")
        for name, result in results['results'].items():
            if not result['passed']:
                print(f"  ❌ {name}: {result.get('error', '未知错误')}")
    
    print(f"\n详细结果已保存到: validation_results.json")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    sys.exit(main())