"""
Document Learning App - FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import init_db
from app.core.config import settings
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.reviews import router as reviews_router
from app.api.export import router as export_router
from app.api.monitoring import router as monitoring_router
from app.api.sync import router as sync_router
from app.middleware.performance import PerformanceMiddleware
from app.utils.logging import setup_privacy_logging, SecurityLogger

# Configure privacy-aware logging
setup_privacy_logging()
logger = SecurityLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.logger.info("Starting Document Learning App API...")
    logger.log_security_event(
        "application_startup",
        {
            "privacy_mode": settings.privacy_mode,
            "anonymize_logs": settings.anonymize_logs,
            "version": "0.1.0"
        },
        "INFO"
    )
    
    try:
        await init_db()
        logger.logger.info("Database initialized successfully")
    except Exception as e:
        logger.log_error(e, {"component": "database_initialization"})
        raise
    
    yield
    
    # Shutdown
    logger.logger.info("Shutting down Document Learning App API...")
    logger.log_security_event("application_shutdown", {}, "INFO")


app = FastAPI(
    title="Document Learning App API",
    description="API for document-based learning with automated content extraction",
    version="0.1.0",
    lifespan=lifespan,
)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(reviews_router)
app.include_router(export_router)
app.include_router(monitoring_router)
app.include_router(sync_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Document Learning App API", 
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app, 
        host=settings.api_host, 
        port=settings.api_port,
        reload=settings.debug
    )