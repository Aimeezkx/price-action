"""
Memory and resource limit testing.
Tests system behavior under memory constraints and resource limitations.
"""

import asyncio
import time
import psutil
import gc
import threading
import json
import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import resource
import os
import signal
from contextlib import contextmanager

@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: float
    memory_usage_mb: float
    memory_percent: float
    cpu_percent: float
    disk_usage_mb: float
    open_files: int
    thread_count: int
    process_memory_mb: float

@dataclass
class MemoryTestResult:
    """Result of a memory test"""
    test_name: str
    start_resources: ResourceSnapshot
    peak_resources: ResourceSnapshot
    end_resources: ResourceSnapshot
    success: bool
    error_message: str = ""
    memory_leaked: bool = False
    memory_leak_mb: float = 0.0
    duration: float = 0.0

class ResourceMonitor:
    """Monitor system and process resources"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.snapshots: List[ResourceSnapshot] = []
        self.monitor_thread: Optional[threading.Thread] = None
    
    def take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current resource usage"""
        try:
            # System resources
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk_usage = psutil.disk_usage('/').used / (1024 * 1024)  # MB
            
            # Process resources
            process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            open_files = len(self.process.open_files())
            thread_count = self.process.num_threads()
            
            return ResourceSnapshot(
                timestamp=time.time(),
                memory_usage_mb=memory_info.used / (1024 * 1024),
                memory_percent=memory_info.percent,
                cpu_percent=cpu_percent,
                disk_usage_mb=disk_usage,
                open_files=open_files,
                thread_count=thread_count,
                process_memory_mb=process_memory
            )
        except Exception as e:
            print(f"Error taking resource snapshot: {e}")
            return ResourceSnapshot(
                timestamp=time.time(),
                memory_usage_mb=0, memory_percent=0, cpu_percent=0,
                disk_usage_mb=0, open_files=0, thread_count=0, process_memory_mb=0
            )
    
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous resource monitoring"""
        self.monitoring = True
        self.snapshots = []
        
        def monitor_loop():
            while self.monitoring:
                snapshot = self.take_snapshot()
                self.snapshots.append(snapshot)
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def get_peak_usage(self) -> ResourceSnapshot:
        """Get peak resource usage from monitoring period"""
        if not self.snapshots:
            return self.take_snapshot()
        
        # Find peak memory usage
        peak_snapshot = max(self.snapshots, key=lambda s: s.process_memory_mb)
        return peak_snapshot
    
    def detect_memory_leak(self, start_snapshot: ResourceSnapshot, 
                          end_snapshot: ResourceSnapshot, 
                          threshold_mb: float = 10.0) -> tuple[bool, float]:
        """Detect if there's a memory leak"""
        memory_diff = end_snapshot.process_memory_mb - start_snapshot.process_memory_mb
        is_leak = memory_diff > threshold_mb
        return is_leak, memory_diff

class MemoryStressTester:
    """Test system behavior under memory stress"""
    
    def __init__(self):
        self.monitor = ResourceMonitor()
        self.test_data_dir = Path("backend/tests/test_data/memory_stress")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def memory_limit(self, limit_mb: int):
        """Context manager to set memory limit for the process"""
        # Convert MB to bytes
        limit_bytes = limit_mb * 1024 * 1024
        
        # Get current limit
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)
        
        try:
            # Set new limit
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard_limit))
            yield
        finally:
            # Restore original limit
            resource.setrlimit(resource.RLIMIT_AS, (soft_limit, hard_limit))
    
    def create_large_data_structure(self, size_mb: int) -> List[bytes]:
        """Create a large data structure in memory"""
        # Create chunks of 1MB each
        chunk_size = 1024 * 1024  # 1MB
        chunks = []
        
        for i in range(size_mb):
            chunk = b'A' * chunk_size
            chunks.append(chunk)
        
        return chunks
    
    def simulate_document_processing_load(self, num_documents: int = 100) -> List[Dict[str, Any]]:
        """Simulate processing many documents simultaneously"""
        documents = []
        
        for i in range(num_documents):
            # Simulate document content (varying sizes)
            content_size = random.randint(10000, 500000)  # 10KB to 500KB
            document = {
                'id': f'doc_{i}',
                'title': f'Document {i}',
                'content': 'A' * content_size,
                'metadata': {
                    'page_count': random.randint(1, 100),
                    'word_count': content_size // 5,
                    'images': ['img_' + str(j) for j in range(random.randint(0, 10))]
                },
                'processed_data': {
                    'chapters': [f'Chapter {j}' for j in range(random.randint(1, 20))],
                    'knowledge_points': [f'KP {j}: ' + 'B' * 1000 for j in range(random.randint(10, 100))],
                    'cards': [f'Card {j}: ' + 'C' * 500 for j in range(random.randint(5, 50))]
                }
            }
            documents.append(document)
        
        return documents
    
    async def test_memory_growth(self, growth_iterations: int = 10, 
                                growth_size_mb: int = 50) -> MemoryTestResult:
        """Test gradual memory growth"""
        test_name = f"memory_growth_{growth_iterations}x{growth_size_mb}MB"
        
        # Start monitoring
        self.monitor.start_monitoring(interval=0.5)
        start_snapshot = self.monitor.take_snapshot()
        start_time = time.time()
        
        try:
            data_structures = []
            
            for i in range(growth_iterations):
                print(f"Memory growth iteration {i+1}/{growth_iterations}")
                
                # Allocate memory
                data = self.create_large_data_structure(growth_size_mb)
                data_structures.append(data)
                
                # Force garbage collection
                gc.collect()
                
                # Brief pause
                await asyncio.sleep(0.5)
                
                # Check current memory usage
                current_snapshot = self.monitor.take_snapshot()
                print(f"Current memory usage: {current_snapshot.process_memory_mb:.1f} MB")
                
                # Check if we're approaching system limits
                if current_snapshot.memory_percent > 90:
                    print("Approaching system memory limit, stopping test")
                    break
            
            # Hold memory for a moment
            await asyncio.sleep(2)
            
            # Clean up
            del data_structures
            gc.collect()
            
            # Wait for cleanup
            await asyncio.sleep(2)
            
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            # Check for memory leak
            is_leak, leak_amount = self.monitor.detect_memory_leak(start_snapshot, end_snapshot)
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=True,
                memory_leaked=is_leak,
                memory_leak_mb=leak_amount,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=False,
                error_message=str(e),
                duration=time.time() - start_time
            )
        finally:
            self.monitor.stop_monitoring()
    
    async def test_memory_limit_behavior(self, limit_mb: int = 512) -> MemoryTestResult:
        """Test behavior when approaching memory limits"""
        test_name = f"memory_limit_{limit_mb}MB"
        
        self.monitor.start_monitoring(interval=0.5)
        start_snapshot = self.monitor.take_snapshot()
        start_time = time.time()
        
        try:
            with self.memory_limit(limit_mb):
                # Try to allocate memory approaching the limit
                target_allocation = int(limit_mb * 0.8)  # 80% of limit
                
                print(f"Attempting to allocate {target_allocation} MB with {limit_mb} MB limit")
                
                data = self.create_large_data_structure(target_allocation)
                
                # Try to process data (simulate real workload)
                processed_count = 0
                for chunk in data:
                    # Simulate processing
                    processed_chunk = chunk[:1000] + b'PROCESSED'
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        await asyncio.sleep(0.1)  # Yield control
                
                print(f"Successfully processed {processed_count} chunks")
                
                # Clean up
                del data
                gc.collect()
            
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=True,
                duration=time.time() - start_time
            )
            
        except MemoryError as e:
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=False,
                error_message=f"MemoryError: {str(e)}",
                duration=time.time() - start_time
            )
        except Exception as e:
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=False,
                error_message=str(e),
                duration=time.time() - start_time
            )
        finally:
            self.monitor.stop_monitoring()
    
    async def test_concurrent_memory_usage(self, num_workers: int = 5, 
                                         allocation_per_worker_mb: int = 100) -> MemoryTestResult:
        """Test concurrent memory allocation by multiple workers"""
        test_name = f"concurrent_memory_{num_workers}workers_{allocation_per_worker_mb}MB"
        
        self.monitor.start_monitoring(interval=0.5)
        start_snapshot = self.monitor.take_snapshot()
        start_time = time.time()
        
        async def worker(worker_id: int):
            """Worker function that allocates and processes memory"""
            try:
                print(f"Worker {worker_id} starting allocation of {allocation_per_worker_mb} MB")
                
                # Allocate memory
                data = self.create_large_data_structure(allocation_per_worker_mb)
                
                # Simulate processing
                for i, chunk in enumerate(data):
                    if i % 10 == 0:
                        await asyncio.sleep(0.1)  # Yield control
                
                # Hold memory for a bit
                await asyncio.sleep(2)
                
                # Clean up
                del data
                gc.collect()
                
                print(f"Worker {worker_id} completed successfully")
                return True
                
            except Exception as e:
                print(f"Worker {worker_id} failed: {e}")
                return False
        
        try:
            # Start all workers concurrently
            tasks = [worker(i) for i in range(num_workers)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful workers
            successful_workers = sum(1 for r in results if r is True)
            
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=successful_workers >= num_workers * 0.8,  # 80% success rate
                error_message=f"Only {successful_workers}/{num_workers} workers succeeded",
                duration=time.time() - start_time
            )
            
        except Exception as e:
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=False,
                error_message=str(e),
                duration=time.time() - start_time
            )
        finally:
            self.monitor.stop_monitoring()
    
    async def test_document_processing_memory(self, num_documents: int = 200) -> MemoryTestResult:
        """Test memory usage during intensive document processing simulation"""
        test_name = f"document_processing_memory_{num_documents}docs"
        
        self.monitor.start_monitoring(interval=0.5)
        start_snapshot = self.monitor.take_snapshot()
        start_time = time.time()
        
        try:
            print(f"Simulating processing of {num_documents} documents")
            
            # Simulate document processing in batches
            batch_size = 20
            processed_documents = []
            
            for batch_start in range(0, num_documents, batch_size):
                batch_end = min(batch_start + batch_size, num_documents)
                batch_docs = batch_end - batch_start
                
                print(f"Processing batch {batch_start//batch_size + 1}: documents {batch_start}-{batch_end}")
                
                # Create batch of documents
                batch = self.simulate_document_processing_load(batch_docs)
                
                # Process each document in the batch
                for doc in batch:
                    # Simulate NLP processing (create additional data)
                    doc['nlp_results'] = {
                        'entities': [f'Entity_{i}' for i in range(random.randint(10, 50))],
                        'embeddings': [random.random() for _ in range(768)],  # Typical embedding size
                        'tokens': doc['content'].split() * 2  # Simulate token processing
                    }
                    
                    processed_documents.append(doc)
                
                # Simulate periodic cleanup
                if len(processed_documents) > 100:
                    # Keep only recent documents
                    processed_documents = processed_documents[-50:]
                    gc.collect()
                
                await asyncio.sleep(0.1)  # Brief pause between batches
            
            # Final cleanup
            del processed_documents
            gc.collect()
            
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            # Check for memory leak
            is_leak, leak_amount = self.monitor.detect_memory_leak(start_snapshot, end_snapshot)
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=True,
                memory_leaked=is_leak,
                memory_leak_mb=leak_amount,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            end_snapshot = self.monitor.take_snapshot()
            peak_snapshot = self.monitor.get_peak_usage()
            
            return MemoryTestResult(
                test_name=test_name,
                start_resources=start_snapshot,
                peak_resources=peak_snapshot,
                end_resources=end_snapshot,
                success=False,
                error_message=str(e),
                duration=time.time() - start_time
            )
        finally:
            self.monitor.stop_monitoring()
    
    def analyze_memory_test_results(self, results: List[MemoryTestResult]) -> Dict[str, Any]:
        """Analyze memory test results"""
        successful_tests = [r for r in results if r.success]
        failed_tests = [r for r in results if not r.success]
        leaked_tests = [r for r in results if r.memory_leaked]
        
        if not results:
            return {"error": "No results to analyze"}
        
        # Calculate statistics
        peak_memory_usage = [r.peak_resources.process_memory_mb for r in results]
        memory_growth = [r.peak_resources.process_memory_mb - r.start_resources.process_memory_mb for r in results]
        
        analysis = {
            "summary": {
                "total_tests": len(results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "tests_with_leaks": len(leaked_tests),
                "success_rate": len(successful_tests) / len(results) * 100,
                "leak_rate": len(leaked_tests) / len(results) * 100
            },
            "memory_statistics": {
                "peak_memory_usage_mb": {
                    "min": min(peak_memory_usage) if peak_memory_usage else 0,
                    "max": max(peak_memory_usage) if peak_memory_usage else 0,
                    "avg": sum(peak_memory_usage) / len(peak_memory_usage) if peak_memory_usage else 0
                },
                "memory_growth_mb": {
                    "min": min(memory_growth) if memory_growth else 0,
                    "max": max(memory_growth) if memory_growth else 0,
                    "avg": sum(memory_growth) / len(memory_growth) if memory_growth else 0
                }
            },
            "test_details": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "peak_memory_mb": r.peak_resources.process_memory_mb,
                    "memory_growth_mb": r.peak_resources.process_memory_mb - r.start_resources.process_memory_mb,
                    "memory_leaked": r.memory_leaked,
                    "memory_leak_mb": r.memory_leak_mb,
                    "error": r.error_message if not r.success else None
                }
                for r in results
            ],
            "errors": [r.error_message for r in failed_tests if r.error_message]
        }
        
        return analysis

@pytest.mark.asyncio
@pytest.mark.load
class TestMemoryResourceLimits:
    """Test suite for memory and resource limit testing"""
    
    @pytest.fixture
    def memory_tester(self):
        return MemoryStressTester()
    
    async def test_gradual_memory_growth(self, memory_tester):
        """Test gradual memory growth and cleanup"""
        result = await memory_tester.test_memory_growth(
            growth_iterations=5, 
            growth_size_mb=20
        )
        
        # Assertions
        assert result.success, f"Memory growth test failed: {result.error_message}"
        assert not result.memory_leaked, f"Memory leak detected: {result.memory_leak_mb} MB"
        assert result.peak_resources.process_memory_mb < 500, \
            f"Peak memory usage too high: {result.peak_resources.process_memory_mb} MB"
        
        print(f"Memory growth test completed: Peak {result.peak_resources.process_memory_mb:.1f} MB")
    
    async def test_memory_limit_handling(self, memory_tester):
        """Test behavior under memory constraints"""
        # Test with a reasonable limit
        result = await memory_tester.test_memory_limit_behavior(limit_mb=256)
        
        # The test should either succeed or fail gracefully
        if not result.success:
            # If it failed, it should be due to memory constraints, not crashes
            assert "MemoryError" in result.error_message or "memory" in result.error_message.lower(), \
                f"Unexpected error type: {result.error_message}"
        
        print(f"Memory limit test: {'Passed' if result.success else 'Failed gracefully'}")
    
    async def test_concurrent_memory_allocation(self, memory_tester):
        """Test concurrent memory allocation"""
        result = await memory_tester.test_concurrent_memory_usage(
            num_workers=3, 
            allocation_per_worker_mb=50
        )
        
        # Assertions
        assert result.success, f"Concurrent memory test failed: {result.error_message}"
        
        print(f"Concurrent memory test completed: Peak {result.peak_resources.process_memory_mb:.1f} MB")
    
    async def test_document_processing_memory_usage(self, memory_tester):
        """Test memory usage during document processing simulation"""
        result = await memory_tester.test_document_processing_memory(num_documents=100)
        
        # Assertions
        assert result.success, f"Document processing memory test failed: {result.error_message}"
        assert not result.memory_leaked, f"Memory leak in document processing: {result.memory_leak_mb} MB"
        
        print(f"Document processing memory test: Peak {result.peak_resources.process_memory_mb:.1f} MB")
    
    async def test_comprehensive_memory_analysis(self, memory_tester):
        """Run comprehensive memory tests and analyze results"""
        results = []
        
        # Run multiple memory tests
        test_configs = [
            ("small_growth", lambda: memory_tester.test_memory_growth(3, 10)),
            ("medium_growth", lambda: memory_tester.test_memory_growth(5, 20)),
            ("concurrent_small", lambda: memory_tester.test_concurrent_memory_usage(2, 25)),
            ("document_processing", lambda: memory_tester.test_document_processing_memory(50))
        ]
        
        for test_name, test_func in test_configs:
            try:
                result = await test_func()
                results.append(result)
            except Exception as e:
                print(f"Test {test_name} failed with exception: {e}")
        
        # Analyze all results
        analysis = memory_tester.analyze_memory_test_results(results)
        
        # Assertions
        assert analysis["summary"]["success_rate"] >= 75, \
            f"Overall success rate too low: {analysis['summary']['success_rate']}%"
        assert analysis["summary"]["leak_rate"] <= 25, \
            f"Too many tests with memory leaks: {analysis['summary']['leak_rate']}%"
        
        print(f"Comprehensive memory analysis: {json.dumps(analysis, indent=2)}")

if __name__ == "__main__":
    # Run standalone test
    async def main():
        tester = MemoryStressTester()
        
        # Run a few tests
        results = []
        
        print("Running memory growth test...")
        result1 = await tester.test_memory_growth(3, 20)
        results.append(result1)
        
        print("Running concurrent memory test...")
        result2 = await tester.test_concurrent_memory_usage(2, 30)
        results.append(result2)
        
        print("Running document processing test...")
        result3 = await tester.test_document_processing_memory(50)
        results.append(result3)
        
        # Analyze results
        analysis = tester.analyze_memory_test_results(results)
        print(json.dumps(analysis, indent=2))
    
    import random
    asyncio.run(main())