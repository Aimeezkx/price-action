#!/usr/bin/env python3
"""
Test Results Analyzer
Analyzes comprehensive test results and generates improvement recommendations.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueCategory(Enum):
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    COVERAGE = "coverage"
    INFRASTRUCTURE = "infrastructure"

@dataclass
class Issue:
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    test_suite: str
    reproduction_steps: List[str]
    suggested_fix: str
    priority_score: int

@dataclass
class Improvement:
    title: str
    description: str
    category: IssueCategory
    impact: str
    effort: str
    priority_score: int
    implementation_steps: List[str]

class TestResultsAnalyzer:
    """Analyze test results and generate improvement recommendations"""
    
    def __init__(self, results_file: str = 'comprehensive_test_results.json'):
        self.results_file = results_file
        self.results = self.load_results()
        self.issues = []
        self.improvements = []
        
    def load_results(self) -> Dict[str, Any]:
        """Load test results from file"""
        if not os.path.exists(self.results_file):
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
            
        with open(self.results_file, 'r') as f:
            return json.load(f)
            
    def analyze_all_results(self) -> Tuple[List[Issue], List[Improvement]]:
        """Analyze all test results and generate issues and improvements"""
        print("🔍 Analyzing test results...")
        
        # Analyze each test suite
        for suite_name, suite_result in self.results.get('test_suites', {}).items():
            self.analyze_test_suite(suite_name, suite_result)
            
        # Analyze overall patterns
        self.analyze_coverage_patterns()
        self.analyze_performance_patterns()
        self.analyze_failure_patterns()
        
        # Generate improvement recommendations
        self.generate_improvements()
        
        # Prioritize issues and improvements
        self.prioritize_issues()
        self.prioritize_improvements()
        
        return self.issues, self.improvements
        
    def analyze_test_suite(self, suite_name: str, suite_result: Dict[str, Any]):
        """Analyze individual test suite results"""
        if not suite_result.get('passed', False):
            # Create issue for failed test suite
            severity = IssueSeverity.CRITICAL if suite_result.get('critical', False) else IssueSeverity.HIGH
            
            issue = Issue(
                title=f"{suite_name.replace('_', ' ').title()} Test Failures",
                description=f"Test suite {suite_name} failed with {suite_result.get('failed_count', 'unknown')} failures",
                severity=severity,
                category=self.categorize_test_suite(suite_name),
                test_suite=suite_name,
                reproduction_steps=[
                    f"Run {suite_name} test suite",
                    "Check test output for specific failures",
                    "Review error logs and stack traces"
                ],
                suggested_fix=self.suggest_fix_for_suite(suite_name, suite_result),
                priority_score=self.calculate_priority_score(severity, suite_result.get('critical', False))
            )
            
            self.issues.append(issue)
            
        # Analyze specific metrics
        if suite_name == 'unit_tests':
            self.analyze_unit_test_coverage(suite_result)
        elif suite_name == 'performance_tests':
            self.analyze_performance_results(suite_result)
        elif suite_name == 'security_tests':
            self.analyze_security_results(suite_result)
            
    def analyze_unit_test_coverage(self, suite_result: Dict[str, Any]):
        """Analyze unit test coverage"""
        coverage_percent = suite_result.get('coverage_percent', 0)
        
        if coverage_percent < 80:
            severity = IssueSeverity.HIGH if coverage_percent < 60 else IssueSeverity.MEDIUM
            
            issue = Issue(
                title="Low Test Coverage",
                description=f"Unit test coverage is {coverage_percent}%, below the 90% target",
                severity=severity,
                category=IssueCategory.COVERAGE,
                test_suite='unit_tests',
                reproduction_steps=[
                    "Run unit tests with coverage report",
                    "Review coverage report for uncovered lines",
                    "Identify critical paths without tests"
                ],
                suggested_fix="Add unit tests for uncovered code paths, prioritizing critical business logic",
                priority_score=self.calculate_priority_score(severity, True)
            )
            
            self.issues.append(issue)
            
    def analyze_performance_results(self, suite_result: Dict[str, Any]):
        """Analyze performance test results"""
        benchmark_results = suite_result.get('benchmark_results', [])
        
        for benchmark in benchmark_results:
            if not benchmark.get('passed', True):
                issue = Issue(
                    title=f"Performance Issue in {benchmark.get('script', 'Unknown')}",
                    description="Performance benchmark failed to meet requirements",
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.PERFORMANCE,
                    test_suite='performance_tests',
                    reproduction_steps=[
                        f"Run {benchmark.get('script', 'performance test')}",
                        "Monitor response times and resource usage",
                        "Compare against performance baselines"
                    ],
                    suggested_fix="Profile code to identify bottlenecks and optimize critical paths",
                    priority_score=self.calculate_priority_score(IssueSeverity.MEDIUM, False)
                )
                
                self.issues.append(issue)
                
    def analyze_security_results(self, suite_result: Dict[str, Any]):
        """Analyze security test results"""
        if not suite_result.get('passed', False):
            issue = Issue(
                title="Security Vulnerabilities Detected",
                description=f"Security tests failed with {suite_result.get('failed_count', 'unknown')} issues",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                test_suite='security_tests',
                reproduction_steps=[
                    "Run security test suite",
                    "Review security scan results",
                    "Identify specific vulnerabilities"
                ],
                suggested_fix="Address security vulnerabilities immediately, implement security best practices",
                priority_score=self.calculate_priority_score(IssueSeverity.CRITICAL, True)
            )
            
            self.issues.append(issue)
            
    def analyze_coverage_patterns(self):
        """Analyze overall test coverage patterns"""
        # Check if multiple test suites are failing
        failed_suites = [
            name for name, result in self.results.get('test_suites', {}).items()
            if not result.get('passed', False)
        ]
        
        if len(failed_suites) >= 3:
            issue = Issue(
                title="Widespread Test Failures",
                description=f"Multiple test suites failing: {', '.join(failed_suites)}",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.INFRASTRUCTURE,
                test_suite='multiple',
                reproduction_steps=[
                    "Run comprehensive test suite",
                    "Check for common failure patterns",
                    "Review test environment setup"
                ],
                suggested_fix="Review test infrastructure, check dependencies and environment configuration",
                priority_score=100
            )
            
            self.issues.append(issue)
            
    def analyze_performance_patterns(self):
        """Analyze performance patterns across test suites"""
        total_time = self.results.get('total_execution_time', 0)
        
        if total_time > 1800:  # 30 minutes
            improvement = Improvement(
                title="Optimize Test Execution Time",
                description=f"Test suite takes {total_time/60:.1f} minutes to complete",
                category=IssueCategory.PERFORMANCE,
                impact="High - Faster feedback for developers",
                effort="Medium - Requires test optimization",
                priority_score=70,
                implementation_steps=[
                    "Parallelize test execution",
                    "Optimize slow test cases",
                    "Use test fixtures more efficiently",
                    "Consider test sharding"
                ]
            )
            
            self.improvements.append(improvement)
            
    def analyze_failure_patterns(self):
        """Analyze failure patterns to identify systemic issues"""
        critical_issues = self.results.get('critical_issues', [])
        
        if len(critical_issues) > 10:
            issue = Issue(
                title="High Number of Critical Issues",
                description=f"Found {len(critical_issues)} critical issues across test suites",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.BUG,
                test_suite='multiple',
                reproduction_steps=[
                    "Review critical issues list",
                    "Identify common root causes",
                    "Prioritize fixes by impact"
                ],
                suggested_fix="Implement systematic bug fixing process, focus on root causes",
                priority_score=95
            )
            
            self.issues.append(issue)
            
    def generate_improvements(self):
        """Generate improvement recommendations based on analysis"""
        
        # Test automation improvements
        if any(suite.get('skipped') for suite in self.results.get('test_suites', {}).values()):
            improvement = Improvement(
                title="Complete Test Automation Coverage",
                description="Some test suites are skipped or not implemented",
                category=IssueCategory.INFRASTRUCTURE,
                impact="High - Better quality assurance",
                effort="High - Requires implementation",
                priority_score=80,
                implementation_steps=[
                    "Implement missing test suites",
                    "Set up proper test environments",
                    "Add automated test execution",
                    "Create test data management"
                ]
            )
            
            self.improvements.append(improvement)
            
        # Performance monitoring
        performance_suite = self.results.get('test_suites', {}).get('performance_tests', {})
        if not performance_suite.get('passed', False) or performance_suite.get('skipped'):
            improvement = Improvement(
                title="Implement Comprehensive Performance Monitoring",
                description="Performance testing needs enhancement for production readiness",
                category=IssueCategory.PERFORMANCE,
                impact="High - Prevent performance regressions",
                effort="Medium - Extend existing framework",
                priority_score=75,
                implementation_steps=[
                    "Set up performance baselines",
                    "Implement automated performance regression detection",
                    "Add real-time performance monitoring",
                    "Create performance optimization guidelines"
                ]
            )
            
            self.improvements.append(improvement)
            
        # Security enhancements
        security_suite = self.results.get('test_suites', {}).get('security_tests', {})
        if not security_suite.get('passed', False):
            improvement = Improvement(
                title="Enhance Security Testing Framework",
                description="Security testing needs strengthening for production deployment",
                category=IssueCategory.SECURITY,
                impact="Critical - Prevent security vulnerabilities",
                effort="High - Requires security expertise",
                priority_score=90,
                implementation_steps=[
                    "Implement automated security scanning",
                    "Add penetration testing procedures",
                    "Create security code review process",
                    "Set up vulnerability monitoring"
                ]
            )
            
            self.improvements.append(improvement)
            
    def categorize_test_suite(self, suite_name: str) -> IssueCategory:
        """Categorize test suite by type"""
        category_map = {
            'unit_tests': IssueCategory.BUG,
            'integration_tests': IssueCategory.BUG,
            'api_tests': IssueCategory.BUG,
            'frontend_tests': IssueCategory.BUG,
            'e2e_tests': IssueCategory.USABILITY,
            'performance_tests': IssueCategory.PERFORMANCE,
            'security_tests': IssueCategory.SECURITY,
            'accessibility_tests': IssueCategory.ACCESSIBILITY,
            'cross_platform_tests': IssueCategory.USABILITY,
            'load_tests': IssueCategory.PERFORMANCE
        }
        
        return category_map.get(suite_name, IssueCategory.BUG)
        
    def suggest_fix_for_suite(self, suite_name: str, suite_result: Dict[str, Any]) -> str:
        """Suggest fix based on test suite type and failure"""
        error = suite_result.get('error', '')
        
        if 'timeout' in error.lower():
            return "Increase test timeout or optimize test performance"
        elif 'connection' in error.lower():
            return "Check database/service connections and test environment setup"
        elif 'import' in error.lower() or 'module' in error.lower():
            return "Install missing dependencies or fix import paths"
        elif suite_name == 'frontend_tests':
            return "Check frontend build process and test configuration"
        elif suite_name == 'e2e_tests':
            return "Verify application is running and accessible for E2E tests"
        else:
            return "Review test logs and fix failing test cases"
            
    def calculate_priority_score(self, severity: IssueSeverity, is_critical: bool) -> int:
        """Calculate priority score for issues"""
        base_scores = {
            IssueSeverity.CRITICAL: 90,
            IssueSeverity.HIGH: 70,
            IssueSeverity.MEDIUM: 50,
            IssueSeverity.LOW: 30
        }
        
        score = base_scores[severity]
        if is_critical:
            score += 10
            
        return min(score, 100)
        
    def prioritize_issues(self):
        """Sort issues by priority score"""
        self.issues.sort(key=lambda x: x.priority_score, reverse=True)
        
    def prioritize_improvements(self):
        """Sort improvements by priority score"""
        self.improvements.sort(key=lambda x: x.priority_score, reverse=True)
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_status': self.results.get('overall_status', 'unknown'),
            'total_execution_time': self.results.get('total_execution_time', 0),
            'summary': {
                'total_issues': len(self.issues),
                'critical_issues': len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL]),
                'high_priority_issues': len([i for i in self.issues if i.severity == IssueSeverity.HIGH]),
                'total_improvements': len(self.improvements),
                'high_impact_improvements': len([i for i in self.improvements if i.priority_score >= 80])
            },
            'issues': [
                {
                    'title': issue.title,
                    'description': issue.description,
                    'severity': issue.severity.value,
                    'category': issue.category.value,
                    'test_suite': issue.test_suite,
                    'priority_score': issue.priority_score,
                    'reproduction_steps': issue.reproduction_steps,
                    'suggested_fix': issue.suggested_fix
                }
                for issue in self.issues
            ],
            'improvements': [
                {
                    'title': improvement.title,
                    'description': improvement.description,
                    'category': improvement.category.value,
                    'impact': improvement.impact,
                    'effort': improvement.effort,
                    'priority_score': improvement.priority_score,
                    'implementation_steps': improvement.implementation_steps
                }
                for improvement in self.improvements
            ]
        }
        
    def save_report(self, filepath: str = 'test_analysis_report.json'):
        """Save analysis report to file"""
        report = self.generate_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📋 Analysis report saved to {filepath}")
        return report

def main():
    """Main execution function"""
    try:
        analyzer = TestResultsAnalyzer()
        issues, improvements = analyzer.analyze_all_results()
        report = analyzer.save_report()
        
        # Print summary
        print("\n" + "="*60)
        print("🔍 TEST RESULTS ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Issues Found: {report['summary']['total_issues']}")
        print(f"Critical Issues: {report['summary']['critical_issues']}")
        print(f"High Priority Issues: {report['summary']['high_priority_issues']}")
        print(f"Improvement Opportunities: {report['summary']['total_improvements']}")
        
        if issues:
            print("\n🚨 Top 5 Critical Issues:")
            for issue in issues[:5]:
                print(f"  {issue.severity.value.upper()}: {issue.title}")
                
        if improvements:
            print("\n💡 Top 3 Improvement Opportunities:")
            for improvement in improvements[:3]:
                print(f"  {improvement.title} (Priority: {improvement.priority_score})")
                
        return True
        
    except Exception as e:
        print(f"💥 Analysis failed: {str(e)}")
        return False

if __name__ == "__main__":
    main()