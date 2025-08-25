"""
Health check API endpoints
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any
import logging
import os
import psutil
import redis

from ..core.database import get_db, engine
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and health"""
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            
            # Check if pgvector extension is available
            try:
                vector_result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                has_vector = vector_result.fetchone() is not None
            except Exception:
                has_vector = False
            
            return {
                "status": "healthy",
                "connected": True,
                "database_url": settings.database_url.split('@')[1] if '@' in settings.database_url else "local",
                "pgvector_enabled": has_vector,
                "response_time_ms": 0  # Could add timing here
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "database_url": settings.database_url.split('@')[1] if '@' in settings.database_url else "local"
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and health"""
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        info = r.info()
        return {
            "status": "healthy",
            "connected": True,
            "redis_url": settings.redis_url.split('@')[1] if '@' in settings.redis_url else "local",
            "memory_usage": info.get('used_memory_human', 'unknown'),
            "uptime_seconds": info.get('uptime_in_seconds', 0)
        }
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "redis_url": settings.redis_url.split('@')[1] if '@' in settings.redis_url else "local"
        }


async def check_filesystem_health() -> Dict[str, Any]:
    """Check filesystem and upload directory health"""
    try:
        upload_dir = settings.upload_dir
        
        # Check if upload directory exists and is writable
        os.makedirs(upload_dir, exist_ok=True)
        test_file = os.path.join(upload_dir, '.health_check')
        
        # Test write access
        with open(test_file, 'w') as f:
            f.write('health_check')
        
        # Test read access
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up test file
        os.remove(test_file)
        
        # Get disk usage
        disk_usage = psutil.disk_usage(upload_dir)
        
        return {
            "status": "healthy",
            "upload_dir": upload_dir,
            "writable": True,
            "disk_usage": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "usage_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
            }
        }
    except Exception as e:
        logger.error(f"Filesystem health check failed: {e}")
        return {
            "status": "unhealthy",
            "upload_dir": settings.upload_dir,
            "writable": False,
            "error": str(e)
        }


async def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "python_version": os.sys.version.split()[0],
            "platform": os.name
        }
    except Exception as e:
        logger.warning(f"System info collection failed: {e}")
        return {
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed status of all system components
    """
    start_time = datetime.utcnow()
    
    # Perform all health checks
    database_health = await check_database_health()
    redis_health = await check_redis_health()
    filesystem_health = await check_filesystem_health()
    system_info = await get_system_info()
    
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000
    
    # Determine overall health status
    overall_healthy = (
        database_health.get("status") == "healthy" and
        filesystem_health.get("status") == "healthy"
        # Redis is optional, so we don't fail if it's down
    )
    
    health_data = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": start_time.isoformat(),
        "response_time_ms": round(response_time, 2),
        "version": "0.1.0",
        "environment": "development" if settings.debug else "production",
        "services": {
            "database": database_health,
            "redis": redis_health,
            "filesystem": filesystem_health
        },
        "system": system_info,
        "configuration": {
            "debug_mode": settings.debug,
            "privacy_mode": settings.privacy_mode,
            "max_file_size_mb": round(settings.max_file_size / (1024**2), 2),
            "allowed_file_types": settings.allowed_file_types
        }
    }
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503
    
    return JSONResponse(
        content=health_data,
        status_code=status_code,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/health/simple")
async def simple_health_check():
    """
    Simple health check endpoint for basic connectivity testing
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "API is running"
    }


@router.get("/health/database")
async def database_health_check():
    """
    Database-specific health check endpoint
    """
    database_health = await check_database_health()
    status_code = 200 if database_health.get("status") == "healthy" else 503
    
    return JSONResponse(
        content={
            "service": "database",
            **database_health,
            "timestamp": datetime.utcnow().isoformat()
        },
        status_code=status_code
    )


@router.get("/health/deep")
async def deep_health_check():
    """
    Deep health check endpoint for comprehensive system validation
    """
    try:
        database_health = await check_database_health()
        redis_health = await check_redis_health()
        
        # Determine overall status
        db_ok = database_health.get("status") == "healthy"
        redis_ok = redis_health.get("status") == "healthy"
        
        overall_status = "ok" if db_ok and redis_ok else "degraded"
        
        return {
            "status": overall_status,
            "checks": {
                "db": "ok" if db_ok else f"error: {database_health.get('error', 'unknown error')}",
                "redis": "ok" if redis_ok else f"error: {redis_health.get('error', 'unknown error')}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Deep health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "checks": {
                    "db": f"error: {str(e)}",
                    "redis": f"error: {str(e)}"
                },
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )