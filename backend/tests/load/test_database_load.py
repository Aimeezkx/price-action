"""
Database performance tests under load.
Tests database performance with concurrent operations and high data volumes.
"""

import asyncio
import time
import random
import json
import pytest
import psutil
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import threading

from app.core.database import engine
from app.models.document import Document
from app.models.knowledge import Knowledge
from app.models.learning import Card

@dataclass
class DatabaseOperation:
    """Database operation result"""
    operation_type: str
    start_time: float
    duration: float
    success: bool
    error_message: str = ""
    rows_affected: int = 0
    connection_time: float = 0.0

class DatabaseLoadTester:
    """Test database performance under various load conditions"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.results: List[DatabaseOperation] = []
        self.test_data_ids = {
            'documents': [],
            'knowledge_points': [],
            'cards': []
        }
    
    def create_test_session(self):
        """Create a database session for testing"""
        return self.SessionLocal()
    
    async def setup_test_data(self, num_documents: int = 100, 
                            num_knowledge_points: int = 1000,
                            num_cards: int = 2000) -> None:
        """Set up test data for load testing"""
        print(f"Setting up test data: {num_documents} docs, {num_knowledge_points} knowledge points, {num_cards} cards")
        
        with self.create_test_session() as session:
            try:
                # Create test documents
                documents = []
                for i in range(num_documents):
                    doc = Document(
                        title=f"Test Document {i}",
                        filename=f"test_doc_{i}.pdf",
                        file_path=f"/test/path/test_doc_{i}.pdf",
                        file_size=random.randint(100000, 5000000),
                        status="completed",
                        content_text=f"This is test content for document {i}. " * 100
                    )
                    documents.append(doc)
                    
                session.add_all(documents)
                session.commit()
                
                # Store document IDs
                self.test_data_ids['documents'] = [doc.id for doc in documents]
                
                # Create test knowledge points
                knowledge_points = []
                for i in range(num_knowledge_points):
                    doc_id = random.choice(self.test_data_ids['documents'])
                    kp = Knowledge(
                        chapter_id=doc_id,  # Using doc_id as chapter_id for simplicity
                        kind="concept",
                        text=f"Knowledge point {i}: This is important information about topic {i % 50}.",
                        confidence_score=random.uniform(0.1, 1.0),
                        entities=[f"entity_{i % 10}"],
                        anchors={"page": random.randint(1, 100), "chapter": i % 20}
                    )
                    knowledge_points.append(kp)
                
                session.add_all(knowledge_points)
                session.commit()
                
                # Store knowledge point IDs
                self.test_data_ids['knowledge_points'] = [kp.id for kp in knowledge_points]
                
                # Create test cards
                cards = []
                for i in range(num_cards):
                    kp_id = random.choice(self.test_data_ids['knowledge_points'])
                    card = Card(
                        knowledge_id=kp_id,
                        front=f"Question {i}: What is the main concept?",
                        back=f"Answer {i}: The main concept is about topic {i % 100}.",
                        card_type="qa",
                        difficulty=random.uniform(0.1, 1.0)
                    )
                    cards.append(card)
                
                session.add_all(cards)
                session.commit()
                
                # Store card IDs
                self.test_data_ids['cards'] = [card.id for card in cards]
                
                print("Test data setup completed successfully")
                
            except Exception as e:
                session.rollback()
                print(f"Error setting up test data: {e}")
                raise
    
    def cleanup_test_data(self) -> None:
        """Clean up test data after testing"""
        print("Cleaning up test data...")
        
        with self.create_test_session() as session:
            try:
                # Delete in reverse order of dependencies
                if self.test_data_ids['cards']:
                    session.query(Card).filter(Card.id.in_(self.test_data_ids['cards'])).delete(synchronize_session=False)
                
                if self.test_data_ids['knowledge_points']:
                    session.query(Knowledge).filter(Knowledge.id.in_(self.test_data_ids['knowledge_points'])).delete(synchronize_session=False)
                
                if self.test_data_ids['documents']:
                    session.query(Document).filter(Document.id.in_(self.test_data_ids['documents'])).delete(synchronize_session=False)
                
                session.commit()
                print("Test data cleanup completed")
                
            except Exception as e:
                session.rollback()
                print(f"Error cleaning up test data: {e}")
    
    def execute_read_operation(self, operation_type: str) -> DatabaseOperation:
        """Execute a read operation and measure performance"""
        start_time = time.time()
        connection_start = time.time()
        
        try:
            with self.create_test_session() as session:
                connection_time = time.time() - connection_start
                
                if operation_type == "simple_select":
                    # Simple document selection
                    result = session.query(Document).limit(10).all()
                    rows_affected = len(result)
                    
                elif operation_type == "complex_join":
                    # Complex join query
                    result = session.query(Document, Knowledge, Card)\
                        .join(Knowledge, Document.id == Knowledge.chapter_id)\
                        .join(Card, Knowledge.id == Card.knowledge_id)\
                        .limit(50).all()
                    rows_affected = len(result)
                    
                elif operation_type == "aggregation":
                    # Aggregation query
                    result = session.query(
                        Document.id,
                        sa.func.count(Knowledge.id).label('kp_count'),
                        sa.func.avg(Knowledge.confidence_score).label('avg_confidence')
                    ).join(Knowledge, Document.id == Knowledge.chapter_id)\
                     .group_by(Document.id)\
                     .limit(20).all()
                    rows_affected = len(result)
                    
                elif operation_type == "full_text_search":
                    # Simulate full-text search
                    search_term = f"topic {random.randint(1, 50)}"
                    result = session.query(Knowledge)\
                        .filter(Knowledge.text.contains(search_term))\
                        .limit(100).all()
                    rows_affected = len(result)
                    
                elif operation_type == "large_result_set":
                    # Query returning large result set
                    result = session.query(Card).limit(1000).all()
                    rows_affected = len(result)
                    
                else:
                    raise ValueError(f"Unknown operation type: {operation_type}")
                
                duration = time.time() - start_time
                
                return DatabaseOperation(
                    operation_type=operation_type,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    rows_affected=rows_affected,
                    connection_time=connection_time
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return DatabaseOperation(
                operation_type=operation_type,
                start_time=start_time,
                duration=duration,
                success=False,
                error_message=str(e),
                connection_time=connection_time
            )
    
    def execute_write_operation(self, operation_type: str) -> DatabaseOperation:
        """Execute a write operation and measure performance"""
        start_time = time.time()
        connection_start = time.time()
        
        try:
            with self.create_test_session() as session:
                connection_time = time.time() - connection_start
                rows_affected = 0
                
                if operation_type == "single_insert":
                    # Single document insert
                    doc = Document(
                        title=f"Load Test Doc {random.randint(1, 10000)}",
                        filename=f"load_test_{random.randint(1, 10000)}.pdf",
                        file_path=f"/load/test/path_{random.randint(1, 10000)}.pdf",
                        file_size=random.randint(100000, 1000000),
                        status="processing"
                    )
                    session.add(doc)
                    session.commit()
                    rows_affected = 1
                    
                elif operation_type == "batch_insert":
                    # Batch insert of knowledge points
                    doc_id = random.choice(self.test_data_ids['documents'])
                    knowledge_points = []
                    for i in range(10):
                        kp = Knowledge(
                            chapter_id=doc_id,
                            kind="concept",
                            text=f"Batch KP {i}: Load test content {random.randint(1, 1000)}",
                            confidence_score=random.uniform(0.1, 1.0),
                            entities=[f"entity_{random.randint(1, 10)}"],
                            anchors={"page": random.randint(1, 100), "chapter": random.randint(1, 10)}
                        )
                        knowledge_points.append(kp)
                    
                    session.add_all(knowledge_points)
                    session.commit()
                    rows_affected = len(knowledge_points)
                    
                elif operation_type == "update_operation":
                    # Update random documents
                    doc_ids = random.sample(self.test_data_ids['documents'], min(10, len(self.test_data_ids['documents'])))
                    result = session.query(Document)\
                        .filter(Document.id.in_(doc_ids))\
                        .update({"status": "updated"}, synchronize_session=False)
                    session.commit()
                    rows_affected = result
                    
                elif operation_type == "delete_operation":
                    # Delete some test knowledge points (if any exist)
                    if self.test_data_ids['knowledge_points']:
                        kp_ids = random.sample(
                            self.test_data_ids['knowledge_points'], 
                            min(5, len(self.test_data_ids['knowledge_points']))
                        )
                        result = session.query(Knowledge)\
                            .filter(Knowledge.id.in_(kp_ids))\
                            .delete(synchronize_session=False)
                        session.commit()
                        rows_affected = result
                        
                        # Remove from tracking
                        for kp_id in kp_ids:
                            if kp_id in self.test_data_ids['knowledge_points']:
                                self.test_data_ids['knowledge_points'].remove(kp_id)
                    
                else:
                    raise ValueError(f"Unknown operation type: {operation_type}")
                
                duration = time.time() - start_time
                
                return DatabaseOperation(
                    operation_type=operation_type,
                    start_time=start_time,
                    duration=duration,
                    success=True,
                    rows_affected=rows_affected,
                    connection_time=connection_time
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return DatabaseOperation(
                operation_type=operation_type,
                start_time=start_time,
                duration=duration,
                success=False,
                error_message=str(e),
                connection_time=connection_time
            )
    
    async def run_concurrent_operations(self, num_threads: int = 10, 
                                      operations_per_thread: int = 50,
                                      read_write_ratio: float = 0.8) -> List[DatabaseOperation]:
        """Run concurrent database operations"""
        print(f"Running concurrent operations: {num_threads} threads, {operations_per_thread} ops/thread")
        
        read_operations = ["simple_select", "complex_join", "aggregation", "full_text_search", "large_result_set"]
        write_operations = ["single_insert", "batch_insert", "update_operation", "delete_operation"]
        
        def worker_thread():
            """Worker thread function"""
            thread_results = []
            
            for _ in range(operations_per_thread):
                # Choose operation type based on read/write ratio
                if random.random() < read_write_ratio:
                    operation_type = random.choice(read_operations)
                    result = self.execute_read_operation(operation_type)
                else:
                    operation_type = random.choice(write_operations)
                    result = self.execute_write_operation(operation_type)
                
                thread_results.append(result)
                
                # Small delay between operations
                time.sleep(random.uniform(0.01, 0.1))
            
            return thread_results
        
        # Execute threads concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread) for _ in range(num_threads)]
            
            all_results = []
            for future in futures:
                try:
                    thread_results = future.result(timeout=300)  # 5 minute timeout
                    all_results.extend(thread_results)
                except Exception as e:
                    print(f"Thread execution error: {e}")
        
        return all_results
    
    def analyze_performance_results(self, results: List[DatabaseOperation]) -> Dict[str, Any]:
        """Analyze database performance results"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Group by operation type
        operation_stats = {}
        for result in successful_results:
            op_type = result.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_connection_time": 0,
                    "total_rows": 0,
                    "durations": [],
                    "connection_times": []
                }
            
            stats = operation_stats[op_type]
            stats["count"] += 1
            stats["total_duration"] += result.duration
            stats["total_connection_time"] += result.connection_time
            stats["total_rows"] += result.rows_affected
            stats["durations"].append(result.duration)
            stats["connection_times"].append(result.connection_time)
        
        # Calculate statistics for each operation type
        for op_type, stats in operation_stats.items():
            durations = stats["durations"]
            connection_times = stats["connection_times"]
            
            stats.update({
                "avg_duration": stats["total_duration"] / stats["count"],
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_connection_time": stats["total_connection_time"] / stats["count"],
                "avg_rows_per_operation": stats["total_rows"] / stats["count"],
                "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                "p99_duration": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
            })
            
            # Remove raw data to reduce output size
            del stats["durations"]
            del stats["connection_times"]
        
        # Overall statistics
        all_durations = [r.duration for r in successful_results]
        all_connection_times = [r.connection_time for r in successful_results]
        
        analysis = {
            "summary": {
                "total_operations": len(results),
                "successful_operations": len(successful_results),
                "failed_operations": len(failed_results),
                "success_rate": len(successful_results) / len(results) * 100,
                "total_duration": sum(all_durations),
                "avg_operation_duration": sum(all_durations) / len(all_durations) if all_durations else 0,
                "avg_connection_time": sum(all_connection_times) / len(all_connection_times) if all_connection_times else 0,
                "operations_per_second": len(successful_results) / sum(all_durations) if sum(all_durations) > 0 else 0
            },
            "operation_statistics": operation_stats,
            "errors": [r.error_message for r in failed_results if r.error_message]
        }
        
        return analysis

@pytest.mark.asyncio
@pytest.mark.load
class TestDatabaseLoad:
    """Test suite for database load testing"""
    
    @pytest.fixture
    async def db_tester(self):
        tester = DatabaseLoadTester()
        await tester.setup_test_data(num_documents=50, num_knowledge_points=500, num_cards=1000)
        yield tester
        tester.cleanup_test_data()
    
    async def test_low_concurrency_load(self, db_tester):
        """Test database with low concurrency (5 threads)"""
        results = await db_tester.run_concurrent_operations(
            num_threads=5, 
            operations_per_thread=20,
            read_write_ratio=0.8
        )
        
        analysis = db_tester.analyze_performance_results(results)
        
        # Assertions
        assert analysis["summary"]["success_rate"] >= 95, \
            f"Success rate too low: {analysis['summary']['success_rate']}%"
        assert analysis["summary"]["avg_operation_duration"] <= 1.0, \
            f"Average operation duration too high: {analysis['summary']['avg_operation_duration']}s"
        
        print(f"Low concurrency database test results: {json.dumps(analysis, indent=2)}")
    
    async def test_medium_concurrency_load(self, db_tester):
        """Test database with medium concurrency (15 threads)"""
        results = await db_tester.run_concurrent_operations(
            num_threads=15, 
            operations_per_thread=30,
            read_write_ratio=0.7
        )
        
        analysis = db_tester.analyze_performance_results(results)
        
        # Assertions
        assert analysis["summary"]["success_rate"] >= 90, \
            f"Success rate too low: {analysis['summary']['success_rate']}%"
        assert analysis["summary"]["avg_operation_duration"] <= 2.0, \
            f"Average operation duration too high: {analysis['summary']['avg_operation_duration']}s"
        
        print(f"Medium concurrency database test results: {json.dumps(analysis, indent=2)}")
    
    async def test_high_concurrency_load(self, db_tester):
        """Test database with high concurrency (25 threads)"""
        results = await db_tester.run_concurrent_operations(
            num_threads=25, 
            operations_per_thread=20,
            read_write_ratio=0.6
        )
        
        analysis = db_tester.analyze_performance_results(results)
        
        # Assertions - More lenient for high concurrency
        assert analysis["summary"]["success_rate"] >= 85, \
            f"Success rate too low: {analysis['summary']['success_rate']}%"
        assert analysis["summary"]["avg_operation_duration"] <= 3.0, \
            f"Average operation duration too high: {analysis['summary']['avg_operation_duration']}s"
        
        print(f"High concurrency database test results: {json.dumps(analysis, indent=2)}")
    
    async def test_write_heavy_load(self, db_tester):
        """Test database with write-heavy workload"""
        results = await db_tester.run_concurrent_operations(
            num_threads=10, 
            operations_per_thread=25,
            read_write_ratio=0.3  # 70% writes
        )
        
        analysis = db_tester.analyze_performance_results(results)
        
        # Assertions
        assert analysis["summary"]["success_rate"] >= 80, \
            f"Success rate too low for write-heavy load: {analysis['summary']['success_rate']}%"
        
        print(f"Write-heavy database test results: {json.dumps(analysis, indent=2)}")
    
    async def test_connection_pool_stress(self, db_tester):
        """Test database connection pool under stress"""
        # Test with more threads than typical connection pool size
        results = await db_tester.run_concurrent_operations(
            num_threads=50, 
            operations_per_thread=10,
            read_write_ratio=0.9
        )
        
        analysis = db_tester.analyze_performance_results(results)
        
        # Check connection times don't get too high
        avg_connection_time = analysis["summary"]["avg_connection_time"]
        assert avg_connection_time <= 0.5, \
            f"Average connection time too high: {avg_connection_time}s"
        
        print(f"Connection pool stress test results: {json.dumps(analysis, indent=2)}")

if __name__ == "__main__":
    # Run standalone test
    async def main():
        tester = DatabaseLoadTester()
        try:
            await tester.setup_test_data(num_documents=20, num_knowledge_points=200, num_cards=400)
            results = await tester.run_concurrent_operations(num_threads=10, operations_per_thread=20)
            analysis = tester.analyze_performance_results(results)
            print(json.dumps(analysis, indent=2))
        finally:
            tester.cleanup_test_data()
    
    asyncio.run(main())