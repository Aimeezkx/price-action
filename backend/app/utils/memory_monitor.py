"""
Memory usage monitoring for document processing
Tracks memory consumption during heavy operations and provides optimization recommendations
"""

import gc
import psutil
import logging
import tracemalloc
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory percentage
    available_mb: float  # Available system memory in MB
    process_name: str = "document_processor"
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryStats:
    """Memory statistics over time"""
    snapshots: deque = field(default_factory=lambda: deque(maxlen=100))
    peak_rss_mb: float = 0
    peak_vms_mb: float = 0
    total_allocations: int = 0
    total_deallocations: int = 0
    
    def add_snapshot(self, snapshot: MemorySnapshot):
        self.snapshots.append(snapshot)
        self.peak_rss_mb = max(self.peak_rss_mb, snapshot.rss_mb)
        self.peak_vms_mb = max(self.peak_vms_mb, snapshot.vms_mb)
    
    def get_average_usage(self) -> float:
        if not self.snapshots:
            return 0
        return sum(s.rss_mb for s in self.snapshots) / len(self.snapshots)
    
    def get_peak_usage(self) -> float:
        return self.peak_rss_mb
    
    def get_memory_trend(self) -> str:
        if len(self.snapshots) < 2:
            return "insufficient_data"
        
        recent = list(self.snapshots)[-10:]  # Last 10 snapshots
        if len(recent) < 2:
            return "insufficient_data"
        
        start_avg = sum(s.rss_mb for s in recent[:len(recent)//2]) / (len(recent)//2)
        end_avg = sum(s.rss_mb for s in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        
        if end_avg > start_avg * 1.1:
            return "increasing"
        elif end_avg < start_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

class MemoryMonitor:
    """Memory monitoring and analysis"""
    
    def __init__(self, enable_tracemalloc: bool = True):
        self.process = psutil.Process()
        self.stats = MemoryStats()
        self.enable_tracemalloc = enable_tracemalloc
        self.monitoring_active = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
        if enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def take_snapshot(self, context: Optional[str] = None, metadata: Optional[Dict] = None) -> MemorySnapshot:
        """Take a memory usage snapshot"""
        try:
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()
            
            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=self.process.memory_percent(),
                available_mb=system_memory.available / 1024 / 1024,
                context=context,
                metadata=metadata or {}
            )
            
            with self._lock:
                self.stats.add_snapshot(snapshot)
            
            # Log warning for high memory usage
            if snapshot.rss_mb > 1000:  # > 1GB
                logger.warning(f"High memory usage detected: {snapshot.rss_mb:.1f}MB in {context or 'unknown context'}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error taking memory snapshot: {e}")
            return MemorySnapshot(
                timestamp=datetime.now(),
                rss_mb=0, vms_mb=0, percent=0, available_mb=0,
                context=context,
                metadata={"error": str(e)}
            )
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self._lock:
            current_snapshot = self.take_snapshot("stats_request")
            
            stats = {
                "current": {
                    "rss_mb": current_snapshot.rss_mb,
                    "vms_mb": current_snapshot.vms_mb,
                    "percent": current_snapshot.percent,
                    "available_mb": current_snapshot.available_mb
                },
                "historical": {
                    "peak_rss_mb": self.stats.peak_rss_mb,
                    "peak_vms_mb": self.stats.peak_vms_mb,
                    "average_rss_mb": self.stats.get_average_usage(),
                    "trend": self.stats.get_memory_trend(),
                    "snapshot_count": len(self.stats.snapshots)
                },
                "system": {
                    "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                    "available_memory_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
                    "memory_percent": psutil.virtual_memory().percent
                }
            }
            
            # Add tracemalloc stats if available
            if self.enable_tracemalloc and tracemalloc.is_tracing():
                try:
                    current_trace, peak_trace = tracemalloc.get_traced_memory()
                    stats["tracemalloc"] = {
                        "current_mb": current_trace / 1024 / 1024,
                        "peak_mb": peak_trace / 1024 / 1024
                    }
                except Exception as e:
                    stats["tracemalloc"] = {"error": str(e)}
            
            return stats
    
    def get_top_memory_contexts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contexts with highest memory usage"""
        with self._lock:
            context_usage = {}
            
            for snapshot in self.stats.snapshots:
                if snapshot.context:
                    if snapshot.context not in context_usage:
                        context_usage[snapshot.context] = {
                            "max_rss_mb": 0,
                            "avg_rss_mb": 0,
                            "count": 0,
                            "total_rss_mb": 0
                        }
                    
                    ctx = context_usage[snapshot.context]
                    ctx["max_rss_mb"] = max(ctx["max_rss_mb"], snapshot.rss_mb)
                    ctx["total_rss_mb"] += snapshot.rss_mb
                    ctx["count"] += 1
                    ctx["avg_rss_mb"] = ctx["total_rss_mb"] / ctx["count"]
            
            # Sort by max memory usage
            sorted_contexts = sorted(
                context_usage.items(),
                key=lambda x: x[1]["max_rss_mb"],
                reverse=True
            )
            
            return [
                {"context": ctx, **stats}
                for ctx, stats in sorted_contexts[:limit]
            ]
    
    def analyze_memory_leaks(self) -> Dict[str, Any]:
        """Analyze potential memory leaks"""
        with self._lock:
            if len(self.stats.snapshots) < 10:
                return {"status": "insufficient_data"}
            
            recent_snapshots = list(self.stats.snapshots)[-20:]
            
            # Check for consistent memory growth
            memory_values = [s.rss_mb for s in recent_snapshots]
            
            # Simple linear regression to detect trend
            n = len(memory_values)
            x_sum = sum(range(n))
            y_sum = sum(memory_values)
            xy_sum = sum(i * memory_values[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            analysis = {
                "memory_trend_mb_per_snapshot": slope,
                "total_growth_mb": memory_values[-1] - memory_values[0],
                "growth_percentage": ((memory_values[-1] - memory_values[0]) / memory_values[0]) * 100 if memory_values[0] > 0 else 0,
                "snapshots_analyzed": n
            }
            
            # Determine leak likelihood
            if slope > 5:  # Growing by more than 5MB per snapshot
                analysis["leak_likelihood"] = "high"
                analysis["recommendation"] = "Investigate memory usage patterns and consider garbage collection"
            elif slope > 1:
                analysis["leak_likelihood"] = "medium"
                analysis["recommendation"] = "Monitor memory usage closely"
            else:
                analysis["leak_likelihood"] = "low"
                analysis["recommendation"] = "Memory usage appears stable"
            
            return analysis
    
    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and measure impact"""
        before_snapshot = self.take_snapshot("before_gc")
        
        # Force garbage collection
        collected = gc.collect()
        
        after_snapshot = self.take_snapshot("after_gc")
        
        freed_mb = before_snapshot.rss_mb - after_snapshot.rss_mb
        
        result = {
            "objects_collected": collected,
            "memory_freed_mb": freed_mb,
            "before_rss_mb": before_snapshot.rss_mb,
            "after_rss_mb": after_snapshot.rss_mb,
            "effectiveness": "high" if freed_mb > 50 else "medium" if freed_mb > 10 else "low"
        }
        
        logger.info(f"Garbage collection freed {freed_mb:.1f}MB, collected {collected} objects")
        
        return result

# Global memory monitor instance
memory_monitor = MemoryMonitor()

@contextmanager
def memory_tracking(context: str, metadata: Optional[Dict] = None):
    """Context manager for tracking memory usage during operations"""
    start_snapshot = memory_monitor.take_snapshot(f"{context}_start", metadata)
    
    try:
        yield memory_monitor
    finally:
        end_snapshot = memory_monitor.take_snapshot(f"{context}_end", metadata)
        
        memory_delta = end_snapshot.rss_mb - start_snapshot.rss_mb
        
        if memory_delta > 100:  # More than 100MB increase
            logger.warning(
                f"High memory usage in {context}: +{memory_delta:.1f}MB "
                f"(from {start_snapshot.rss_mb:.1f}MB to {end_snapshot.rss_mb:.1f}MB)"
            )

def memory_profiled(context: str):
    """Decorator to profile memory usage of functions"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with memory_tracking(f"{context}:{func.__name__}"):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with memory_tracking(f"{context}:{func.__name__}"):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Document processing specific memory monitoring
class DocumentProcessingMemoryMonitor:
    """Specialized memory monitoring for document processing operations"""
    
    @staticmethod
    def monitor_document_parsing(doc_id: str, file_size_mb: float):
        """Monitor memory during document parsing"""
        metadata = {"document_id": doc_id, "file_size_mb": file_size_mb}
        return memory_tracking("document_parsing", metadata)
    
    @staticmethod
    def monitor_image_extraction(doc_id: str, image_count: int):
        """Monitor memory during image extraction"""
        metadata = {"document_id": doc_id, "image_count": image_count}
        return memory_tracking("image_extraction", metadata)
    
    @staticmethod
    def monitor_nlp_processing(doc_id: str, text_length: int):
        """Monitor memory during NLP processing"""
        metadata = {"document_id": doc_id, "text_length": text_length}
        return memory_tracking("nlp_processing", metadata)
    
    @staticmethod
    def monitor_embedding_generation(doc_id: str, segment_count: int):
        """Monitor memory during embedding generation"""
        metadata = {"document_id": doc_id, "segment_count": segment_count}
        return memory_tracking("embedding_generation", metadata)
    
    @staticmethod
    def get_processing_recommendations(doc_size_mb: float) -> Dict[str, Any]:
        """Get memory optimization recommendations based on document size"""
        current_memory = memory_monitor.get_memory_stats()
        available_mb = current_memory["current"]["available_mb"]
        
        recommendations = {
            "batch_size": "normal",
            "enable_streaming": False,
            "force_gc_frequency": "normal",
            "warnings": []
        }
        
        # Adjust recommendations based on document size and available memory
        if doc_size_mb > 100:  # Large document
            if available_mb < 2000:  # Less than 2GB available
                recommendations["batch_size"] = "small"
                recommendations["enable_streaming"] = True
                recommendations["force_gc_frequency"] = "high"
                recommendations["warnings"].append("Large document with limited memory - using conservative processing")
            
        if doc_size_mb > 500:  # Very large document
            recommendations["batch_size"] = "small"
            recommendations["enable_streaming"] = True
            recommendations["warnings"].append("Very large document - consider splitting into smaller chunks")
        
        if current_memory["current"]["percent"] > 80:
            recommendations["force_gc_frequency"] = "high"
            recommendations["warnings"].append("High current memory usage - frequent garbage collection recommended")
        
        return recommendations