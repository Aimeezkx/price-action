"""
Concurrent document processing load tests.
Tests the system's ability to handle multiple document processing requests simultaneously.
"""

import asyncio
import time
import pytest
import aiohttp
import json
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import threading
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """Result of a document processing operation"""
    document_id: str
    processing_time: float
    success: bool
    error_message: str = ""
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class ConcurrentDocumentProcessor:
    """Test concurrent document processing capabilities"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_documents = self._prepare_test_documents()
        self.results: List[ProcessingResult] = []
        
    def _prepare_test_documents(self) -> List[Path]:
        """Prepare test documents of various sizes"""
        test_docs_dir = Path("backend/tests/test_data/load_test_docs")
        test_docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test documents if they don't exist
        documents = []
        for size in ["small", "medium", "large"]:
            doc_path = test_docs_dir / f"{size}_test.pdf"
            if not doc_path.exists():
                self._create_test_document(doc_path, size)
            documents.append(doc_path)
            
        return documents
        
    def _create_test_document(self, path: Path, size: str):
        """Create a test PDF document of specified size"""
        # This would create actual test PDFs - simplified for now
        content_sizes = {
            "small": "A" * 1000,    # ~1KB
            "medium": "B" * 50000,  # ~50KB  
            "large": "C" * 500000   # ~500KB
        }
        
        with open(path, 'w') as f:
            f.write(content_sizes[size])
    
    async def upload_document(self, session: aiohttp.ClientSession, 
                            document_path: Path) -> ProcessingResult:
        """Upload a single document and measure processing time"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        try:
            with open(document_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=document_path.name)
                
                async with session.post(f"{self.base_url}/api/documents/upload", 
                                      data=data) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        document_id = result_data.get('document_id')
                        
                        # Wait for processing to complete
                        await self._wait_for_processing(session, document_id)
                        
                        processing_time = time.time() - start_time
                        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        end_cpu = psutil.cpu_percent()
                        
                        return ProcessingResult(
                            document_id=document_id,
                            processing_time=processing_time,
                            success=True,
                            memory_usage=end_memory - start_memory,
                            cpu_usage=end_cpu - start_cpu
                        )
                    else:
                        error_text = await response.text()
                        return ProcessingResult(
                            document_id="",
                            processing_time=time.time() - start_time,
                            success=False,
                            error_message=f"HTTP {response.status}: {error_text}"
                        )
                        
        except Exception as e:
            return ProcessingResult(
                document_id="",
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def _wait_for_processing(self, session: aiohttp.ClientSession, 
                                 document_id: str, timeout: int = 120):
        """Wait for document processing to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with session.get(f"{self.base_url}/api/documents/{document_id}/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    if status_data.get('status') == 'completed':
                        return
                    elif status_data.get('status') == 'failed':
                        raise Exception(f"Document processing failed: {status_data.get('error')}")
                        
            await asyncio.sleep(2)
            
        raise Exception(f"Document processing timeout after {timeout} seconds")
    
    async def run_concurrent_test(self, concurrent_uploads: int = 10, 
                                iterations: int = 3) -> Dict[str, Any]:
        """Run concurrent document processing test"""
        print(f"Starting concurrent processing test: {concurrent_uploads} concurrent uploads, {iterations} iterations")
        
        all_results = []
        
        async with aiohttp.ClientSession() as session:
            for iteration in range(iterations):
                print(f"Running iteration {iteration + 1}/{iterations}")
                
                # Create tasks for concurrent uploads
                tasks = []
                for i in range(concurrent_uploads):
                    document = self.test_documents[i % len(self.test_documents)]
                    task = self.upload_document(session, document)
                    tasks.append(task)
                
                # Execute all tasks concurrently
                iteration_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in iteration_results:
                    if isinstance(result, ProcessingResult):
                        all_results.append(result)
                    else:
                        # Handle exceptions
                        all_results.append(ProcessingResult(
                            document_id="",
                            processing_time=0,
                            success=False,
                            error_message=str(result)
                        ))
                
                # Brief pause between iterations
                await asyncio.sleep(5)
        
        return self._analyze_results(all_results)
    
    def _analyze_results(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """Analyze test results and generate report"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if successful_results:
            processing_times = [r.processing_time for r in successful_results]
            memory_usage = [r.memory_usage for r in successful_results]
            cpu_usage = [r.cpu_usage for r in successful_results]
            
            analysis = {
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": len(successful_results) / len(results) * 100,
                "processing_times": {
                    "min": min(processing_times),
                    "max": max(processing_times),
                    "avg": sum(processing_times) / len(processing_times),
                    "median": sorted(processing_times)[len(processing_times) // 2]
                },
                "resource_usage": {
                    "avg_memory_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                    "avg_cpu_percent": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
                },
                "errors": [r.error_message for r in failed_results]
            }
        else:
            analysis = {
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_results),
                "success_rate": 0,
                "errors": [r.error_message for r in failed_results]
            }
        
        return analysis

@pytest.mark.asyncio
@pytest.mark.load
class TestConcurrentDocumentProcessing:
    """Test suite for concurrent document processing"""
    
    @pytest.fixture
    def processor(self):
        return ConcurrentDocumentProcessor()
    
    async def test_low_concurrency(self, processor):
        """Test with low concurrency (5 concurrent uploads)"""
        results = await processor.run_concurrent_test(concurrent_uploads=5, iterations=2)
        
        # Assertions
        assert results["success_rate"] >= 90, f"Success rate too low: {results['success_rate']}%"
        assert results["processing_times"]["avg"] <= 60, f"Average processing time too high: {results['processing_times']['avg']}s"
        
        print(f"Low concurrency test results: {json.dumps(results, indent=2)}")
    
    async def test_medium_concurrency(self, processor):
        """Test with medium concurrency (15 concurrent uploads)"""
        results = await processor.run_concurrent_test(concurrent_uploads=15, iterations=2)
        
        # Assertions
        assert results["success_rate"] >= 80, f"Success rate too low: {results['success_rate']}%"
        assert results["processing_times"]["avg"] <= 90, f"Average processing time too high: {results['processing_times']['avg']}s"
        
        print(f"Medium concurrency test results: {json.dumps(results, indent=2)}")
    
    async def test_high_concurrency(self, processor):
        """Test with high concurrency (25 concurrent uploads)"""
        results = await processor.run_concurrent_test(concurrent_uploads=25, iterations=1)
        
        # Assertions - More lenient for high concurrency
        assert results["success_rate"] >= 70, f"Success rate too low: {results['success_rate']}%"
        assert results["processing_times"]["avg"] <= 120, f"Average processing time too high: {results['processing_times']['avg']}s"
        
        print(f"High concurrency test results: {json.dumps(results, indent=2)}")
    
    async def test_resource_limits(self, processor):
        """Test system behavior under resource constraints"""
        # Monitor system resources during test
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent(interval=1)
        
        results = await processor.run_concurrent_test(concurrent_uploads=20, iterations=1)
        
        final_memory = psutil.virtual_memory().percent
        final_cpu = psutil.cpu_percent(interval=1)
        
        # Check resource usage didn't spike too high
        memory_increase = final_memory - initial_memory
        cpu_increase = final_cpu - initial_cpu
        
        assert memory_increase <= 30, f"Memory usage increased too much: {memory_increase}%"
        assert cpu_increase <= 50, f"CPU usage increased too much: {cpu_increase}%"
        
        print(f"Resource usage - Memory: +{memory_increase}%, CPU: +{cpu_increase}%")
        print(f"Resource limits test results: {json.dumps(results, indent=2)}")

if __name__ == "__main__":
    # Run standalone test
    async def main():
        processor = ConcurrentDocumentProcessor()
        results = await processor.run_concurrent_test(concurrent_uploads=10, iterations=2)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())