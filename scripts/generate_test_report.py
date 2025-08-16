#!/usr/bin/env python3
"""
Comprehensive test report generator for the automated testing pipeline.
Aggregates results from all test types and generates detailed reports.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from jinja2 import Template
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("Warning: Visualization libraries not available. Install matplotlib, seaborn, pandas, jinja2 for full functionality.")


class TestResultParser:
    """Parse test results from various formats"""
    
    def parse_junit_xml(self, file_path: str) -> Dict[str, Any]:
        """Parse JUnit XML test results"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            result = {
                'type': 'junit',
                'total_tests': int(root.get('tests', 0)),
                'failures': int(root.get('failures', 0)),
                'errors': int(root.get('errors', 0)),
                'skipped': int(root.get('skipped', 0)),
                'time': float(root.get('time', 0)),
                'test_cases': []
            }
            
            for testcase in root.findall('.//testcase'):
                case = {
                    'name': testcase.get('name'),
                    'classname': testcase.get('classname'),
                    'time': float(testcase.get('time', 0)),
                    'status': 'passed'
                }
                
                if testcase.find('failure') is not None:
                    case['status'] = 'failed'
                    case['failure'] = testcase.find('failure').text
                elif testcase.find('error') is not None:
                    case['status'] = 'error'
                    case['error'] = testcase.find('error').text
                elif testcase.find('skipped') is not None:
                    case['status'] = 'skipped'
                
                result['test_cases'].append(case)
            
            result['passed'] = result['total_tests'] - result['failures'] - result['errors'] - result['skipped']
            result['success_rate'] = (result['passed'] / result['total_tests']) * 100 if result['total_tests'] > 0 else 0
            
            return result
        except Exception as e:
            print(f"Error parsing JUnit XML {file_path}: {e}")
            return {'type': 'junit', 'error': str(e)}
    
    def parse_coverage_xml(self, file_path: str) -> Dict[str, Any]:
        """Parse coverage XML results"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            result = {
                'type': 'coverage',
                'line_rate': float(root.get('line-rate', 0)) * 100,
                'branch_rate': float(root.get('branch-rate', 0)) * 100,
                'packages': []
            }
            
            for package in root.findall('.//package'):
                pkg = {
                    'name': package.get('name'),
                    'line_rate': float(package.get('line-rate', 0)) * 100,
                    'branch_rate': float(package.get('branch-rate', 0)) * 100,
                    'classes': []
                }
                
                for cls in package.findall('.//class'):
                    cls_info = {
                        'name': cls.get('name'),
                        'filename': cls.get('filename'),
                        'line_rate': float(cls.get('line-rate', 0)) * 100,
                        'branch_rate': float(cls.get('branch-rate', 0)) * 100
                    }
                    pkg['classes'].append(cls_info)
                
                result['packages'].append(pkg)
            
            return result
        except Exception as e:
            print(f"Error parsing coverage XML {file_path}: {e}")
            return {'type': 'coverage', 'error': str(e)}
    
    def parse_performance_json(self, file_path: str) -> Dict[str, Any]:
        """Parse performance test results"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            result = {
                'type': 'performance',
                'benchmarks': data.get('benchmarks', []),
                'summary': data.get('summary', {}),
                'timestamp': data.get('timestamp', datetime.now().isoformat())
            }
            
            return result
        except Exception as e:
            print(f"Error parsing performance JSON {file_path}: {e}")
            return {'type': 'performance', 'error': str(e)}
    
    def parse_security_json(self, file_path: str) -> Dict[str, Any]:
        """Parse security test results (Bandit format)"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            result = {
                'type': 'security',
                'results': data.get('results', []),
                'metrics': data.get('metrics', {}),
                'generated_at': data.get('generated_at', datetime.now().isoformat())
            }
            
            # Categorize issues by severity
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for issue in result['results']:
                severity = issue.get('issue_severity', 'LOW')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            result['severity_counts'] = severity_counts
            result['total_issues'] = len(result['results'])
            
            return result
        except Exception as e:
            print(f"Error parsing security JSON {file_path}: {e}")
            return {'type': 'security', 'error': str(e)}


class TestReportGenerator:
    """Generate comprehensive test reports"""
    
    def __init__(self, artifacts_dir: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.parser = TestResultParser()
        self.results = {}
        
    def collect_results(self):
        """Collect all test results from artifacts directory"""
        print(f"Collecting test results from {self.artifacts_dir}")
        
        # Collect unit test results
        self._collect_junit_results('unit')
        
        # Collect integration test results
        self._collect_junit_results('integration')
        
        # Collect E2E test results
        self._collect_junit_results('e2e')
        
        # Collect security test results
        self._collect_junit_results('security')
        
        # Collect coverage results
        self._collect_coverage_results()
        
        # Collect performance results
        self._collect_performance_results()
        
        # Collect security scan results
        self._collect_security_scan_results()
        
        print(f"Collected results for: {list(self.results.keys())}")
    
    def _collect_junit_results(self, test_type: str):
        """Collect JUnit XML results for a specific test type"""
        pattern = f"*{test_type}*results*.xml"
        xml_files = list(self.artifacts_dir.rglob(pattern))
        
        if xml_files:
            for xml_file in xml_files:
                result = self.parser.parse_junit_xml(str(xml_file))
                if 'error' not in result:
                    if test_type not in self.results:
                        self.results[test_type] = []
                    self.results[test_type].append(result)
                    print(f"Parsed {test_type} results from {xml_file}")
    
    def _collect_coverage_results(self):
        """Collect coverage results"""
        coverage_files = list(self.artifacts_dir.rglob("*coverage*.xml"))
        
        if coverage_files:
            self.results['coverage'] = []
            for coverage_file in coverage_files:
                result = self.parser.parse_coverage_xml(str(coverage_file))
                if 'error' not in result:
                    self.results['coverage'].append(result)
                    print(f"Parsed coverage results from {coverage_file}")
    
    def _collect_performance_results(self):
        """Collect performance test results"""
        perf_files = list(self.artifacts_dir.rglob("*performance*.json"))
        
        if perf_files:
            self.results['performance'] = []
            for perf_file in perf_files:
                result = self.parser.parse_performance_json(str(perf_file))
                if 'error' not in result:
                    self.results['performance'].append(result)
                    print(f"Parsed performance results from {perf_file}")
    
    def _collect_security_scan_results(self):
        """Collect security scan results"""
        security_files = list(self.artifacts_dir.rglob("*bandit*.json"))
        
        if security_files:
            self.results['security_scan'] = []
            for security_file in security_files:
                result = self.parser.parse_security_json(str(security_file))
                if 'error' not in result:
                    self.results['security_scan'].append(result)
                    print(f"Parsed security scan results from {security_file}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate overall test summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'total_skipped': 0,
            'overall_success_rate': 0,
            'coverage_rate': 0,
            'performance_issues': 0,
            'security_issues': 0,
            'test_types': {}
        }
        
        # Aggregate test results
        for test_type, results in self.results.items():
            if test_type in ['unit', 'integration', 'e2e', 'security']:
                type_summary = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': 0,
                    'skipped': 0,
                    'success_rate': 0
                }
                
                for result in results:
                    if isinstance(result, dict) and 'total_tests' in result:
                        type_summary['total'] += result['total_tests']
                        type_summary['passed'] += result.get('passed', 0)
                        type_summary['failed'] += result.get('failures', 0)
                        type_summary['errors'] += result.get('errors', 0)
                        type_summary['skipped'] += result.get('skipped', 0)
                
                if type_summary['total'] > 0:
                    type_summary['success_rate'] = (type_summary['passed'] / type_summary['total']) * 100
                
                summary['test_types'][test_type] = type_summary
                summary['total_tests'] += type_summary['total']
                summary['total_passed'] += type_summary['passed']
                summary['total_failed'] += type_summary['failed']
                summary['total_errors'] += type_summary['errors']
                summary['total_skipped'] += type_summary['skipped']
        
        # Calculate overall success rate
        if summary['total_tests'] > 0:
            summary['overall_success_rate'] = (summary['total_passed'] / summary['total_tests']) * 100
        
        # Get coverage rate
        if 'coverage' in self.results and self.results['coverage']:
            coverage_rates = [r.get('line_rate', 0) for r in self.results['coverage']]
            summary['coverage_rate'] = sum(coverage_rates) / len(coverage_rates)
        
        # Count security issues
        if 'security_scan' in self.results:
            for result in self.results['security_scan']:
                summary['security_issues'] += result.get('total_issues', 0)
        
        return summary
    
    def generate_html_report(self, output_file: str):
        """Generate HTML test report"""
        summary = self.generate_summary()
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; margin-top: 5px; }
        .success { border-left-color: #28a745; }
        .success .metric-value { color: #28a745; }
        .warning { border-left-color: #ffc107; }
        .warning .metric-value { color: #ffc107; }
        .danger { border-left-color: #dc3545; }
        .danger .metric-value { color: #dc3545; }
        .section { margin-bottom: 30px; }
        .section h2 { border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .test-type { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .progress-bar { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #28a745; transition: width 0.3s ease; }
        .test-details { margin-top: 15px; }
        .test-case { padding: 5px 0; border-bottom: 1px solid #eee; }
        .status-passed { color: #28a745; }
        .status-failed { color: #dc3545; }
        .status-error { color: #fd7e14; }
        .status-skipped { color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Comprehensive Test Report</h1>
            <p class="timestamp">Generated on {{ summary.timestamp }}</p>
        </div>
        
        <div class="summary">
            <div class="metric-card {% if summary.overall_success_rate >= 95 %}success{% elif summary.overall_success_rate >= 80 %}warning{% else %}danger{% endif %}">
                <div class="metric-value">{{ "%.1f"|format(summary.overall_success_rate) }}%</div>
                <div class="metric-label">Overall Success Rate</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value">{{ summary.total_tests }}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            
            <div class="metric-card success">
                <div class="metric-value">{{ summary.total_passed }}</div>
                <div class="metric-label">Passed</div>
            </div>
            
            <div class="metric-card danger">
                <div class="metric-value">{{ summary.total_failed + summary.total_errors }}</div>
                <div class="metric-label">Failed/Errors</div>
            </div>
            
            <div class="metric-card {% if summary.coverage_rate >= 90 %}success{% elif summary.coverage_rate >= 70 %}warning{% else %}danger{% endif %}">
                <div class="metric-value">{{ "%.1f"|format(summary.coverage_rate) }}%</div>
                <div class="metric-label">Code Coverage</div>
            </div>
            
            <div class="metric-card {% if summary.security_issues == 0 %}success{% else %}danger{% endif %}">
                <div class="metric-value">{{ summary.security_issues }}</div>
                <div class="metric-label">Security Issues</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Test Results by Type</h2>
            {% for test_type, type_data in summary.test_types.items() %}
            <div class="test-type">
                <h3>{{ test_type.title() }} Tests</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ type_data.success_rate }}%"></div>
                </div>
                <p>{{ type_data.passed }}/{{ type_data.total }} tests passed ({{ "%.1f"|format(type_data.success_rate) }}%)</p>
                {% if type_data.failed > 0 or type_data.errors > 0 %}
                <p class="status-failed">{{ type_data.failed }} failed, {{ type_data.errors }} errors</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        {% if results.coverage %}
        <div class="section">
            <h2>Code Coverage Details</h2>
            {% for coverage in results.coverage %}
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Line Coverage</th>
                        <th>Branch Coverage</th>
                    </tr>
                </thead>
                <tbody>
                    {% for package in coverage.packages %}
                    <tr>
                        <td>{{ package.name }}</td>
                        <td>{{ "%.1f"|format(package.line_rate) }}%</td>
                        <td>{{ "%.1f"|format(package.branch_rate) }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if results.performance %}
        <div class="section">
            <h2>Performance Test Results</h2>
            {% for perf in results.performance %}
            <table>
                <thead>
                    <tr>
                        <th>Benchmark</th>
                        <th>Average Time</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for benchmark in perf.benchmarks %}
                    <tr>
                        <td>{{ benchmark.name }}</td>
                        <td>{{ "%.3f"|format(benchmark.average_time) }}s</td>
                        <td class="{% if benchmark.passed %}status-passed{% else %}status-failed{% endif %}">
                            {{ "PASS" if benchmark.passed else "FAIL" }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if results.security_scan %}
        <div class="section">
            <h2>Security Scan Results</h2>
            {% for security in results.security_scan %}
            <div class="test-type">
                <h3>Security Issues by Severity</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for severity, count in security.severity_counts.items() %}
                        <tr>
                            <td class="{% if severity == 'HIGH' %}status-failed{% elif severity == 'MEDIUM' %}warning{% else %}status-skipped{% endif %}">
                                {{ severity }}
                            </td>
                            <td>{{ count }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        html_content = template.render(summary=summary, results=self.results)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_file}")
    
    def generate_json_report(self, output_file: str):
        """Generate JSON test report"""
        summary = self.generate_summary()
        
        report = {
            'summary': summary,
            'detailed_results': self.results,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"JSON report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive test reports')
    parser.add_argument('--artifacts-dir', required=True, help='Directory containing test artifacts')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['html', 'json'], default='html', help='Output format')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.artifacts_dir):
        print(f"Error: Artifacts directory {args.artifacts_dir} does not exist")
        sys.exit(1)
    
    generator = TestReportGenerator(args.artifacts_dir)
    generator.collect_results()
    
    if args.format == 'html':
        generator.generate_html_report(args.output)
    else:
        generator.generate_json_report(args.output)
    
    print("Test report generation completed successfully!")


if __name__ == '__main__':
    main()