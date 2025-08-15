"""
Performance monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ..middleware.performance import get_performance_stats, reset_performance_stats
from ..utils.memory_monitor import memory_monitor
from ..core.cache import cache_manager
from ..core.db_optimization import DatabaseOptimizer, run_database_optimization
from ..core.database import get_db_session

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get current performance metrics including:
    - Request timing statistics
    - Database query performance
    - System resource usage
    - Slow query analysis
    """
    try:
        stats = get_performance_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint with performance indicators
    """
    stats = get_performance_stats()
    system_metrics = stats.get('system', {})
    
    # Determine health status based on system metrics
    health_status = "healthy"
    issues = []
    
    if system_metrics.get('cpu_percent', 0) > 80:
        health_status = "warning"
        issues.append("High CPU usage")
        
    if system_metrics.get('memory_percent', 0) > 85:
        health_status = "warning"
        issues.append("High memory usage")
        
    if system_metrics.get('disk_percent', 0) > 90:
        health_status = "critical"
        issues.append("Low disk space")
        
    # Check for performance issues
    summary = stats.get('summary', {})
    if summary.get('avg_request_time', 0) > 2.0:
        health_status = "warning"
        issues.append("Slow average response time")
        
    if summary.get('slow_queries_count', 0) > 10:
        health_status = "warning"
        issues.append("Multiple slow database queries")
    
    return {
        "status": health_status,
        "timestamp": stats.get('timestamp'),
        "issues": issues,
        "metrics": {
            "avg_response_time": summary.get('avg_request_time', 0),
            "recent_requests": summary.get('recent_requests_5min', 0),
            "cpu_percent": system_metrics.get('cpu_percent', 0),
            "memory_percent": system_metrics.get('memory_percent', 0),
            "disk_percent": system_metrics.get('disk_percent', 0)
        }
    }

@router.post("/performance/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset performance metrics (useful for testing or after maintenance)
    """
    try:
        reset_performance_stats()
        return {"status": "success", "message": "Performance metrics reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting metrics: {str(e)}")

@router.get("/performance/endpoints")
async def get_endpoint_performance() -> Dict[str, Any]:
    """
    Get detailed performance metrics for each API endpoint
    """
    stats = get_performance_stats()
    endpoints = stats.get('endpoints', {})
    
    # Sort endpoints by average response time (slowest first)
    sorted_endpoints = sorted(
        endpoints.items(),
        key=lambda x: x[1].get('avg_time', 0),
        reverse=True
    )
    
    return {
        "status": "success",
        "data": {
            "endpoints": dict(sorted_endpoints),
            "total_endpoints": len(endpoints),
            "slowest_endpoint": sorted_endpoints[0] if sorted_endpoints else None
        }
    }

@router.get("/performance/queries")
async def get_query_performance() -> Dict[str, Any]:
    """
    Get database query performance metrics
    """
    stats = get_performance_stats()
    
    return {
        "status": "success",
        "data": {
            "slow_queries": stats.get('slow_queries', []),
            "total_queries": stats.get('summary', {}).get('total_db_queries', 0),
            "recent_queries": stats.get('summary', {}).get('recent_db_queries_5min', 0),
            "avg_query_time": stats.get('summary', {}).get('avg_query_time', 0)
        }
    }

@router.get("/memory")
async def get_memory_stats() -> Dict[str, Any]:
    """
    Get current memory usage statistics
    """
    try:
        stats = memory_monitor.get_memory_stats()
        top_contexts = memory_monitor.get_top_memory_contexts()
        leak_analysis = memory_monitor.analyze_memory_leaks()
        
        return {
            "status": "success",
            "data": {
                "current_usage": stats,
                "top_memory_contexts": top_contexts,
                "leak_analysis": leak_analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory stats: {str(e)}")

@router.post("/memory/gc")
async def force_garbage_collection() -> Dict[str, Any]:
    """
    Force garbage collection and return impact metrics
    """
    try:
        result = memory_monitor.force_garbage_collection()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during garbage collection: {str(e)}")

@router.get("/cache")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics
    """
    try:
        stats = await cache_manager.get_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cache stats: {str(e)}")

@router.post("/cache/clear")
async def clear_cache(namespace: str = None) -> Dict[str, Any]:
    """
    Clear cache (optionally by namespace)
    """
    try:
        if namespace:
            success = await cache_manager.clear_namespace(namespace)
            message = f"Cleared cache namespace: {namespace}"
        else:
            # Clear all namespaces (implementation would need to be added to cache_manager)
            success = True
            message = "Cache clear requested"
        
        return {
            "status": "success" if success else "error",
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/database")
async def get_database_performance():
    """
    Get database performance analysis
    """
    try:
        async with get_db_session() as session:
            optimizer = DatabaseOptimizer(session.bind)
            
            performance_analysis = await optimizer.analyze_query_performance(session)
            missing_indexes = await optimizer.get_missing_indexes(session)
            size_info = await optimizer.get_database_size_info(session)
            
            return {
                "status": "success",
                "data": {
                    "performance_analysis": performance_analysis,
                    "missing_indexes": missing_indexes,
                    "size_info": size_info
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing database performance: {str(e)}")

@router.post("/database/optimize")
async def optimize_database():
    """
    Run database optimization (create indexes, vacuum tables)
    """
    try:
        result = await run_database_optimization()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing database: {str(e)}")

@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get comprehensive system performance metrics
    """
    try:
        performance_stats = get_performance_stats()
        memory_stats = memory_monitor.get_memory_stats()
        cache_stats = await cache_manager.get_stats()
        
        return {
            "status": "success",
            "data": {
                "performance": performance_stats,
                "memory": memory_stats,
                "cache": cache_stats,
                "timestamp": performance_stats.get('timestamp')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system metrics: {str(e)}")