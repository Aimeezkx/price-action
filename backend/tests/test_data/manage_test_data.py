#!/usr/bin/env python3
"""
Test Data Management CLI

Command-line interface for managing test data including generation,
cleanup, snapshots, and analytics.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_data.test_document_generator import TestDocumentGenerator
from tests.test_data.synthetic_data_generator import SyntheticDataGenerator
from tests.test_data.test_data_manager import TestDataManager
from tests.test_data.performance_baseline_manager import PerformanceBaselineManager
from tests.test_data.test_result_tracker import TestResultTracker, create_sample_test_results


def generate_documents(args):
    """Generate test documents"""
    print("Generating test documents...")
    generator = TestDocumentGenerator(args.output_dir)
    generator.generate_all_test_documents()
    print("✓ Test documents generated successfully")


def generate_synthetic_data(args):
    """Generate synthetic test data"""
    print("Generating synthetic test data...")
    generator = SyntheticDataGenerator(args.output_dir)
    generator.generate_all_synthetic_data()
    print("✓ Synthetic test data generated successfully")


def create_baselines(args):
    """Create performance baselines"""
    print("Creating performance baselines...")
    manager = PerformanceBaselineManager(args.data_dir)
    manager.create_initial_baselines()
    print("✓ Performance baselines created successfully")


def create_snapshot(args):
    """Create test data snapshot"""
    print(f"Creating snapshot '{args.name}'...")
    manager = TestDataManager(args.data_dir)
    snapshot_id = manager.create_data_snapshot(args.name, args.description or "")
    print(f"✓ Snapshot created: {snapshot_id}")


def restore_snapshot(args):
    """Restore test data from snapshot"""
    print(f"Restoring snapshot '{args.snapshot_id}'...")
    manager = TestDataManager(args.data_dir)
    manager.restore_data_snapshot(args.snapshot_id)
    print("✓ Snapshot restored successfully")


def cleanup_data(args):
    """Clean up test data"""
    manager = TestDataManager(args.data_dir)
    
    if args.all:
        print("Cleaning up all test data...")
        manager.cleanup_all_test_data()
        print("✓ All test data cleaned up")
    elif args.snapshots:
        print(f"Cleaning up old snapshots (keeping {args.keep} most recent)...")
        manager.cleanup_old_snapshots(args.keep)
        print("✓ Old snapshots cleaned up")
    elif args.results:
        print(f"Cleaning up test results older than {args.days} days...")
        tracker = TestResultTracker(args.data_dir + "/results")
        result = tracker.cleanup_old_results(args.days)
        print(f"✓ Cleaned up {result['deleted_results']} test results and {result['deleted_suites']} suite runs")


def show_stats(args):
    """Show test data statistics"""
    manager = TestDataManager(args.data_dir)
    stats = manager.get_test_data_stats()
    
    print("\n=== Test Data Statistics ===")
    print(f"Total size: {stats['total_size_bytes'] / (1024*1024):.2f} MB")
    print(f"Active contexts: {stats['active_contexts']}")
    print(f"Temporary directories: {stats['temp_dirs']}")
    print(f"Temporary databases: {stats['temp_databases']}")
    print(f"Snapshots: {stats['snapshot_count']}")
    
    print("\nFile counts by type:")
    for file_type, count in stats['file_counts'].items():
        print(f"  {file_type}: {count}")
        
    # Test results statistics
    try:
        tracker = TestResultTracker(args.data_dir + "/results")
        report = tracker.generate_test_report(7)
        
        print("\n=== Test Results (Last 7 Days) ===")
        overall = report['overall_statistics']
        print(f"Total tests: {overall['total_tests']}")
        print(f"Pass rate: {overall['pass_rate_percent']:.1f}%")
        print(f"Average duration: {overall['avg_duration_ms']:.0f}ms")
        
        if report['flaky_tests']:
            print(f"Flaky tests: {len(report['flaky_tests'])}")
            
    except Exception as e:
        print(f"\nCould not load test results: {e}")


def validate_data(args):
    """Validate test data integrity"""
    print("Validating test data integrity...")
    manager = TestDataManager(args.data_dir)
    validation = manager.validate_test_data_integrity()
    
    if validation['valid']:
        print("✓ All test data is valid")
    else:
        print("✗ Test data validation failed")
        
    print(f"\nChecked {validation['checked_files']} files")
    
    if validation['errors']:
        print("\nErrors found:")
        for error in validation['errors']:
            print(f"  - {error}")
            
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
            
    if validation['corrupted_files']:
        print("\nCorrupted files:")
        for file_path in validation['corrupted_files']:
            print(f"  - {file_path}")


def generate_test_results(args):
    """Generate sample test results"""
    print("Generating sample test results...")
    create_sample_test_results()
    print("✓ Sample test results generated successfully")


def show_test_report(args):
    """Show test results report"""
    tracker = TestResultTracker(args.data_dir + "/results")
    report = tracker.generate_test_report(args.days)
    
    print(f"\n=== Test Report (Last {args.days} Days) ===")
    print(f"Generated at: {report['generated_at']}")
    
    # Overall statistics
    overall = report['overall_statistics']
    print(f"\nOverall Statistics:")
    print(f"  Total tests: {overall['total_tests']}")
    print(f"  Passed: {overall['passed_tests']} ({overall['pass_rate_percent']:.1f}%)")
    print(f"  Failed: {overall['failed_tests']}")
    print(f"  Errors: {overall['error_tests']}")
    print(f"  Skipped: {overall['skipped_tests']}")
    print(f"  Average duration: {overall['avg_duration_ms']:.0f}ms")
    
    # Suite statistics
    suite = report['suite_statistics']
    print(f"\nSuite Statistics:")
    print(f"  Total runs: {suite['total_runs']}")
    print(f"  Average suite duration: {suite['avg_suite_duration_ms']:.0f}ms")
    print(f"  Average pass rate: {suite['avg_pass_rate_percent']:.1f}%")
    
    # Flaky tests
    if report['flaky_tests']:
        print(f"\nFlaky Tests ({len(report['flaky_tests'])}):")
        for test in report['flaky_tests'][:5]:  # Show top 5
            print(f"  - {test['test_name']}: {test['flakiness_score']:.2%} failure rate")
            
    # Slowest tests
    if report['slowest_tests']:
        print(f"\nSlowest Tests:")
        for test in report['slowest_tests'][:5]:  # Show top 5
            print(f"  - {test['test_name']}: {test['avg_duration']:.0f}ms avg")
            
    # Common failures
    if report['failure_analysis']['common_failures']:
        print(f"\nCommon Failures:")
        for failure in report['failure_analysis']['common_failures'][:3]:  # Show top 3
            print(f"  - {failure['error_message'][:60]}... ({failure['failure_count']} times)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test Data Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate documents --output-dir ./test_docs
  %(prog)s generate synthetic --output-dir ./synthetic
  %(prog)s create-baselines --data-dir ./performance
  %(prog)s snapshot create --name "before_refactor" --description "Baseline before major refactor"
  %(prog)s cleanup --all
  %(prog)s stats --data-dir ./test_data
  %(prog)s validate --data-dir ./test_data
  %(prog)s report --days 30
        """
    )
    
    parser.add_argument(
        '--data-dir',
        default='backend/tests/test_data',
        help='Base directory for test data (default: backend/tests/test_data)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate test data')
    generate_subparsers = generate_parser.add_subparsers(dest='generate_type')
    
    # Generate documents
    docs_parser = generate_subparsers.add_parser('documents', help='Generate test documents')
    docs_parser.add_argument('--output-dir', default='backend/tests/test_data/documents',
                           help='Output directory for documents')
    docs_parser.set_defaults(func=generate_documents)
    
    # Generate synthetic data
    synthetic_parser = generate_subparsers.add_parser('synthetic', help='Generate synthetic test data')
    synthetic_parser.add_argument('--output-dir', default='backend/tests/test_data/synthetic',
                                help='Output directory for synthetic data')
    synthetic_parser.set_defaults(func=generate_synthetic_data)
    
    # Generate test results
    results_parser = generate_subparsers.add_parser('results', help='Generate sample test results')
    results_parser.set_defaults(func=generate_test_results)
    
    # Create baselines command
    baselines_parser = subparsers.add_parser('create-baselines', help='Create performance baselines')
    baselines_parser.set_defaults(func=create_baselines)
    
    # Snapshot commands
    snapshot_parser = subparsers.add_parser('snapshot', help='Manage data snapshots')
    snapshot_subparsers = snapshot_parser.add_subparsers(dest='snapshot_action')
    
    # Create snapshot
    create_snap_parser = snapshot_subparsers.add_parser('create', help='Create data snapshot')
    create_snap_parser.add_argument('--name', required=True, help='Snapshot name')
    create_snap_parser.add_argument('--description', help='Snapshot description')
    create_snap_parser.set_defaults(func=create_snapshot)
    
    # Restore snapshot
    restore_snap_parser = snapshot_subparsers.add_parser('restore', help='Restore data snapshot')
    restore_snap_parser.add_argument('snapshot_id', help='Snapshot ID to restore')
    restore_snap_parser.set_defaults(func=restore_snapshot)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up test data')
    cleanup_group = cleanup_parser.add_mutually_exclusive_group(required=True)
    cleanup_group.add_argument('--all', action='store_true', help='Clean up all test data')
    cleanup_group.add_argument('--snapshots', action='store_true', help='Clean up old snapshots')
    cleanup_group.add_argument('--results', action='store_true', help='Clean up old test results')
    cleanup_parser.add_argument('--keep', type=int, default=10, help='Number of snapshots to keep')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Days of results to keep')
    cleanup_parser.set_defaults(func=cleanup_data)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show test data statistics')
    stats_parser.set_defaults(func=show_stats)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate test data integrity')
    validate_parser.set_defaults(func=validate_data)
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Show test results report')
    report_parser.add_argument('--days', type=int, default=7, help='Number of days to include in report')
    report_parser.set_defaults(func=show_test_report)
    
    # Parse arguments and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    try:
        if hasattr(args, 'func'):
            args.func(args)
        else:
            print(f"No handler for command: {args.command}")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())