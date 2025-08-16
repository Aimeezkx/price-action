"""Memory usage monitoring during document processing."""

import pytest
import asyncio
import time
import psutil
import gc
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from app.parsers.factory import ParserFactory
from app.services.document_service import DocumentService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from .conftest import PerformanceMonitor, BenchmarkResult, PerformanceMetrics


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time."""
    timestamp: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float  # Available system memory


class MemoryProfiler:
    """Profile memory usage during operations."""
    
    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.snapshots: List[MemorySnapshot] = []
        self.process = psutil.Process()
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start memory monitoring in background."""
        self.snapshots.clear()
        self.monitoring = True
        
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                system_memory = psutil.virtual_memory()
                
                snapshot = MemorySnapshot(
                    timestamp=time.time(),
                    rss_mb=memory_info.rss / 1024 / 1024,
                    vms_mb=memory_info.vms / 1024 / 1024,
                    percent=self.process.memory_percent(),
                    available_mb=system_memory.available / 1024 / 1024
                )
                
                self.snapshots.append(snapshot)
                await asyncio.sleep(self.sample_interval)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
                
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        
    def get_memory_stats(self) -> Dict:
        """Get memory usage statistics."""
        if not self.snapshots:
            return {}
            
        rss_values = [s.rss_mb for s in self.snapshots]
        vms_values = [s.vms_mb for s in self.snapshots]
        percent_values = [s.percent for s in self.snapshots]
        
        return {
            "peak_rss_mb": max(rss_values),
            "avg_rss_mb": sum(rss_values) / len(rss_values),
            "min_rss_mb": min(rss_values),
            "peak_vms_mb": max(vms_values),
            "avg_vms_mb": sum(vms_values) / len(vms_values),
            "peak_percent": max(percent_values),
            "avg_percent": sum(percent_values) / len(percent_values),
            "memory_growth_mb": rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            "samples_count": len(self.snapshots),
            "duration_seconds": self.snapshots[-1].timestamp - self.snapshots[0].timestamp if len(self.snapshots) > 1 else 0
        }
        
    def detect_memory_leaks(self, threshold_mb: float = 50) -> bool:
        """Detect potential memory leaks."""
        stats = self.get_memory_stats()
        return stats.get("memory_growth_mb", 0) > threshold_mb


class TestMemoryMonitoring:
    """Test memory usage monitoring during document processing."""
    
    @pytest.mark.asyncio
    async def test_pdf_parsing_memory_usage(
        self,
        test_documents_path: Path,
        performance_thresholds: Dict
    ):
        """Test memory usage during PDF parsing."""
        profiler = MemoryProfiler(sample_interval=0.05)  # Sample every 50ms
        
        test_file = test_documents_path / "1_视频教程的 课件幻灯片.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
            
        # Start memory monitoring
        monitor_task = asyncio.create_task(profiler.start_monitoring())
        
        try:
            # Force garbage collection before test
            gc.collect()
            
            # Parse document
            parser_factory = ParserFactory()
            parser = parser_factory.get_parser(str(test_file))
            content = await parser.parse_async(str(test_file))
            
            # Let monitoring run a bit more to capture cleanup
            await asyncio.sleep(0.5)
            
        finally:
            profiler.stop_monitoring()
            monitor_task.cancel()
            
        # Analyze memory usage
        stats = profiler.get_memory_stats()
        
        print(f"\nPDF Parsing Memory Analysis:")
        print(f"  Peak RSS: {stats['peak_rss_mb']:.2f}MB")
        print(f"  Average RSS: {stats['avg_rss_mb']:.2f}MB")
        print(f"  Memory growth: {stats['memory_growth_mb']:.2f}MB")
        print(f"  Peak memory %: {stats['peak_percent']:.2f}%")
        print(f"  Duration: {stats['duration_seconds']:.2f}s")
        print(f"  Samples: {stats['samples_count']}")
        
        # Memory assertions
        max_memory = performance_thresholds["document_processing"]["memory_limit"]
        assert stats["peak_rss_mb"] <= max_memory, \
            f"Peak memory {stats['peak_rss_mb']:.2f}MB exceeded threshold {max_memory}MB"
        
        # Check for memory leaks
        assert not profiler.detect_memory_leaks(50), \
            f"Potential memory leak detected: {stats['memory_growth_mb']:.2f}MB growth"
        
        # Validate parsing results
        assert len(content.text_blocks) > 0, "No text blocks extracted"
        
    @pytest.mark.asyncio
    async def test_complete_pipeline_memory_usage(
        self,
        test_documents_path: Path,
        performance_thresholds: Dict
    ):
        """Test memory usage during complete document processing pipeline."""
        profiler = MemoryProfiler(sample_interval=0.1)
        
        test_file = test_documents_path / "2_TPA-Reversals.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
            
        # Services
        document_service = DocumentService()
        knowledge_service = KnowledgeExtractionService()
        card_service = CardGenerationService()
        
        # Start memory monitoring
        monitor_task = asyncio.create_task(profiler.start_monitoring())
        
        try:
            gc.collect()  # Clean up before test
            
            # Step 1: Parse document
            parser_factory = ParserFactory()
            parser = parser_factory.get_parser(str(test_file))
            content = await parser.parse_async(str(test_file))
            
            await asyncio.sleep(0.2)  # Let memory settle
            
            # Step 2: Extract knowledge points
            knowledge_points = await knowledge_service.extract_knowledge_points(
                content.text_blocks[:10]  # Limit for memory test
            )
            
            await asyncio.sleep(0.2)
            
            # Step 3: Generate cards
            cards = []
            for kp in knowledge_points[:5]:  # Limit for memory test
                card = await card_service.generate_card(kp)
                cards.append(card)
                
            await asyncio.sleep(0.5)  # Let cleanup happen
            
        finally:
            profiler.stop_monitoring()
            monitor_task.cancel()
            
        # Analyze memory usage
        stats = profiler.get_memory_stats()
        
        print(f"\nComplete Pipeline Memory Analysis:")
        print(f"  Peak RSS: {stats['peak_rss_mb']:.2f}MB")
        print(f"  Average RSS: {stats['avg_rss_mb']:.2f}MB")
        print(f"  Memory growth: {stats['memory_growth_mb']:.2f}MB")
        print(f"  Peak memory %: {stats['peak_percent']:.2f}%")
        print(f"  Duration: {stats['duration_seconds']:.2f}s")
        
        # Memory assertions
        max_memory = performance_thresholds["document_processing"]["memory_limit"]
        assert stats["peak_rss_mb"] <= max_memory, \
            f"Peak memory {stats['peak_rss_mb']:.2f}MB exceeded threshold {max_memory}MB"
        
        # Pipeline should not have significant memory leaks
        assert not profiler.detect_memory_leaks(100), \
            f"Potential memory leak in pipeline: {stats['memory_growth_mb']:.2f}MB growth"
            
    @pytest.mark.asyncio
    async def test_concurrent_processing_memory_usage(
        self,
        test_documents_path: Path,
        performance_thresholds: Dict
    ):
        """Test memory usage during concurrent document processing."""
        profiler = MemoryProfiler(sample_interval=0.1)
        
        # Get available test files
        test_files = [
            "1_视频教程的 课件幻灯片.pdf",
            "2_TPA-Reversals.pdf"
        ]
        
        existing_files = [f for f in test_files if (test_documents_path / f).exists()]
        if len(existing_files) < 2:
            pytest.skip("Need at least 2 test documents for concurrent testing")
            
        # Start memory monitoring
        monitor_task = asyncio.create_task(profiler.start_monitoring())
        
        async def process_document(file_path: Path) -> Dict:
            """Process a single document."""
            try:
                parser_factory = ParserFactory()
                parser = parser_factory.get_parser(str(file_path))
                content = await parser.parse_async(str(file_path))
                
                return {
                    "filename": file_path.name,
                    "text_blocks": len(content.text_blocks),
                    "images": len(content.images),
                    "success": True
                }
            except Exception as e:
                return {
                    "filename": file_path.name,
                    "error": str(e),
                    "success": False
                }
        
        try:
            gc.collect()  # Clean up before test
            
            # Process documents concurrently
            tasks = [
                process_document(test_documents_path / filename)
                for filename in existing_files[:2]  # Limit to 2 for memory test
            ]
            
            results = await asyncio.gather(*tasks)
            
            await asyncio.sleep(1.0)  # Let cleanup happen
            
        finally:
            profiler.stop_monitoring()
            monitor_task.cancel()
            
        # Analyze memory usage
        stats = profiler.get_memory_stats()
        
        print(f"\nConcurrent Processing Memory Analysis:")
        print(f"  Documents processed: {len(existing_files[:2])}")
        print(f"  Peak RSS: {stats['peak_rss_mb']:.2f}MB")
        print(f"  Average RSS: {stats['avg_rss_mb']:.2f}MB")
        print(f"  Memory growth: {stats['memory_growth_mb']:.2f}MB")
        print(f"  Peak memory %: {stats['peak_percent']:.2f}%")
        
        # Concurrent processing should use more memory but within limits
        max_memory = performance_thresholds["document_processing"]["memory_limit"] * 1.5  # Allow 50% more for concurrent
        assert stats["peak_rss_mb"] <= max_memory, \
            f"Peak memory {stats['peak_rss_mb']:.2f}MB exceeded concurrent threshold {max_memory}MB"
        
        # Check results
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= 1, "At least one document should process successfully"
        
    @pytest.mark.asyncio
    async def test_memory_cleanup_after_processing(
        self,
        test_documents_path: Path
    ):
        """Test that memory is properly cleaned up after processing."""
        profiler = MemoryProfiler(sample_interval=0.1)
        
        test_file = test_documents_path / "1_视频教程的 课件幻灯片.pdf"
        if not test_file.exists():
            pytest.skip("Test document not found")
            
        # Measure baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Start monitoring
        monitor_task = asyncio.create_task(profiler.start_monitoring())
        
        try:
            # Process document multiple times
            for i in range(3):
                parser_factory = ParserFactory()
                parser = parser_factory.get_parser(str(test_file))
                content = await parser.parse_async(str(test_file))
                
                # Explicitly delete references
                del content
                del parser
                
                # Force garbage collection
                gc.collect()
                
                await asyncio.sleep(0.5)  # Let cleanup happen
                
        finally:
            profiler.stop_monitoring()
            monitor_task.cancel()
            
        # Final cleanup and measurement
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        stats = profiler.get_memory_stats()
        memory_growth = final_memory - baseline_memory
        
        print(f"\nMemory Cleanup Analysis:")
        print(f"  Baseline memory: {baseline_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Net memory growth: {memory_growth:.2f}MB")
        print(f"  Peak during processing: {stats['peak_rss_mb']:.2f}MB")
        print(f"  Processing cycles: 3")
        
        # Memory growth should be minimal after cleanup
        assert memory_growth <= 30, \
            f"Memory growth after cleanup {memory_growth:.2f}MB suggests memory leak"
            
    @pytest.mark.asyncio
    async def test_large_document_memory_scaling(
        self,
        test_documents_path: Path,
        performance_thresholds: Dict
    ):
        """Test memory usage scaling with document size."""
        profiler = MemoryProfiler(sample_interval=0.1)
        
        # Test with different document sizes if available
        test_cases = [
            {
                "filename": "1_视频教程的 课件幻灯片.pdf",
                "expected_size": "small",
                "memory_multiplier": 1.0
            },
            {
                "filename": "2_TPA-Reversals.pdf", 
                "expected_size": "medium",
                "memory_multiplier": 1.5
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            test_file = test_documents_path / test_case["filename"]
            if not test_file.exists():
                continue
                
            # Start monitoring for this document
            profiler.snapshots.clear()
            monitor_task = asyncio.create_task(profiler.start_monitoring())
            
            try:
                gc.collect()
                
                parser_factory = ParserFactory()
                parser = parser_factory.get_parser(str(test_file))
                content = await parser.parse_async(str(test_file))
                
                await asyncio.sleep(0.5)
                
            finally:
                profiler.stop_monitoring()
                monitor_task.cancel()
                
            stats = profiler.get_memory_stats()
            
            result = {
                "filename": test_case["filename"],
                "size_category": test_case["expected_size"],
                "peak_memory_mb": stats["peak_rss_mb"],
                "avg_memory_mb": stats["avg_rss_mb"],
                "text_blocks": len(content.text_blocks),
                "images": len(content.images)
            }
            
            results.append(result)
            
            print(f"\n{test_case['expected_size'].title()} Document Memory Usage:")
            print(f"  File: {test_case['filename']}")
            print(f"  Peak memory: {stats['peak_rss_mb']:.2f}MB")
            print(f"  Text blocks: {len(content.text_blocks)}")
            print(f"  Images: {len(content.images)}")
            
            # Check memory scaling
            base_memory_limit = performance_thresholds["document_processing"]["memory_limit"]
            expected_limit = base_memory_limit * test_case["memory_multiplier"]
            
            assert stats["peak_rss_mb"] <= expected_limit, \
                f"Memory usage {stats['peak_rss_mb']:.2f}MB exceeded scaled limit {expected_limit}MB"
        
        # Compare memory usage between different document sizes
        if len(results) >= 2:
            small_result = next((r for r in results if r["size_category"] == "small"), None)
            medium_result = next((r for r in results if r["size_category"] == "medium"), None)
            
            if small_result and medium_result:
                memory_ratio = medium_result["peak_memory_mb"] / small_result["peak_memory_mb"]
                content_ratio = medium_result["text_blocks"] / max(small_result["text_blocks"], 1)
                
                print(f"\nMemory Scaling Analysis:")
                print(f"  Memory ratio (medium/small): {memory_ratio:.2f}x")
                print(f"  Content ratio (medium/small): {content_ratio:.2f}x")
                
                # Memory should scale reasonably with content size
                assert memory_ratio <= content_ratio * 2, \
                    f"Memory scaling {memory_ratio:.2f}x too high for content ratio {content_ratio:.2f}x"