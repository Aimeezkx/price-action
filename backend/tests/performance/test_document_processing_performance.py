"""Document processing performance benchmarks."""

import pytest
import asyncio
import time
import os
from pathlib import Path
from typing import Dict, List

from app.parsers.factory import ParserFactory
from app.services.document_service import DocumentService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from .conftest import PerformanceMonitor, BenchmarkResult, PerformanceMetrics


class TestDocumentProcessingPerformance:
    """Test document processing performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_pdf_parsing_performance(
        self, 
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict,
        test_documents_path: Path
    ):
        """Test PDF parsing performance with different document sizes."""
        parser_factory = ParserFactory()
        results = []
        
        # Test documents with different sizes
        test_cases = [
            {
                "name": "small_pdf",
                "filename": "1_视频教程的 课件幻灯片.pdf",
                "expected_pages": 5,
                "threshold": performance_thresholds["document_processing"]["small_doc_time"]
            },
            {
                "name": "medium_pdf", 
                "filename": "2_TPA-Reversals.pdf",
                "expected_pages": 15,
                "threshold": performance_thresholds["document_processing"]["medium_doc_time"]
            }
        ]
        
        for test_case in test_cases:
            file_path = test_documents_path / test_case["filename"]
            
            if not file_path.exists():
                pytest.skip(f"Test document {test_case['filename']} not found")
                continue
                
            # Monitor performance during parsing
            performance_monitor.start_monitoring()
            
            try:
                start_time = time.time()
                parser = parser_factory.get_parser(str(file_path))
                content = await parser.parse_async(str(file_path))
                end_time = time.time()
                
                # Sample metrics during processing
                for _ in range(5):
                    performance_monitor.sample_metrics()
                    await asyncio.sleep(0.1)
                    
                metrics = performance_monitor.stop_monitoring()
                metrics.execution_time = end_time - start_time
                metrics.success = len(content.text_blocks) > 0
                
                # Validate results
                assert len(content.text_blocks) > 0, "No text blocks extracted"
                assert metrics.execution_time <= test_case["threshold"], \
                    f"Processing time {metrics.execution_time:.2f}s exceeded threshold {test_case['threshold']}s"
                
                result = BenchmarkResult(
                    test_name=f"pdf_parsing_{test_case['name']}",
                    metrics=metrics,
                    threshold_passed=metrics.execution_time <= test_case["threshold"],
                    threshold_values={"max_time": test_case["threshold"]}
                )
                results.append(result)
                
                print(f"\n{test_case['name']} Results:")
                print(f"  Processing time: {metrics.execution_time:.2f}s")
                print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
                print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
                print(f"  Text blocks extracted: {len(content.text_blocks)}")
                print(f"  Images extracted: {len(content.images)}")
                
            except Exception as e:
                metrics = performance_monitor.stop_monitoring()
                metrics.success = False
                metrics.error_message = str(e)
                
                result = BenchmarkResult(
                    test_name=f"pdf_parsing_{test_case['name']}_failed",
                    metrics=metrics,
                    threshold_passed=False,
                    threshold_values={"max_time": test_case["threshold"]}
                )
                results.append(result)
                raise
        
        # Verify all tests passed thresholds
        failed_tests = [r for r in results if not r.threshold_passed]
        assert len(failed_tests) == 0, f"Performance tests failed: {[r.test_name for r in failed_tests]}"
    
    @pytest.mark.asyncio
    async def test_complete_document_pipeline_performance(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict,
        test_documents_path: Path
    ):
        """Test complete document processing pipeline performance."""
        document_service = DocumentService()
        knowledge_service = KnowledgeExtractionService()
        card_service = CardGenerationService()
        
        test_file = test_documents_path / "1_视频教程的 课件幻灯片.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
            
        performance_monitor.start_monitoring()
        
        try:
            start_time = time.time()
            
            # Step 1: Parse document
            parser_factory = ParserFactory()
            parser = parser_factory.get_parser(str(test_file))
            content = await parser.parse_async(str(test_file))
            
            # Sample metrics
            performance_monitor.sample_metrics()
            
            # Step 2: Extract knowledge points
            knowledge_points = await knowledge_service.extract_knowledge_points(content.text_blocks)
            
            # Sample metrics
            performance_monitor.sample_metrics()
            
            # Step 3: Generate cards
            cards = []
            for kp in knowledge_points[:10]:  # Limit to first 10 for performance test
                card = await card_service.generate_card(kp)
                cards.append(card)
                
            # Sample metrics
            performance_monitor.sample_metrics()
            
            end_time = time.time()
            
            metrics = performance_monitor.stop_monitoring()
            metrics.execution_time = end_time - start_time
            metrics.success = len(cards) > 0
            
            # Performance assertions
            max_pipeline_time = performance_thresholds["document_processing"]["medium_doc_time"]
            assert metrics.execution_time <= max_pipeline_time, \
                f"Pipeline time {metrics.execution_time:.2f}s exceeded threshold {max_pipeline_time}s"
            
            max_memory = performance_thresholds["document_processing"]["memory_limit"]
            assert metrics.peak_memory_mb <= max_memory, \
                f"Peak memory {metrics.peak_memory_mb:.2f}MB exceeded threshold {max_memory}MB"
            
            print(f"\nComplete Pipeline Results:")
            print(f"  Total processing time: {metrics.execution_time:.2f}s")
            print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
            print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
            print(f"  Knowledge points extracted: {len(knowledge_points)}")
            print(f"  Cards generated: {len(cards)}")
            
        except Exception as e:
            metrics = performance_monitor.stop_monitoring()
            metrics.success = False
            metrics.error_message = str(e)
            raise
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_processing(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict,
        test_documents_path: Path
    ):
        """Test memory usage patterns during document processing."""
        memory_samples = []
        
        test_file = test_documents_path / "2_TPA-Reversals.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
            
        performance_monitor.start_monitoring()
        
        async def memory_sampler():
            """Sample memory usage every 100ms."""
            while True:
                performance_monitor.sample_metrics()
                current_memory = performance_monitor.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                await asyncio.sleep(0.1)
        
        # Start memory sampling task
        sampler_task = asyncio.create_task(memory_sampler())
        
        try:
            # Process document
            parser_factory = ParserFactory()
            parser = parser_factory.get_parser(str(test_file))
            content = await parser.parse_async(str(test_file))
            
            # Stop sampling
            sampler_task.cancel()
            
            metrics = performance_monitor.stop_monitoring()
            
            # Analyze memory usage patterns
            if memory_samples:
                max_memory = max(memory_samples)
                avg_memory = sum(memory_samples) / len(memory_samples)
                memory_growth = memory_samples[-1] - memory_samples[0] if len(memory_samples) > 1 else 0
                
                print(f"\nMemory Usage Analysis:")
                print(f"  Peak memory: {max_memory:.2f}MB")
                print(f"  Average memory: {avg_memory:.2f}MB")
                print(f"  Memory growth: {memory_growth:.2f}MB")
                print(f"  Samples collected: {len(memory_samples)}")
                
                # Memory threshold checks
                max_allowed = performance_thresholds["document_processing"]["memory_limit"]
                assert max_memory <= max_allowed, \
                    f"Peak memory {max_memory:.2f}MB exceeded threshold {max_allowed}MB"
                
                # Check for memory leaks (growth should be reasonable)
                assert memory_growth <= 100, \
                    f"Memory growth {memory_growth:.2f}MB suggests potential memory leak"
            
        except asyncio.CancelledError:
            pass
        finally:
            if not sampler_task.cancelled():
                sampler_task.cancel()
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict,
        test_documents_path: Path
    ):
        """Test performance with concurrent document processing."""
        test_files = [
            "1_视频教程的 课件幻灯片.pdf",
            "2_TPA-Reversals.pdf"
        ]
        
        # Filter existing files
        existing_files = [f for f in test_files if (test_documents_path / f).exists()]
        if len(existing_files) < 2:
            pytest.skip("Need at least 2 test documents for concurrent testing")
        
        performance_monitor.start_monitoring()
        
        async def process_document(file_path: Path) -> Dict:
            """Process a single document and return metrics."""
            start_time = time.time()
            
            try:
                parser_factory = ParserFactory()
                parser = parser_factory.get_parser(str(file_path))
                content = await parser.parse_async(str(file_path))
                
                end_time = time.time()
                
                return {
                    "filename": file_path.name,
                    "processing_time": end_time - start_time,
                    "text_blocks": len(content.text_blocks),
                    "images": len(content.images),
                    "success": True
                }
            except Exception as e:
                return {
                    "filename": file_path.name,
                    "processing_time": time.time() - start_time,
                    "error": str(e),
                    "success": False
                }
        
        # Process documents concurrently
        start_time = time.time()
        
        tasks = [
            process_document(test_documents_path / filename) 
            for filename in existing_files[:3]  # Limit to 3 concurrent
        ]
        
        # Sample metrics during concurrent processing
        async def sample_during_processing():
            while True:
                performance_monitor.sample_metrics()
                await asyncio.sleep(0.2)
        
        sampler_task = asyncio.create_task(sample_during_processing())
        
        try:
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            sampler_task.cancel()
            
            metrics = performance_monitor.stop_monitoring()
            total_time = end_time - start_time
            
            # Analyze results
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            print(f"\nConcurrent Processing Results:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Failed: {len(failed_results)}")
            print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
            
            for result in successful_results:
                print(f"  {result['filename']}: {result['processing_time']:.2f}s")
            
            # Performance assertions
            assert len(failed_results) == 0, f"Some documents failed: {failed_results}"
            
            # Concurrent processing should be more efficient than sequential
            sequential_time_estimate = sum(r["processing_time"] for r in successful_results)
            efficiency = sequential_time_estimate / total_time if total_time > 0 else 0
            
            print(f"  Concurrency efficiency: {efficiency:.2f}x")
            assert efficiency >= 1.5, f"Concurrent processing not efficient enough: {efficiency:.2f}x"
            
        except asyncio.CancelledError:
            pass
        finally:
            if not sampler_task.cancelled():
                sampler_task.cancel()