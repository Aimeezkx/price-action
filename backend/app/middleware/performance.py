"""
Performance monitoring middleware for FastAPI
Tracks request/response times, database queries, and system metrics
"""

import time
import psutil
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Stores and manages performance metrics"""
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.request_times: deque = deque(maxlen=max_entries)
        self.db_queries: deque = deque(maxlen=max_entries)
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: deque = deque(maxlen=100)
        self.error_count: Dict[str, int] = defaultdict(int)
        
    def add_request_time(self, endpoint: str, method: str, duration: float, status_code: int):
        """Add request timing data"""
        self.request_times.append({
            'endpoint': endpoint,
            'method': method,
            'duration': duration,
            'status_code': status_code,
            'timestamp': datetime.now()
        })
        
        # Track per-endpoint stats
        key = f"{method} {endpoint}"
        self.endpoint_stats[key].append(duration)
        
        # Keep only recent stats (last 100 requests per endpoint)
        if len(self.endpoint_stats[key]) > 100:
            self.endpoint_stats[key] = self.endpoint_stats[key][-100:]
            
        # Track errors
        if status_code >= 400:
            self.error_count[key] += 1
            
    def add_db_query(self, query: str, duration: float, params: Optional[Dict] = None):
        """Add database query timing data"""
        query_data = {
            'query': query[:200] + '...' if len(query) > 200 else query,
            'duration': duration,
            'params': str(params)[:100] if params else None,
            'timestamp': datetime.now()
        }
        
        self.db_queries.append(query_data)
        
        # Track slow queries (>100ms)
        if duration > 0.1:
            self.slow_queries.append(query_data)
            logger.warning(f"Slow query detected: {duration:.3f}s - {query[:100]}")
            
    def get_stats(self) -> Dict:
        """Get performance statistics summary"""
        now = datetime.now()
        recent_requests = [
            r for r in self.request_times 
            if now - r['timestamp'] < timedelta(minutes=5)
        ]
        
        recent_queries = [
            q for q in self.db_queries 
            if now - q['timestamp'] < timedelta(minutes=5)
        ]
        
        # Calculate endpoint statistics
        endpoint_summary = {}
        for endpoint, times in self.endpoint_stats.items():
            if times:
                endpoint_summary[endpoint] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'p95_time': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
                    'error_count': self.error_count.get(endpoint, 0)
                }
        
        return {
            'summary': {
                'total_requests': len(self.request_times),
                'recent_requests_5min': len(recent_requests),
                'total_db_queries': len(self.db_queries),
                'recent_db_queries_5min': len(recent_queries),
                'slow_queries_count': len(self.slow_queries),
                'avg_request_time': sum(r['duration'] for r in recent_requests) / len(recent_requests) if recent_requests else 0,
                'avg_query_time': sum(q['duration'] for q in recent_queries) / len(recent_queries) if recent_queries else 0
            },
            'endpoints': endpoint_summary,
            'slow_queries': list(self.slow_queries)[-10:],  # Last 10 slow queries
            'system': self.get_system_metrics()
        }
        
    def get_system_metrics(self) -> Dict:
        """Get current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

# Global metrics instance
performance_metrics = PerformanceMetrics()

class PerformanceMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware to track request performance"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Track memory before request
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        response = await call_next(request)
        
        # Calculate timing and memory usage
        duration = time.time() - start_time
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = memory_after - memory_before
        
        # Extract endpoint info
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Record metrics
        performance_metrics.add_request_time(endpoint, method, duration, status_code)
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        response.headers["X-Memory-Delta"] = f"{memory_delta:.2f}MB"
        
        # Log slow requests
        if duration > 1.0:  # Log requests slower than 1 second
            logger.warning(
                f"Slow request: {method} {endpoint} - {duration:.3f}s "
                f"(Status: {status_code}, Memory: +{memory_delta:.2f}MB)"
            )
            
        return response

# Database query performance tracking
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    performance_metrics.add_db_query(statement, total, parameters)

def get_performance_stats() -> Dict:
    """Get current performance statistics"""
    return performance_metrics.get_stats()

def reset_performance_stats():
    """Reset all performance statistics"""
    global performance_metrics
    performance_metrics = PerformanceMetrics()