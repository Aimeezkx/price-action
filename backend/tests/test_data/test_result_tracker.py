"""
Test Result History Tracker

Tracks test results over time, maintains history, and provides analytics
for test reliability, flakiness detection, and trend analysis.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestCategory(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOAD = "load"


@dataclass
class TestResult:
    """Represents a single test result"""
    id: str
    test_name: str
    test_category: TestCategory
    status: TestStatus
    duration_ms: float
    timestamp: str
    environment: str
    commit_hash: Optional[str]
    branch: str
    error_message: Optional[str]
    stack_trace: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class TestSuiteResult:
    """Represents results from a complete test suite run"""
    id: str
    suite_name: str
    timestamp: str
    environment: str
    commit_hash: Optional[str]
    branch: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration_ms: float
    test_results: List[TestResult]
    metadata: Dict[str, Any]


class TestResultTracker:
    """Tracks and analyzes test results over time"""
    
    def __init__(self, data_dir: str = "backend/tests/test_data/results"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "test_results.db"
        self.analytics_file = self.data_dir / "test_analytics.json"
        
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for test results"""
        conn = sqlite3.connect(str(self.db_path))
        
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS test_suite_runs (
                id TEXT PRIMARY KEY,
                suite_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                environment TEXT NOT NULL,
                commit_hash TEXT,
                branch TEXT NOT NULL,
                total_tests INTEGER NOT NULL,
                passed_tests INTEGER NOT NULL,
                failed_tests INTEGER NOT NULL,
                skipped_tests INTEGER NOT NULL,
                error_tests INTEGER NOT NULL,
                total_duration_ms REAL NOT NULL,
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                suite_run_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                test_category TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                timestamp TEXT NOT NULL,
                environment TEXT NOT NULL,
                commit_hash TEXT,
                branch TEXT NOT NULL,
                error_message TEXT,
                stack_trace TEXT,
                metadata TEXT,
                FOREIGN KEY (suite_run_id) REFERENCES test_suite_runs (id)
            );
            
            CREATE TABLE IF NOT EXISTS test_flakiness (
                test_name TEXT PRIMARY KEY,
                total_runs INTEGER NOT NULL,
                failed_runs INTEGER NOT NULL,
                flakiness_score REAL NOT NULL,
                last_failure TEXT,
                last_success TEXT,
                consecutive_failures INTEGER NOT NULL,
                consecutive_successes INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_test_results_name ON test_results(test_name);
            CREATE INDEX IF NOT EXISTS idx_test_results_timestamp ON test_results(timestamp);
            CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status);
            CREATE INDEX IF NOT EXISTS idx_suite_runs_timestamp ON test_suite_runs(timestamp);
        """)
        
        conn.close()
        
    def record_test_suite_result(self, suite_result: TestSuiteResult):
        """Record a complete test suite result"""
        conn = sqlite3.connect(str(self.db_path))
        
        try:
            # Insert suite run
            conn.execute("""
                INSERT INTO test_suite_runs 
                (id, suite_name, timestamp, environment, commit_hash, branch,
                 total_tests, passed_tests, failed_tests, skipped_tests, error_tests,
                 total_duration_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suite_result.id,
                suite_result.suite_name,
                suite_result.timestamp,
                suite_result.environment,
                suite_result.commit_hash,
                suite_result.branch,
                suite_result.total_tests,
                suite_result.passed_tests,
                suite_result.failed_tests,
                suite_result.skipped_tests,
                suite_result.error_tests,
                suite_result.total_duration_ms,
                json.dumps(suite_result.metadata)
            ))
            
            # Insert individual test results
            for test_result in suite_result.test_results:
                conn.execute("""
                    INSERT INTO test_results
                    (id, suite_run_id, test_name, test_category, status, duration_ms,
                     timestamp, environment, commit_hash, branch, error_message,
                     stack_trace, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    test_result.id,
                    suite_result.id,
                    test_result.test_name,
                    test_result.test_category.value,
                    test_result.status.value,
                    test_result.duration_ms,
                    test_result.timestamp,
                    test_result.environment,
                    test_result.commit_hash,
                    test_result.branch,
                    test_result.error_message,
                    test_result.stack_trace,
                    json.dumps(test_result.metadata)
                ))
                
                # Update flakiness tracking
                self._update_flakiness_tracking(conn, test_result)
                
            conn.commit()
            
        finally:
            conn.close()
            
        # Update analytics
        self._update_analytics()
        
    def get_test_history(self, test_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get history for a specific test"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor = conn.execute("""
            SELECT * FROM test_results 
            WHERE test_name = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (test_name, cutoff_date))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            if result['metadata']:
                result['metadata'] = json.loads(result['metadata'])
            results.append(result)
            
        conn.close()
        return results
        
    def get_flaky_tests(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Get tests that are considered flaky (failure rate above threshold)"""
        conn = sqlite3.connect(str(self.db_path))
        
        cursor = conn.execute("""
            SELECT * FROM test_flakiness 
            WHERE flakiness_score > ? AND total_runs >= 10
            ORDER BY flakiness_score DESC
        """, (threshold,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        conn.close()
        return results
        
    def get_test_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get overall test trends"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get daily pass rates
        cursor = conn.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_tests,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
                AVG(duration_ms) as avg_duration
            FROM test_results 
            WHERE timestamp > ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (cutoff_date,))
        
        daily_stats = []
        for row in cursor.fetchall():
            date, total, passed, avg_duration = row
            pass_rate = (passed / total) * 100 if total > 0 else 0
            daily_stats.append({
                "date": date,
                "total_tests": total,
                "passed_tests": passed,
                "pass_rate": pass_rate,
                "avg_duration_ms": avg_duration
            })
            
        # Get category breakdown
        cursor = conn.execute("""
            SELECT 
                test_category,
                COUNT(*) as total_tests,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
                AVG(duration_ms) as avg_duration
            FROM test_results 
            WHERE timestamp > ?
            GROUP BY test_category
        """, (cutoff_date,))
        
        category_stats = []
        for row in cursor.fetchall():
            category, total, passed, avg_duration = row
            pass_rate = (passed / total) * 100 if total > 0 else 0
            category_stats.append({
                "category": category,
                "total_tests": total,
                "passed_tests": passed,
                "pass_rate": pass_rate,
                "avg_duration_ms": avg_duration
            })
            
        conn.close()
        
        return {
            "daily_stats": daily_stats,
            "category_stats": category_stats,
            "period_days": days
        }
        
    def get_slowest_tests(self, limit: int = 20, days: int = 7) -> List[Dict[str, Any]]:
        """Get slowest tests by average duration"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor = conn.execute("""
            SELECT 
                test_name,
                test_category,
                COUNT(*) as run_count,
                AVG(duration_ms) as avg_duration,
                MAX(duration_ms) as max_duration,
                MIN(duration_ms) as min_duration
            FROM test_results 
            WHERE timestamp > ? AND status = 'passed'
            GROUP BY test_name, test_category
            HAVING run_count >= 3
            ORDER BY avg_duration DESC
            LIMIT ?
        """, (cutoff_date, limit))
        
        results = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        conn.close()
        return results
        
    def get_failure_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analyze test failures over time"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get most common failure reasons
        cursor = conn.execute("""
            SELECT 
                error_message,
                COUNT(*) as failure_count,
                COUNT(DISTINCT test_name) as affected_tests
            FROM test_results 
            WHERE timestamp > ? AND status IN ('failed', 'error') 
                AND error_message IS NOT NULL
            GROUP BY error_message
            ORDER BY failure_count DESC
            LIMIT 10
        """, (cutoff_date,))
        
        common_failures = []
        for row in cursor.fetchall():
            error_msg, count, affected_tests = row
            common_failures.append({
                "error_message": error_msg,
                "failure_count": count,
                "affected_tests": affected_tests
            })
            
        # Get tests with most failures
        cursor = conn.execute("""
            SELECT 
                test_name,
                test_category,
                COUNT(*) as failure_count,
                COUNT(DISTINCT DATE(timestamp)) as failure_days
            FROM test_results 
            WHERE timestamp > ? AND status IN ('failed', 'error')
            GROUP BY test_name, test_category
            ORDER BY failure_count DESC
            LIMIT 10
        """, (cutoff_date,))
        
        failing_tests = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            failing_tests.append(dict(zip(columns, row)))
            
        conn.close()
        
        return {
            "common_failures": common_failures,
            "failing_tests": failing_tests,
            "period_days": days
        }
        
    def generate_test_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Overall statistics
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_tests,
                SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed_tests,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tests,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_tests,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped_tests,
                AVG(duration_ms) as avg_duration,
                SUM(duration_ms) as total_duration
            FROM test_results 
            WHERE timestamp > ?
        """, (cutoff_date,))
        
        overall_stats = cursor.fetchone()
        total, passed, failed, errors, skipped, avg_duration, total_duration = overall_stats
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        
        # Suite run statistics
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_runs,
                AVG(total_duration_ms) as avg_suite_duration,
                AVG(CAST(passed_tests AS FLOAT) / total_tests * 100) as avg_pass_rate
            FROM test_suite_runs 
            WHERE timestamp > ?
        """, (cutoff_date,))
        
        suite_stats = cursor.fetchone()
        total_runs, avg_suite_duration, avg_suite_pass_rate = suite_stats
        
        conn.close()
        
        # Get additional analysis
        trends = self.get_test_trends(days)
        flaky_tests = self.get_flaky_tests()
        slowest_tests = self.get_slowest_tests(10, days)
        failure_analysis = self.get_failure_analysis(days)
        
        return {
            "report_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "overall_statistics": {
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "error_tests": errors,
                "skipped_tests": skipped,
                "pass_rate_percent": pass_rate,
                "avg_duration_ms": avg_duration,
                "total_duration_ms": total_duration
            },
            "suite_statistics": {
                "total_runs": total_runs,
                "avg_suite_duration_ms": avg_suite_duration,
                "avg_pass_rate_percent": avg_suite_pass_rate
            },
            "trends": trends,
            "flaky_tests": flaky_tests,
            "slowest_tests": slowest_tests,
            "failure_analysis": failure_analysis
        }
        
    def cleanup_old_results(self, days_to_keep: int = 90):
        """Clean up old test results to manage database size"""
        conn = sqlite3.connect(str(self.db_path))
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Delete old test results
        cursor = conn.execute("""
            DELETE FROM test_results WHERE timestamp < ?
        """, (cutoff_date,))
        
        deleted_results = cursor.rowcount
        
        # Delete old suite runs
        cursor = conn.execute("""
            DELETE FROM test_suite_runs WHERE timestamp < ?
        """, (cutoff_date,))
        
        deleted_suites = cursor.rowcount
        
        # Clean up orphaned flakiness records
        conn.execute("""
            DELETE FROM test_flakiness 
            WHERE test_name NOT IN (
                SELECT DISTINCT test_name FROM test_results
            )
        """)
        
        conn.commit()
        conn.close()
        
        return {
            "deleted_results": deleted_results,
            "deleted_suites": deleted_suites,
            "cutoff_date": cutoff_date
        }
        
    def _update_flakiness_tracking(self, conn: sqlite3.Connection, test_result: TestResult):
        """Update flakiness tracking for a test"""
        # Get current flakiness data
        cursor = conn.execute("""
            SELECT * FROM test_flakiness WHERE test_name = ?
        """, (test_result.test_name,))
        
        current = cursor.fetchone()
        
        if current:
            # Update existing record
            total_runs = current[1] + 1
            failed_runs = current[2] + (1 if test_result.status in [TestStatus.FAILED, TestStatus.ERROR] else 0)
            flakiness_score = failed_runs / total_runs
            
            if test_result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                last_failure = test_result.timestamp
                consecutive_failures = current[6] + 1
                consecutive_successes = 0
            else:
                last_failure = current[4]
                consecutive_failures = 0
                consecutive_successes = current[7] + 1
                
            last_success = test_result.timestamp if test_result.status == TestStatus.PASSED else current[5]
            
            conn.execute("""
                UPDATE test_flakiness 
                SET total_runs = ?, failed_runs = ?, flakiness_score = ?,
                    last_failure = ?, last_success = ?, consecutive_failures = ?,
                    consecutive_successes = ?, updated_at = ?
                WHERE test_name = ?
            """, (
                total_runs, failed_runs, flakiness_score, last_failure, last_success,
                consecutive_failures, consecutive_successes, datetime.now().isoformat(),
                test_result.test_name
            ))
        else:
            # Create new record
            total_runs = 1
            failed_runs = 1 if test_result.status in [TestStatus.FAILED, TestStatus.ERROR] else 0
            flakiness_score = failed_runs / total_runs
            
            last_failure = test_result.timestamp if test_result.status in [TestStatus.FAILED, TestStatus.ERROR] else None
            last_success = test_result.timestamp if test_result.status == TestStatus.PASSED else None
            consecutive_failures = 1 if test_result.status in [TestStatus.FAILED, TestStatus.ERROR] else 0
            consecutive_successes = 1 if test_result.status == TestStatus.PASSED else 0
            
            conn.execute("""
                INSERT INTO test_flakiness
                (test_name, total_runs, failed_runs, flakiness_score, last_failure,
                 last_success, consecutive_failures, consecutive_successes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_result.test_name, total_runs, failed_runs, flakiness_score,
                last_failure, last_success, consecutive_failures, consecutive_successes,
                datetime.now().isoformat()
            ))
            
    def _update_analytics(self):
        """Update analytics summary"""
        analytics = {
            "last_updated": datetime.now().isoformat(),
            "summary": self.generate_test_report(30),
            "flaky_tests_count": len(self.get_flaky_tests()),
            "total_test_runs": self._get_total_test_runs()
        }
        
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
            
    def _get_total_test_runs(self) -> int:
        """Get total number of test runs"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM test_results")
        count = cursor.fetchone()[0]
        conn.close()
        return count


def create_sample_test_results():
    """Create sample test results for demonstration"""
    tracker = TestResultTracker()
    
    # Sample test names
    test_names = [
        "test_document_upload",
        "test_pdf_parsing",
        "test_card_generation",
        "test_search_functionality",
        "test_user_authentication",
        "test_srs_algorithm",
        "test_database_connection",
        "test_api_endpoints",
        "test_frontend_rendering",
        "test_performance_benchmarks"
    ]
    
    # Generate sample results for the last 30 days
    for day in range(30):
        date = datetime.now() - timedelta(days=day)
        
        # Create suite result
        suite_id = str(uuid.uuid4())
        test_results = []
        
        for test_name in test_names:
            # Simulate some flakiness
            if test_name == "test_performance_benchmarks" and day % 7 == 0:
                status = TestStatus.FAILED
            elif test_name == "test_database_connection" and day % 10 == 0:
                status = TestStatus.ERROR
            else:
                status = TestStatus.PASSED if day % 20 != 0 else TestStatus.FAILED
                
            test_result = TestResult(
                id=str(uuid.uuid4()),
                test_name=test_name,
                test_category=TestCategory.UNIT,
                status=status,
                duration_ms=float(1000 + (day * 100) + hash(test_name) % 5000),
                timestamp=date.isoformat(),
                environment="test",
                commit_hash=f"abc123{day:02d}",
                branch="main",
                error_message="Sample error message" if status in [TestStatus.FAILED, TestStatus.ERROR] else None,
                stack_trace="Sample stack trace" if status in [TestStatus.FAILED, TestStatus.ERROR] else None,
                metadata={"sample": True, "day": day}
            )
            test_results.append(test_result)
            
        suite_result = TestSuiteResult(
            id=suite_id,
            suite_name="comprehensive_test_suite",
            timestamp=date.isoformat(),
            environment="test",
            commit_hash=f"abc123{day:02d}",
            branch="main",
            total_tests=len(test_results),
            passed_tests=len([r for r in test_results if r.status == TestStatus.PASSED]),
            failed_tests=len([r for r in test_results if r.status == TestStatus.FAILED]),
            skipped_tests=0,
            error_tests=len([r for r in test_results if r.status == TestStatus.ERROR]),
            total_duration_ms=sum(r.duration_ms for r in test_results),
            test_results=test_results,
            metadata={"sample_data": True}
        )
        
        tracker.record_test_suite_result(suite_result)
        
    print("Sample test results created!")


if __name__ == "__main__":
    create_sample_test_results()