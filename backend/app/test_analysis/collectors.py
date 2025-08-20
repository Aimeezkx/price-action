"""
Test Result Collectors for Various Testing Frameworks
"""
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import re

from .models import TestCategory, TestStatus


class TestResultCollector:
    """Base class for test result collectors"""
    
    def __init__(self, test_category: TestCategory):
        self.test_category = test_category
    
    async def collect_results(self) -> Dict[str, Any]:
        """Collect test results - to be implemented by subclasses"""
        raise NotImplementedError


class PytestCollector(TestResultCollector):
    """Collect results from pytest"""
    
    def __init__(self, test_dir: str = "backend/tests"):
        super().__init__(TestCategory.UNIT)
        self.test_dir = Path(test_dir)
    
    async def collect_results(self) -> Dict[str, Any]:
        """Collect pytest results"""
        try:
            # Run pytest with JSON report
            cmd = [
                "python", "-m", "pytest",
                str(self.test_dir),
                "--json-report",
                "--json-report-file=test_results.json",
                "--cov=app",
                "--cov-report=json:coverage.json",
                "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="backend")
            
            # Parse JSON report
            json_report_path = Path("backend/test_results.json")
            coverage_report_path = Path("backend/coverage.json")
            
            test_data = {}
            
            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    pytest_data = json.load(f)
                
                test_data = self._parse_pytest_json(pytest_data)
            
            # Parse coverage data
            if coverage_report_path.exists():
                with open(coverage_report_path, 'r') as f:
                    coverage_data = json.load(f)
                
                test_data["coverage"] = self._parse_coverage_json(coverage_data)
            
            return test_data
            
        except Exception as e:
            return {
                "error": f"Failed to collect pytest results: {str(e)}",
                "test_suites": [],
                "coverage": None
            }
    
    def _parse_pytest_json(self, pytest_data: Dict) -> Dict[str, Any]:
        """Parse pytest JSON report"""
        summary = pytest_data.get("summary", {})
        tests = pytest_data.get("tests", [])
        
        # Calculate totals
        total_tests = summary.get("total", 0)
        passed_tests = summary.get("passed", 0)
        failed_tests = summary.get("failed", 0)
        skipped_tests = summary.get("skipped", 0)
        error_tests = summary.get("error", 0)
        
        # Determine overall status
        if failed_tests > 0 or error_tests > 0:
            status = TestStatus.FAILED
        elif total_tests == 0:
            status = TestStatus.PENDING
        else:
            status = TestStatus.PASSED
        
        # Parse individual test results
        test_results = []
        for test in tests:
            test_result = {
                "name": test.get("nodeid", "Unknown"),
                "status": self._map_pytest_outcome(test.get("outcome", "unknown")),
                "duration": test.get("duration", 0.0),
                "error_message": None,
                "stack_trace": None,
                "metadata": {
                    "file": test.get("file"),
                    "line": test.get("lineno")
                }
            }
            
            # Add error details if test failed
            if test.get("outcome") in ["failed", "error"]:
                call = test.get("call", {})
                test_result["error_message"] = call.get("longrepr", "")
                test_result["stack_trace"] = call.get("longrepr", "")
            
            test_results.append(test_result)
        
        return {
            "test_suites": [{
                "name": "Backend Unit Tests",
                "category": self.test_category.value,
                "status": status.value,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "error_tests": error_tests,
                "duration": pytest_data.get("duration", 0.0),
                "test_results": test_results
            }]
        }
    
    def _map_pytest_outcome(self, outcome: str) -> str:
        """Map pytest outcome to our test status"""
        mapping = {
            "passed": TestStatus.PASSED.value,
            "failed": TestStatus.FAILED.value,
            "skipped": TestStatus.SKIPPED.value,
            "error": TestStatus.ERROR.value
        }
        return mapping.get(outcome, TestStatus.ERROR.value)
    
    def _parse_coverage_json(self, coverage_data: Dict) -> Dict[str, Any]:
        """Parse coverage JSON report"""
        totals = coverage_data.get("totals", {})
        files = coverage_data.get("files", {})
        
        coverage_by_file = {}
        uncovered_files = []
        
        for file_path, file_data in files.items():
            summary = file_data.get("summary", {})
            covered_lines = summary.get("covered_lines", 0)
            num_statements = summary.get("num_statements", 1)
            
            file_coverage = (covered_lines / num_statements * 100) if num_statements > 0 else 0
            coverage_by_file[file_path] = file_coverage
            
            if file_coverage < 80:  # Consider files with <80% coverage as needing attention
                uncovered_files.append(file_path)
        
        return {
            "total_lines": totals.get("num_statements", 0),
            "covered_lines": totals.get("covered_lines", 0),
            "coverage_percentage": totals.get("percent_covered", 0.0),
            "uncovered_files": uncovered_files,
            "coverage_by_file": coverage_by_file
        }


class JestCollector(TestResultCollector):
    """Collect results from Jest (frontend tests)"""
    
    def __init__(self, test_dir: str = "frontend"):
        super().__init__(TestCategory.UNIT)
        self.test_dir = Path(test_dir)
    
    async def collect_results(self) -> Dict[str, Any]:
        """Collect Jest test results"""
        try:
            # Run Jest with JSON output
            cmd = [
                "npm", "test", "--",
                "--json",
                "--coverage",
                "--watchAll=false",
                "--passWithNoTests"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.test_dir))
            
            if result.stdout:
                jest_data = json.loads(result.stdout)
                return self._parse_jest_json(jest_data)
            else:
                return {
                    "error": "No Jest output received",
                    "test_suites": []
                }
                
        except Exception as e:
            return {
                "error": f"Failed to collect Jest results: {str(e)}",
                "test_suites": []
            }
    
    def _parse_jest_json(self, jest_data: Dict) -> Dict[str, Any]:
        """Parse Jest JSON output"""
        test_results = jest_data.get("testResults", [])
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        total_duration = 0.0
        
        parsed_test_results = []
        
        for test_file in test_results:
            file_tests = test_file.get("assertionResults", [])
            
            for test in file_tests:
                total_tests += 1
                duration = test.get("duration", 0) / 1000.0  # Convert ms to seconds
                total_duration += duration
                
                status = test.get("status", "unknown")
                if status == "passed":
                    passed_tests += 1
                elif status == "failed":
                    failed_tests += 1
                elif status == "pending" or status == "skipped":
                    skipped_tests += 1
                
                test_result = {
                    "name": test.get("fullName", "Unknown"),
                    "status": self._map_jest_status(status),
                    "duration": duration,
                    "error_message": None,
                    "stack_trace": None,
                    "metadata": {
                        "file": test_file.get("name"),
                        "title": test.get("title")
                    }
                }
                
                # Add failure details
                if status == "failed":
                    failure_messages = test.get("failureMessages", [])
                    if failure_messages:
                        test_result["error_message"] = failure_messages[0]
                        test_result["stack_trace"] = "\n".join(failure_messages)
                
                parsed_test_results.append(test_result)
        
        # Determine overall status
        if failed_tests > 0:
            status = TestStatus.FAILED
        elif total_tests == 0:
            status = TestStatus.PENDING
        else:
            status = TestStatus.PASSED
        
        # Parse coverage if available
        coverage_data = None
        if "coverageMap" in jest_data:
            coverage_data = self._parse_jest_coverage(jest_data["coverageMap"])
        
        result = {
            "test_suites": [{
                "name": "Frontend Unit Tests",
                "category": self.test_category.value,
                "status": status.value,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "error_tests": 0,
                "duration": total_duration,
                "test_results": parsed_test_results
            }]
        }
        
        if coverage_data:
            result["coverage"] = coverage_data
        
        return result
    
    def _map_jest_status(self, status: str) -> str:
        """Map Jest status to our test status"""
        mapping = {
            "passed": TestStatus.PASSED.value,
            "failed": TestStatus.FAILED.value,
            "pending": TestStatus.SKIPPED.value,
            "skipped": TestStatus.SKIPPED.value,
            "todo": TestStatus.SKIPPED.value
        }
        return mapping.get(status, TestStatus.ERROR.value)
    
    def _parse_jest_coverage(self, coverage_map: Dict) -> Dict[str, Any]:
        """Parse Jest coverage data"""
        total_lines = 0
        covered_lines = 0
        coverage_by_file = {}
        uncovered_files = []
        
        for file_path, file_coverage in coverage_map.items():
            statements = file_coverage.get("s", {})
            if statements:
                file_total = len(statements)
                file_covered = sum(1 for count in statements.values() if count > 0)
                
                total_lines += file_total
                covered_lines += file_covered
                
                file_percentage = (file_covered / file_total * 100) if file_total > 0 else 0
                coverage_by_file[file_path] = file_percentage
                
                if file_percentage < 80:
                    uncovered_files.append(file_path)
        
        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        return {
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "coverage_percentage": coverage_percentage,
            "uncovered_files": uncovered_files,
            "coverage_by_file": coverage_by_file
        }


class PlaywrightCollector(TestResultCollector):
    """Collect results from Playwright E2E tests"""
    
    def __init__(self, test_dir: str = "frontend/e2e"):
        super().__init__(TestCategory.E2E)
        self.test_dir = Path(test_dir)
    
    async def collect_results(self) -> Dict[str, Any]:
        """Collect Playwright test results"""
        try:
            # Run Playwright tests with JSON reporter
            cmd = [
                "npx", "playwright", "test",
                "--reporter=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="frontend")
            
            if result.stdout:
                playwright_data = json.loads(result.stdout)
                return self._parse_playwright_json(playwright_data)
            else:
                return {
                    "error": "No Playwright output received",
                    "test_suites": []
                }
                
        except Exception as e:
            return {
                "error": f"Failed to collect Playwright results: {str(e)}",
                "test_suites": []
            }
    
    def _parse_playwright_json(self, playwright_data: Dict) -> Dict[str, Any]:
        """Parse Playwright JSON output"""
        suites = playwright_data.get("suites", [])
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        total_duration = 0.0
        
        parsed_test_results = []
        
        def parse_suite(suite, suite_name=""):
            nonlocal total_tests, passed_tests, failed_tests, skipped_tests, total_duration
            
            current_suite_name = suite_name + suite.get("title", "")
            
            # Parse tests in this suite
            for spec in suite.get("specs", []):
                for test in spec.get("tests", []):
                    total_tests += 1
                    
                    results = test.get("results", [])
                    if results:
                        result = results[0]  # Take first result
                        status = result.get("status", "unknown")
                        duration = result.get("duration", 0) / 1000.0  # Convert ms to seconds
                        total_duration += duration
                        
                        if status == "passed":
                            passed_tests += 1
                        elif status == "failed":
                            failed_tests += 1
                        elif status == "skipped":
                            skipped_tests += 1
                        
                        test_result = {
                            "name": f"{current_suite_name} > {test.get('title', 'Unknown')}",
                            "status": self._map_playwright_status(status),
                            "duration": duration,
                            "error_message": result.get("error", {}).get("message"),
                            "stack_trace": result.get("error", {}).get("stack"),
                            "metadata": {
                                "suite": current_suite_name,
                                "file": spec.get("file"),
                                "line": spec.get("line")
                            }
                        }
                        
                        parsed_test_results.append(test_result)
            
            # Recursively parse nested suites
            for nested_suite in suite.get("suites", []):
                parse_suite(nested_suite, current_suite_name + " > ")
        
        # Parse all suites
        for suite in suites:
            parse_suite(suite)
        
        # Determine overall status
        if failed_tests > 0:
            status = TestStatus.FAILED
        elif total_tests == 0:
            status = TestStatus.PENDING
        else:
            status = TestStatus.PASSED
        
        return {
            "test_suites": [{
                "name": "End-to-End Tests",
                "category": self.test_category.value,
                "status": status.value,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "error_tests": 0,
                "duration": total_duration,
                "test_results": parsed_test_results
            }]
        }
    
    def _map_playwright_status(self, status: str) -> str:
        """Map Playwright status to our test status"""
        mapping = {
            "passed": TestStatus.PASSED.value,
            "failed": TestStatus.FAILED.value,
            "skipped": TestStatus.SKIPPED.value,
            "timedOut": TestStatus.ERROR.value,
            "interrupted": TestStatus.ERROR.value
        }
        return mapping.get(status, TestStatus.ERROR.value)


class PerformanceCollector:
    """Collect performance benchmark results"""
    
    def __init__(self, results_dir: str = "performance_results"):
        self.results_dir = Path(results_dir)
    
    async def collect_results(self) -> Dict[str, Any]:
        """Collect performance benchmark results"""
        try:
            performance_data = {}
            
            # Look for performance result files
            if self.results_dir.exists():
                for result_file in self.results_dir.glob("*.json"):
                    with open(result_file, 'r') as f:
                        data = json.load(f)
                        benchmark_name = result_file.stem
                        performance_data[benchmark_name] = self._parse_performance_data(data)
            
            return {"performance": performance_data}
            
        except Exception as e:
            return {
                "error": f"Failed to collect performance results: {str(e)}",
                "performance": {}
            }
    
    def _parse_performance_data(self, data: Dict) -> Dict[str, Any]:
        """Parse performance benchmark data"""
        return {
            "metric": data.get("metric", "response_time"),
            "value": data.get("value", 0.0),
            "unit": data.get("unit", "ms"),
            "threshold": data.get("threshold"),
            "passed": data.get("value", 0.0) <= data.get("threshold", float('inf')) if data.get("threshold") else True
        }


class TestResultAggregator:
    """Aggregate results from multiple test collectors"""
    
    def __init__(self):
        self.collectors = [
            PytestCollector(),
            JestCollector(),
            PlaywrightCollector(),
            PerformanceCollector()
        ]
    
    async def collect_all_results(self) -> Dict[str, Any]:
        """Collect results from all configured collectors"""
        aggregated_results = {
            "test_suites": [],
            "performance": {},
            "coverage": None,
            "collection_timestamp": datetime.now().isoformat(),
            "errors": []
        }
        
        for collector in self.collectors:
            try:
                results = await collector.collect_results()
                
                if "error" in results:
                    aggregated_results["errors"].append({
                        "collector": collector.__class__.__name__,
                        "error": results["error"]
                    })
                    continue
                
                # Merge test suites
                if "test_suites" in results:
                    aggregated_results["test_suites"].extend(results["test_suites"])
                
                # Merge performance data
                if "performance" in results:
                    aggregated_results["performance"].update(results["performance"])
                
                # Use coverage from the first collector that provides it
                if "coverage" in results and results["coverage"] and not aggregated_results["coverage"]:
                    aggregated_results["coverage"] = results["coverage"]
                
            except Exception as e:
                aggregated_results["errors"].append({
                    "collector": collector.__class__.__name__,
                    "error": str(e)
                })
        
        return aggregated_results