"""
Bug Fix Verification Service

This service provides comprehensive bug fix verification workflows,
automated testing of fixes, and quality assurance processes.
"""

import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
try:
    import git
except ImportError:
    git = None

from .bug_tracking_service import TestIssue, IssueStatus, IssueSeverity
from .bug_reproduction_service import BugReproductionService

@dataclass
class FixVerificationResult:
    """Result of fix verification process"""
    issue_id: str
    fix_commit: str
    verification_time: datetime
    tests_passed: bool
    reproduction_scripts_passed: bool
    regression_tests_passed: bool
    performance_impact: Optional[Dict[str, float]]
    code_quality_score: Optional[float]
    verification_status: str  # 'passed', 'failed', 'partial'
    detailed_results: Dict[str, Any]
    recommendations: List[str]

@dataclass
class FixValidationRule:
    """Rule for validating bug fixes"""
    rule_id: str
    name: str
    description: str
    severity_applicable: List[IssueSeverity]
    validation_function: str
    required_for_approval: bool

class BugFixVerificationService:
    """Service for verifying bug fixes"""
    
    def __init__(self, storage_path: str = "fix_verification"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "results").mkdir(exist_ok=True)
        (self.storage_path / "reports").mkdir(exist_ok=True)
        (self.storage_path / "temp").mkdir(exist_ok=True)
        
        self.reproduction_service = BugReproductionService()
        self.validation_rules = self._load_validation_rules()
        
        # Initialize git repo reference
        self.repo = None
        if git:
            try:
                self.repo = git.Repo(".")
            except:
                self.repo = None
    
    def _load_validation_rules(self) -> List[FixValidationRule]:
        """Load fix validation rules"""
        return [
            FixValidationRule(
                rule_id="reproduction_test",
                name="Reproduction Test Verification",
                description="Verify that reproduction scripts no longer reproduce the bug",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM],
                validation_function="verify_reproduction_scripts",
                required_for_approval=True
            ),
            FixValidationRule(
                rule_id="regression_test",
                name="Regression Test Coverage",
                description="Ensure regression tests are created and passing",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH],
                validation_function="verify_regression_tests",
                required_for_approval=True
            ),
            FixValidationRule(
                rule_id="unit_tests",
                name="Unit Test Coverage",
                description="Verify that unit tests cover the fixed code",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM],
                validation_function="verify_unit_test_coverage",
                required_for_approval=True
            ),
            FixValidationRule(
                rule_id="integration_tests",
                name="Integration Test Verification",
                description="Run integration tests to ensure fix doesn't break other functionality",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH],
                validation_function="verify_integration_tests",
                required_for_approval=True
            ),
            FixValidationRule(
                rule_id="performance_impact",
                name="Performance Impact Assessment",
                description="Measure performance impact of the fix",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH],
                validation_function="assess_performance_impact",
                required_for_approval=False
            ),
            FixValidationRule(
                rule_id="code_quality",
                name="Code Quality Check",
                description="Verify code quality metrics are maintained",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM],
                validation_function="check_code_quality",
                required_for_approval=False
            ),
            FixValidationRule(
                rule_id="security_scan",
                name="Security Vulnerability Scan",
                description="Scan for new security vulnerabilities introduced by the fix",
                severity_applicable=[IssueSeverity.CRITICAL, IssueSeverity.HIGH],
                validation_function="scan_security_vulnerabilities",
                required_for_approval=True
            )
        ]
    
    def verify_fix(self, issue: TestIssue, fix_commit: str) -> FixVerificationResult:
        """Comprehensive fix verification"""
        verification_start = datetime.now()
        
        # Initialize result
        result = FixVerificationResult(
            issue_id=issue.id,
            fix_commit=fix_commit,
            verification_time=verification_start,
            tests_passed=False,
            reproduction_scripts_passed=False,
            regression_tests_passed=False,
            performance_impact=None,
            code_quality_score=None,
            verification_status='failed',
            detailed_results={},
            recommendations=[]
        )
        
        # Get applicable validation rules
        applicable_rules = [
            rule for rule in self.validation_rules 
            if issue.severity in rule.severity_applicable
        ]
        
        # Run each validation rule
        validation_results = {}
        required_passed = 0
        required_total = 0
        
        for rule in applicable_rules:
            try:
                rule_result = self._run_validation_rule(rule, issue, fix_commit)
                validation_results[rule.rule_id] = rule_result
                
                if rule.required_for_approval:
                    required_total += 1
                    if rule_result.get('passed', False):
                        required_passed += 1
                        
            except Exception as e:
                validation_results[rule.rule_id] = {
                    'passed': False,
                    'error': str(e),
                    'details': f"Validation rule {rule.rule_id} failed with error: {e}"
                }
                if rule.required_for_approval:
                    required_total += 1
        
        # Update result with validation outcomes
        result.detailed_results = validation_results
        
        # Set specific result flags
        result.reproduction_scripts_passed = validation_results.get('reproduction_test', {}).get('passed', False)
        result.regression_tests_passed = validation_results.get('regression_test', {}).get('passed', False)
        result.tests_passed = validation_results.get('unit_tests', {}).get('passed', False)
        
        # Set performance impact if available
        perf_result = validation_results.get('performance_impact', {})
        if 'metrics' in perf_result:
            result.performance_impact = perf_result['metrics']
        
        # Set code quality score if available
        quality_result = validation_results.get('code_quality', {})
        if 'score' in quality_result:
            result.code_quality_score = quality_result['score']
        
        # Determine overall verification status
        if required_passed == required_total and required_total > 0:
            result.verification_status = 'passed'
        elif required_passed > 0:
            result.verification_status = 'partial'
        else:
            result.verification_status = 'failed'
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, validation_results)
        
        # Save verification result
        self._save_verification_result(result)
        
        # Generate verification report
        self._generate_verification_report(result, issue)
        
        return result
    
    def _run_validation_rule(self, rule: FixValidationRule, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Run a specific validation rule"""
        if rule.validation_function == "verify_reproduction_scripts":
            return self._verify_reproduction_scripts(issue, fix_commit)
        elif rule.validation_function == "verify_regression_tests":
            return self._verify_regression_tests(issue, fix_commit)
        elif rule.validation_function == "verify_unit_test_coverage":
            return self._verify_unit_test_coverage(issue, fix_commit)
        elif rule.validation_function == "verify_integration_tests":
            return self._verify_integration_tests(issue, fix_commit)
        elif rule.validation_function == "assess_performance_impact":
            return self._assess_performance_impact(issue, fix_commit)
        elif rule.validation_function == "check_code_quality":
            return self._check_code_quality(issue, fix_commit)
        elif rule.validation_function == "scan_security_vulnerabilities":
            return self._scan_security_vulnerabilities(issue, fix_commit)
        else:
            return {'passed': False, 'error': f'Unknown validation function: {rule.validation_function}'}
    
    def _verify_reproduction_scripts(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Verify that reproduction scripts no longer reproduce the bug"""
        try:
            # Run reproduction verification
            verification_result = self.reproduction_service.verify_fix(issue.id)
            
            if 'error' in verification_result:
                return {
                    'passed': False,
                    'error': verification_result['error'],
                    'details': 'No reproduction scripts found or error running them'
                }
            
            # Check if bug is fixed based on reproduction scripts
            bug_fixed = verification_result.get('bug_fixed', False)
            scripts_run = verification_result.get('scripts_run', 0)
            
            return {
                'passed': bug_fixed,
                'scripts_run': scripts_run,
                'details': verification_result.get('detailed_results', []),
                'summary': f"Bug fixed: {bug_fixed}, Scripts run: {scripts_run}"
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error verifying reproduction scripts: {e}'
            }
    
    def _verify_regression_tests(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Verify regression tests exist and pass"""
        try:
            # Check if regression test exists
            regression_test_path = Path(f"bug_tracking/regression_test_{issue.id}.py")
            
            if not regression_test_path.exists():
                return {
                    'passed': False,
                    'error': 'No regression test found',
                    'details': f'Expected regression test at {regression_test_path}'
                }
            
            # Run the regression test
            result = subprocess.run(
                ["python", "-m", "pytest", str(regression_test_path), "-v"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'test_output': result.stdout,
                'test_errors': result.stderr,
                'return_code': result.returncode,
                'details': f'Regression test {"passed" if passed else "failed"}'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'error': 'Regression test timed out',
                'details': 'Test execution exceeded 5 minute timeout'
            }
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error running regression test: {e}'
            }
    
    def _verify_unit_test_coverage(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Verify unit test coverage for the fix"""
        try:
            # Get changed files from the fix commit
            changed_files = self._get_changed_files(fix_commit)
            
            if not changed_files:
                return {
                    'passed': False,
                    'error': 'No changed files found in commit',
                    'details': f'Could not determine changed files for commit {fix_commit}'
                }
            
            # Run unit tests with coverage
            result = subprocess.run([
                "python", "-m", "pytest", 
                "--cov=backend/app",
                "--cov-report=json",
                "backend/tests/",
                "-v"
            ], capture_output=True, text=True, timeout=600)
            
            # Parse coverage report
            coverage_file = Path("coverage.json")
            coverage_data = {}
            
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
            
            # Calculate coverage for changed files
            changed_file_coverage = {}
            for file_path in changed_files:
                if file_path in coverage_data.get('files', {}):
                    file_coverage = coverage_data['files'][file_path]
                    changed_file_coverage[file_path] = file_coverage.get('summary', {}).get('percent_covered', 0)
            
            # Determine if coverage is acceptable (>80% for critical/high severity)
            min_coverage = 80 if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH] else 70
            avg_coverage = sum(changed_file_coverage.values()) / len(changed_file_coverage) if changed_file_coverage else 0
            
            passed = result.returncode == 0 and avg_coverage >= min_coverage
            
            return {
                'passed': passed,
                'test_output': result.stdout,
                'test_errors': result.stderr,
                'coverage_data': changed_file_coverage,
                'average_coverage': avg_coverage,
                'minimum_required': min_coverage,
                'details': f'Unit tests {"passed" if result.returncode == 0 else "failed"}, Coverage: {avg_coverage:.1f}%'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error verifying unit test coverage: {e}'
            }
    
    def _verify_integration_tests(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Verify integration tests pass"""
        try:
            # Run integration tests
            result = subprocess.run([
                "python", "-m", "pytest", 
                "backend/tests/integration/",
                "-v"
            ], capture_output=True, text=True, timeout=900)
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'test_output': result.stdout,
                'test_errors': result.stderr,
                'return_code': result.returncode,
                'details': f'Integration tests {"passed" if passed else "failed"}'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'error': 'Integration tests timed out',
                'details': 'Test execution exceeded 15 minute timeout'
            }
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error running integration tests: {e}'
            }
    
    def _assess_performance_impact(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Assess performance impact of the fix"""
        try:
            # Run performance tests before and after fix
            # This is a simplified version - in practice you'd want to run on a clean environment
            
            # Run performance benchmark
            result = subprocess.run([
                "python", "run_performance_tests.py",
                "--format", "json"
            ], capture_output=True, text=True, timeout=1800)
            
            if result.returncode != 0:
                return {
                    'passed': False,
                    'error': 'Performance tests failed to run',
                    'details': result.stderr
                }
            
            # Parse performance results
            try:
                perf_data = json.loads(result.stdout)
                
                # Extract key metrics
                metrics = {
                    'document_processing_time': perf_data.get('document_processing', {}).get('avg_time', 0),
                    'search_response_time': perf_data.get('search', {}).get('avg_time', 0),
                    'memory_usage': perf_data.get('memory', {}).get('peak_mb', 0),
                    'cpu_usage': perf_data.get('cpu', {}).get('avg_percent', 0)
                }
                
                # Simple performance regression check
                # In practice, you'd compare against baseline metrics
                performance_acceptable = (
                    metrics['document_processing_time'] < 60 and  # Less than 60 seconds
                    metrics['search_response_time'] < 1.0 and     # Less than 1 second
                    metrics['memory_usage'] < 2048                # Less than 2GB
                )
                
                return {
                    'passed': performance_acceptable,
                    'metrics': metrics,
                    'details': f'Performance impact assessed: {"acceptable" if performance_acceptable else "concerning"}'
                }
                
            except json.JSONDecodeError:
                return {
                    'passed': False,
                    'error': 'Could not parse performance test results',
                    'details': 'Performance test output was not valid JSON'
                }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'error': 'Performance tests timed out',
                'details': 'Performance test execution exceeded 30 minute timeout'
            }
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error assessing performance impact: {e}'
            }
    
    def _check_code_quality(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Check code quality metrics"""
        try:
            # Get changed files
            changed_files = self._get_changed_files(fix_commit)
            
            if not changed_files:
                return {
                    'passed': True,
                    'score': 100,
                    'details': 'No code changes to analyze'
                }
            
            # Run code quality checks (simplified version)
            quality_checks = []
            
            # Check for Python code style
            python_files = [f for f in changed_files if f.endswith('.py')]
            if python_files:
                # Run flake8
                flake8_result = subprocess.run([
                    "flake8", "--max-line-length=100"
                ] + python_files, capture_output=True, text=True)
                
                quality_checks.append({
                    'check': 'flake8',
                    'passed': flake8_result.returncode == 0,
                    'output': flake8_result.stdout,
                    'errors': flake8_result.stderr
                })
                
                # Run pylint (simplified)
                pylint_result = subprocess.run([
                    "pylint", "--score=yes", "--reports=no"
                ] + python_files, capture_output=True, text=True)
                
                # Extract pylint score
                pylint_score = 0
                for line in pylint_result.stdout.split('\n'):
                    if 'Your code has been rated at' in line:
                        try:
                            score_part = line.split('rated at ')[1].split('/')[0]
                            pylint_score = float(score_part)
                        except:
                            pass
                
                quality_checks.append({
                    'check': 'pylint',
                    'passed': pylint_score >= 7.0,  # Minimum score of 7.0
                    'score': pylint_score,
                    'output': pylint_result.stdout
                })
            
            # Calculate overall quality score
            passed_checks = sum(1 for check in quality_checks if check['passed'])
            total_checks = len(quality_checks)
            overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
            
            return {
                'passed': overall_score >= 80,  # 80% of checks must pass
                'score': overall_score,
                'checks': quality_checks,
                'details': f'Code quality score: {overall_score:.1f}% ({passed_checks}/{total_checks} checks passed)'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error checking code quality: {e}'
            }
    
    def _scan_security_vulnerabilities(self, issue: TestIssue, fix_commit: str) -> Dict[str, Any]:
        """Scan for security vulnerabilities"""
        try:
            # Run security scan using bandit for Python code
            result = subprocess.run([
                "bandit", "-r", "backend/app/", "-f", "json"
            ], capture_output=True, text=True)
            
            # Parse bandit results
            try:
                if result.stdout:
                    bandit_data = json.loads(result.stdout)
                    
                    # Count high and medium severity issues
                    high_issues = len([i for i in bandit_data.get('results', []) if i.get('issue_severity') == 'HIGH'])
                    medium_issues = len([i for i in bandit_data.get('results', []) if i.get('issue_severity') == 'MEDIUM'])
                    
                    # Security scan passes if no high severity issues
                    passed = high_issues == 0
                    
                    return {
                        'passed': passed,
                        'high_severity_issues': high_issues,
                        'medium_severity_issues': medium_issues,
                        'scan_results': bandit_data.get('results', []),
                        'details': f'Security scan: {high_issues} high, {medium_issues} medium severity issues'
                    }
                else:
                    return {
                        'passed': True,
                        'details': 'No security issues found'
                    }
                    
            except json.JSONDecodeError:
                return {
                    'passed': False,
                    'error': 'Could not parse security scan results',
                    'details': 'Security scan output was not valid JSON'
                }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'details': f'Error running security scan: {e}'
            }
    
    def _get_changed_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit"""
        if not self.repo:
            return []
        
        try:
            commit = self.repo.commit(commit_hash)
            changed_files = []
            
            # Get files changed in this commit
            for item in commit.stats.files:
                changed_files.append(item)
            
            return changed_files
            
        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def _generate_recommendations(self, result: FixVerificationResult, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        # Check reproduction scripts
        if not result.reproduction_scripts_passed:
            recommendations.append("Create and run reproduction scripts to verify the bug is actually fixed")
        
        # Check regression tests
        if not result.regression_tests_passed:
            recommendations.append("Create regression tests to prevent this bug from reoccurring")
        
        # Check unit tests
        if not result.tests_passed:
            recommendations.append("Ensure unit tests cover the fixed code and are passing")
        
        # Check performance impact
        if result.performance_impact:
            for metric, value in result.performance_impact.items():
                if metric == 'document_processing_time' and value > 60:
                    recommendations.append("Consider optimizing document processing performance")
                elif metric == 'search_response_time' and value > 1.0:
                    recommendations.append("Consider optimizing search response time")
                elif metric == 'memory_usage' and value > 2048:
                    recommendations.append("Consider optimizing memory usage")
        
        # Check code quality
        if result.code_quality_score and result.code_quality_score < 80:
            recommendations.append("Improve code quality by addressing linting issues and following best practices")
        
        # Check security
        security_result = validation_results.get('security_scan', {})
        if security_result.get('high_severity_issues', 0) > 0:
            recommendations.append("Address high severity security issues before deploying the fix")
        
        # General recommendations based on verification status
        if result.verification_status == 'failed':
            recommendations.append("Fix must address all critical validation failures before approval")
        elif result.verification_status == 'partial':
            recommendations.append("Consider addressing remaining validation issues for better quality assurance")
        
        return recommendations
    
    def _save_verification_result(self, result: FixVerificationResult):
        """Save verification result to storage"""
        result_file = self.storage_path / "results" / f"verification_{result.issue_id}_{result.fix_commit[:8]}.json"
        
        # Convert result to dict for JSON serialization
        result_dict = asdict(result)
        result_dict['verification_time'] = result.verification_time.isoformat()
        
        with open(result_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
    
    def _generate_verification_report(self, result: FixVerificationResult, issue: TestIssue):
        """Generate human-readable verification report"""
        report_content = f"""# Fix Verification Report

## Issue Information
- **Issue ID**: {result.issue_id}
- **Issue Title**: {issue.title}
- **Fix Commit**: {result.fix_commit}
- **Verification Time**: {result.verification_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Verification Status**: {result.verification_status.upper()}

## Verification Summary
- **Tests Passed**: {'✅' if result.tests_passed else '❌'}
- **Reproduction Scripts Passed**: {'✅' if result.reproduction_scripts_passed else '❌'}
- **Regression Tests Passed**: {'✅' if result.regression_tests_passed else '❌'}

## Performance Impact
"""
        
        if result.performance_impact:
            for metric, value in result.performance_impact.items():
                report_content += f"- **{metric.replace('_', ' ').title()}**: {value}\n"
        else:
            report_content += "No performance impact data available.\n"
        
        report_content += f"""
## Code Quality Score
{result.code_quality_score if result.code_quality_score else 'Not assessed'}

## Detailed Results
"""
        
        for validation_name, validation_result in result.detailed_results.items():
            status = '✅' if validation_result.get('passed', False) else '❌'
            report_content += f"### {validation_name.replace('_', ' ').title()} {status}\n"
            report_content += f"{validation_result.get('details', 'No details available')}\n\n"
        
        report_content += f"""
## Recommendations
"""
        
        if result.recommendations:
            for i, recommendation in enumerate(result.recommendations, 1):
                report_content += f"{i}. {recommendation}\n"
        else:
            report_content += "No specific recommendations.\n"
        
        report_content += f"""
## Approval Status
"""
        
        if result.verification_status == 'passed':
            report_content += "✅ **APPROVED** - Fix meets all verification requirements and can be deployed.\n"
        elif result.verification_status == 'partial':
            report_content += "⚠️ **CONDITIONAL** - Fix passes critical requirements but has some issues to address.\n"
        else:
            report_content += "❌ **REJECTED** - Fix does not meet verification requirements and needs additional work.\n"
        
        # Save report
        report_file = self.storage_path / "reports" / f"verification_report_{result.issue_id}_{result.fix_commit[:8]}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
    
    def get_verification_history(self, issue_id: str) -> List[FixVerificationResult]:
        """Get verification history for an issue"""
        results = []
        results_dir = self.storage_path / "results"
        
        if not results_dir.exists():
            return results
        
        # Find all verification files for this issue
        for result_file in results_dir.glob(f"verification_{issue_id}_*.json"):
            try:
                with open(result_file, 'r') as f:
                    result_data = json.load(f)
                
                # Convert datetime string back to datetime object
                result_data['verification_time'] = datetime.fromisoformat(result_data['verification_time'])
                
                result = FixVerificationResult(**result_data)
                results.append(result)
                
            except Exception as e:
                print(f"Error loading verification result {result_file}: {e}")
        
        # Sort by verification time (newest first)
        results.sort(key=lambda x: x.verification_time, reverse=True)
        
        return results
    
    def approve_fix(self, issue_id: str, fix_commit: str, approver: str) -> Dict[str, Any]:
        """Approve a fix after verification"""
        # Get the latest verification result
        verification_results = self.get_verification_history(issue_id)
        
        if not verification_results:
            return {
                'success': False,
                'error': 'No verification results found for this issue'
            }
        
        latest_result = verification_results[0]
        
        if latest_result.fix_commit != fix_commit:
            return {
                'success': False,
                'error': f'Latest verification is for commit {latest_result.fix_commit}, not {fix_commit}'
            }
        
        if latest_result.verification_status != 'passed':
            return {
                'success': False,
                'error': f'Fix verification status is {latest_result.verification_status}, not passed'
            }
        
        # Record approval
        approval_data = {
            'issue_id': issue_id,
            'fix_commit': fix_commit,
            'approver': approver,
            'approval_time': datetime.now().isoformat(),
            'verification_result_id': f"{latest_result.issue_id}_{latest_result.fix_commit[:8]}"
        }
        
        approval_file = self.storage_path / "results" / f"approval_{issue_id}_{fix_commit[:8]}.json"
        with open(approval_file, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        return {
            'success': True,
            'approval_data': approval_data,
            'message': f'Fix for issue {issue_id} approved by {approver}'
        }