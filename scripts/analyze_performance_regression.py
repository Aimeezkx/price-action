#!/usr/bin/env python3
"""
Performance regression analysis tool for automated testing pipeline.
Compares current performance results against baseline to detect regressions.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import statistics


class PerformanceAnalyzer:
    """Analyze performance test results for regressions"""
    
    def __init__(self, threshold: float = 0.2):
        """
        Initialize analyzer with regression threshold
        
        Args:
            threshold: Regression threshold as percentage (0.2 = 20% slower is regression)
        """
        self.threshold = threshold
        self.regressions = []
        self.improvements = []
        self.stable_metrics = []
    
    def load_results(self, file_path: str) -> Dict[str, Any]:
        """Load performance results from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Performance results file {file_path} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {e}")
            return {}
    
    def compare_benchmarks(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current benchmarks against baseline"""
        comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'threshold': self.threshold,
            'regressions': [],
            'improvements': [],
            'stable': [],
            'new_benchmarks': [],
            'missing_benchmarks': [],
            'overall_status': 'PASS'
        }
        
        current_benchmarks = self._extract_benchmarks(current)
        baseline_benchmarks = self._extract_benchmarks(baseline)
        
        # Find new benchmarks
        current_names = set(current_benchmarks.keys())
        baseline_names = set(baseline_benchmarks.keys())
        
        new_benchmarks = current_names - baseline_names
        missing_benchmarks = baseline_names - current_names
        common_benchmarks = current_names & baseline_names
        
        comparison_results['new_benchmarks'] = list(new_benchmarks)
        comparison_results['missing_benchmarks'] = list(missing_benchmarks)
        
        # Compare common benchmarks
        for benchmark_name in common_benchmarks:
            current_data = current_benchmarks[benchmark_name]
            baseline_data = baseline_benchmarks[benchmark_name]
            
            comparison = self._compare_benchmark(benchmark_name, current_data, baseline_data)
            
            if comparison['status'] == 'REGRESSION':
                comparison_results['regressions'].append(comparison)
                comparison_results['overall_status'] = 'FAIL'
            elif comparison['status'] == 'IMPROVEMENT':
                comparison_results['improvements'].append(comparison)
            else:
                comparison_results['stable'].append(comparison)
        
        return comparison_results
    
    def _extract_benchmarks(self, results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract benchmark data from results"""
        benchmarks = {}
        
        # Handle different result formats
        if 'benchmarks' in results:
            # Direct benchmark format
            for benchmark in results['benchmarks']:
                name = benchmark.get('name', 'unknown')
                benchmarks[name] = benchmark
        elif 'summary' in results:
            # Summary format with nested benchmarks
            summary = results['summary']
            for key, value in summary.items():
                if isinstance(value, dict) and 'average_time' in value:
                    benchmarks[key] = value
        else:
            # Try to find benchmark-like data
            for key, value in results.items():
                if isinstance(value, dict) and any(metric in value for metric in ['time', 'duration', 'latency']):
                    benchmarks[key] = value
        
        return benchmarks
    
    def _compare_benchmark(self, name: str, current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare a single benchmark against baseline"""
        comparison = {
            'name': name,
            'current': current,
            'baseline': baseline,
            'status': 'STABLE',
            'change_percent': 0.0,
            'change_absolute': 0.0,
            'metrics': {}
        }
        
        # Compare different metrics
        metrics_to_compare = ['average_time', 'time', 'duration', 'latency', 'response_time']
        
        for metric in metrics_to_compare:
            if metric in current and metric in baseline:
                current_value = self._extract_numeric_value(current[metric])
                baseline_value = self._extract_numeric_value(baseline[metric])
                
                if current_value is not None and baseline_value is not None and baseline_value > 0:
                    change_percent = ((current_value - baseline_value) / baseline_value) * 100
                    change_absolute = current_value - baseline_value
                    
                    comparison['metrics'][metric] = {
                        'current': current_value,
                        'baseline': baseline_value,
                        'change_percent': change_percent,
                        'change_absolute': change_absolute
                    }
                    
                    # Determine overall status based on primary metric
                    if metric == 'average_time' or len(comparison['metrics']) == 1:
                        comparison['change_percent'] = change_percent
                        comparison['change_absolute'] = change_absolute
                        
                        if change_percent > (self.threshold * 100):
                            comparison['status'] = 'REGRESSION'
                        elif change_percent < -(self.threshold * 100):
                            comparison['status'] = 'IMPROVEMENT'
        
        return comparison
    
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        elif isinstance(value, dict):
            # Try common keys for numeric values
            for key in ['value', 'mean', 'average', 'median']:
                if key in value:
                    return self._extract_numeric_value(value[key])
        return None
    
    def generate_report(self, comparison_results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Generate human-readable regression report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append("PERFORMANCE REGRESSION ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {comparison_results['timestamp']}")
        report_lines.append(f"Regression Threshold: {comparison_results['threshold'] * 100:.1f}%")
        report_lines.append(f"Overall Status: {comparison_results['overall_status']}")
        report_lines.append("")
        
        # Summary
        report_lines.append("SUMMARY:")
        report_lines.append(f"  Regressions: {len(comparison_results['regressions'])}")
        report_lines.append(f"  Improvements: {len(comparison_results['improvements'])}")
        report_lines.append(f"  Stable: {len(comparison_results['stable'])}")
        report_lines.append(f"  New Benchmarks: {len(comparison_results['new_benchmarks'])}")
        report_lines.append(f"  Missing Benchmarks: {len(comparison_results['missing_benchmarks'])}")
        report_lines.append("")
        
        # Regressions (most important)
        if comparison_results['regressions']:
            report_lines.append("🚨 PERFORMANCE REGRESSIONS DETECTED:")
            report_lines.append("-" * 40)
            for regression in comparison_results['regressions']:
                report_lines.append(f"  {regression['name']}:")
                report_lines.append(f"    Change: {regression['change_percent']:+.1f}% ({regression['change_absolute']:+.3f}s)")
                
                for metric, data in regression['metrics'].items():
                    report_lines.append(f"    {metric}: {data['baseline']:.3f}s → {data['current']:.3f}s")
                report_lines.append("")
        
        # Improvements
        if comparison_results['improvements']:
            report_lines.append("✅ PERFORMANCE IMPROVEMENTS:")
            report_lines.append("-" * 40)
            for improvement in comparison_results['improvements']:
                report_lines.append(f"  {improvement['name']}:")
                report_lines.append(f"    Change: {improvement['change_percent']:+.1f}% ({improvement['change_absolute']:+.3f}s)")
                report_lines.append("")
        
        # New benchmarks
        if comparison_results['new_benchmarks']:
            report_lines.append("🆕 NEW BENCHMARKS:")
            report_lines.append("-" * 40)
            for benchmark in comparison_results['new_benchmarks']:
                report_lines.append(f"  {benchmark}")
            report_lines.append("")
        
        # Missing benchmarks
        if comparison_results['missing_benchmarks']:
            report_lines.append("⚠️  MISSING BENCHMARKS:")
            report_lines.append("-" * 40)
            for benchmark in comparison_results['missing_benchmarks']:
                report_lines.append(f"  {benchmark}")
            report_lines.append("")
        
        # Stable benchmarks (summary only)
        if comparison_results['stable']:
            report_lines.append(f"✓ STABLE BENCHMARKS ({len(comparison_results['stable'])}):")
            report_lines.append("-" * 40)
            for stable in comparison_results['stable'][:5]:  # Show first 5
                report_lines.append(f"  {stable['name']}: {stable['change_percent']:+.1f}%")
            if len(comparison_results['stable']) > 5:
                report_lines.append(f"  ... and {len(comparison_results['stable']) - 5} more")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_content)
            print(f"Regression report saved to: {output_file}")
        
        return report_content
    
    def create_baseline(self, results: Dict[str, Any], baseline_file: str):
        """Create or update performance baseline"""
        baseline_data = {
            'created_at': datetime.now().isoformat(),
            'benchmarks': self._extract_benchmarks(results),
            'metadata': {
                'source': 'automated_baseline_creation',
                'total_benchmarks': len(self._extract_benchmarks(results))
            }
        }
        
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"Performance baseline created: {baseline_file}")
        return baseline_data


def main():
    parser = argparse.ArgumentParser(description='Analyze performance regression')
    parser.add_argument('--current', required=True, help='Current performance results file')
    parser.add_argument('--baseline', required=True, help='Baseline performance results file')
    parser.add_argument('--threshold', type=float, default=0.2, help='Regression threshold (default: 0.2 = 20%)')
    parser.add_argument('--output', help='Output file for regression report')
    parser.add_argument('--create-baseline', action='store_true', help='Create baseline from current results')
    parser.add_argument('--fail-on-regression', action='store_true', help='Exit with error code if regressions found')
    
    args = parser.parse_args()
    
    analyzer = PerformanceAnalyzer(threshold=args.threshold)
    
    # Load current results
    current_results = analyzer.load_results(args.current)
    if not current_results:
        print(f"Error: Could not load current results from {args.current}")
        sys.exit(1)
    
    # Handle baseline creation
    if args.create_baseline:
        analyzer.create_baseline(current_results, args.baseline)
        print("Baseline created successfully!")
        return
    
    # Load baseline results
    baseline_results = analyzer.load_results(args.baseline)
    if not baseline_results:
        print(f"Warning: Could not load baseline results from {args.baseline}")
        print("Creating new baseline from current results...")
        analyzer.create_baseline(current_results, args.baseline)
        return
    
    # Perform comparison
    comparison_results = analyzer.compare_benchmarks(current_results, baseline_results)
    
    # Generate report
    report_content = analyzer.generate_report(comparison_results, args.output)
    
    # Print summary to console
    print(report_content)
    
    # Exit with appropriate code
    if args.fail_on_regression and comparison_results['overall_status'] == 'FAIL':
        print(f"\n❌ Performance regressions detected! {len(comparison_results['regressions'])} benchmark(s) regressed.")
        sys.exit(1)
    elif comparison_results['overall_status'] == 'FAIL':
        print(f"\n⚠️  Performance regressions detected but not failing build. {len(comparison_results['regressions'])} benchmark(s) regressed.")
    else:
        print(f"\n✅ No performance regressions detected!")
    
    sys.exit(0)


if __name__ == '__main__':
    main()