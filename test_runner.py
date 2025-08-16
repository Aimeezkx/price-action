#!/usr/bin/env python3
"""
Comprehensive test runner for the document learning application.
Executes all test suites and generates comprehensive reports.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click


class TestResult:
    """Represents the result of a test suite execution."""
    
    def __init__(self, name: str, passed: bool = False, duration: float = 0.0, 
                 details: Optional[Dict] = None):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.details = details or {}
        self.timestamp = datetime.now()


class TestRunner:
    """Comprehensive test runner for all test suites."""
    
    def __init__(self, output_dir: Path = Path("test_results")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[TestResult] = []
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> TestResult:
        """Run a command and capture the result."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            passed = result.returncode == 0
            
            details = {
                "command": " ".join(command),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            
            return TestResult(
                name=" ".join(command[:2]),
                passed=passed,
                duration=duration,
                details=details
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                name=" ".join(command[:2]),
                passed=False,
                duration=duration,
                details={"error": "Test timed out after 5 minutes"}
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=" ".join(command[:2]),
                passed=False,
                duration=duration,
                details={"error": str(e)}
            )
    
    def run_backend_unit_tests(self) -> TestResult:
        """Run backend unit tests with coverage."""
        click.echo("🧪 Running backend unit tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--cov=app",
            "--cov-report=html:test_results/backend_coverage",
            "--cov-report=json:test_results/backend_coverage.json",
            "--junit-xml=test_results/backend_junit.xml",
            "-m", "unit"
        ]
        
        return self.run_command(command, cwd=Path("backend"))
    
    def run_backend_integration_tests(self) -> TestResult:
        """Run backend integration tests."""
        click.echo("🔗 Running backend integration tests...")
        
        command = [
            "python", "-m", "pytest",
            "test_*_integration.py",
            "-v",
            "--junit-xml=test_results/backend_integration_junit.xml",
            "-m", "integration"
        ]
        
        return self.run_command(command, cwd=Path("backend"))
    
    def run_backend_performance_tests(self) -> TestResult:
        """Run backend performance tests."""
        click.echo("⚡ Running backend performance tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--benchmark-only",
            "--benchmark-json=test_results/backend_benchmark.json",
            "-m", "performance"
        ]
        
        return self.run_command(command, cwd=Path("backend"))
    
    def run_frontend_unit_tests(self) -> TestResult:
        """Run frontend unit tests."""
        click.echo("🎨 Running frontend unit tests...")
        
        command = ["npm", "run", "test:coverage"]
        
        return self.run_command(command, cwd=Path("frontend"))
    
    def run_frontend_e2e_tests(self) -> TestResult:
        """Run frontend end-to-end tests."""
        click.echo("🌐 Running frontend E2E tests...")
        
        # First, start the development server
        click.echo("Starting development servers...")
        
        # Start backend server
        backend_process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--port", "8000"],
            cwd=Path("backend")
        )
        
        # Start frontend server
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=Path("frontend")
        )
        
        # Wait for servers to start
        time.sleep(10)
        
        try:
            command = ["npx", "playwright", "test", "--reporter=json"]
            result = self.run_command(command, cwd=Path("frontend"))
        finally:
            # Clean up processes
            backend_process.terminate()
            frontend_process.terminate()
            backend_process.wait()
            frontend_process.wait()
        
        return result
    
    def run_security_tests(self) -> TestResult:
        """Run security tests."""
        click.echo("🔒 Running security tests...")
        
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--junit-xml=test_results/security_junit.xml",
            "-m", "security"
        ]
        
        return self.run_command(command, cwd=Path("backend"))
    
    def run_accessibility_tests(self) -> TestResult:
        """Run accessibility tests."""
        click.echo("♿ Running accessibility tests...")
        
        command = ["npm", "run", "test:accessibility"]
        
        return self.run_command(command, cwd=Path("frontend"))
    
    def run_load_tests(self) -> TestResult:
        """Run load tests using Locust."""
        click.echo("📈 Running load tests...")
        
        # Create a simple load test script
        load_test_script = Path("backend/load_test.py")
        if not load_test_script.exists():
            load_test_content = '''
from locust import HttpUser, task, between

class DocumentLearningUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_documents(self):
        self.client.get("/api/documents")
    
    @task
    def search(self):
        self.client.get("/api/search?q=test")
    
    @task
    def get_cards(self):
        self.client.get("/api/cards")
'''
            load_test_script.write_text(load_test_content)
        
        command = [
            "locust",
            "-f", "load_test.py",
            "--headless",
            "--users", "10",
            "--spawn-rate", "2",
            "--run-time", "30s",
            "--host", "http://localhost:8000",
            "--html", "test_results/load_test_report.html"
        ]
        
        return self.run_command(command, cwd=Path("backend"))
    
    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        click.echo("📊 Generating comprehensive test report...")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "timestamp": datetime.now().isoformat()
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "timestamp": r.timestamp.isoformat(),
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        # Save JSON report
        report_path = self.output_dir / "comprehensive_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_report = self.generate_html_report(report)
        html_path = self.output_dir / "comprehensive_test_report.html"
        with open(html_path, "w") as f:
            f.write(html_report)
        
        # Print summary
        click.echo(f"\n{'='*60}")
        click.echo("📋 TEST SUMMARY")
        click.echo(f"{'='*60}")
        click.echo(f"Total Tests: {total_tests}")
        click.echo(f"Passed: {passed_tests} ✅")
        click.echo(f"Failed: {failed_tests} ❌")
        click.echo(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        click.echo(f"Total Duration: {total_duration:.2f}s")
        click.echo(f"\nDetailed report saved to: {html_path}")
        
        # Print failed tests
        if failed_tests > 0:
            click.echo(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.passed:
                    click.echo(f"  - {result.name}")
                    if "error" in result.details:
                        click.echo(f"    Error: {result.details['error']}")
    
    def generate_html_report(self, report: Dict) -> str:
        """Generate HTML test report."""
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Document Learning App - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .test-result {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }}
        .test-result.passed {{ border-left: 5px solid green; }}
        .test-result.failed {{ border-left: 5px solid red; }}
        .details {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        pre {{ background: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Document Learning App - Comprehensive Test Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {report['summary']['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="passed">{report['summary']['passed_tests']}</span></p>
        <p><strong>Failed:</strong> <span class="failed">{report['summary']['failed_tests']}</span></p>
        <p><strong>Success Rate:</strong> {report['summary']['success_rate']:.1f}%</p>
        <p><strong>Total Duration:</strong> {report['summary']['total_duration']:.2f}s</p>
        <p><strong>Generated:</strong> {report['summary']['timestamp']}</p>
    </div>
    
    <h2>Test Results</h2>
'''
        
        for result in report['results']:
            status_class = 'passed' if result['passed'] else 'failed'
            status_text = '✅ PASSED' if result['passed'] else '❌ FAILED'
            
            html += f'''
    <div class="test-result {status_class}">
        <h3>{result['name']} - {status_text}</h3>
        <p><strong>Duration:</strong> {result['duration']:.2f}s</p>
        <p><strong>Timestamp:</strong> {result['timestamp']}</p>
'''
            
            if result['details'].get('error'):
                html += f'<div class="details"><strong>Error:</strong> {result["details"]["error"]}</div>'
            
            if result['details'].get('stdout'):
                html += f'<div class="details"><strong>Output:</strong><pre>{result["details"]["stdout"][:1000]}...</pre></div>'
            
            html += '</div>'
        
        html += '''
</body>
</html>
'''
        return html


@click.command()
@click.option('--suite', type=click.Choice([
    'unit', 'integration', 'performance', 'e2e', 'security', 'accessibility', 'load', 'all'
]), default='all', help='Test suite to run')
@click.option('--output-dir', type=click.Path(), default='test_results', help='Output directory for test results')
def main(suite: str, output_dir: str):
    """Run comprehensive tests for the document learning application."""
    
    runner = TestRunner(Path(output_dir))
    
    if suite in ['unit', 'all']:
        runner.results.append(runner.run_backend_unit_tests())
        runner.results.append(runner.run_frontend_unit_tests())
    
    if suite in ['integration', 'all']:
        runner.results.append(runner.run_backend_integration_tests())
    
    if suite in ['performance', 'all']:
        runner.results.append(runner.run_backend_performance_tests())
    
    if suite in ['e2e', 'all']:
        runner.results.append(runner.run_frontend_e2e_tests())
    
    if suite in ['security', 'all']:
        runner.results.append(runner.run_security_tests())
    
    if suite in ['accessibility', 'all']:
        runner.results.append(runner.run_accessibility_tests())
    
    if suite in ['load', 'all']:
        runner.results.append(runner.run_load_tests())
    
    runner.generate_report()
    
    # Exit with error code if any tests failed
    failed_tests = sum(1 for r in runner.results if not r.passed)
    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()