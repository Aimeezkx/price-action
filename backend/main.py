"""
Document Learning App - FastAPI Backend
"""
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
import logging
import traceback

# Import routers
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.queue import router as queue_router
from app.routes.cards import router as cards_router

# Import database initialization
from app.core.database import init_db, create_tables

# Ensure upload directory exists and is consistent with Docker volume
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Document Learning App API",
    description="API for document learning and flashcard generation",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await init_db()
        await create_tables()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.warning(f"Database initialization failed: {e}")
        logging.warning("Application will continue without database connection")

# Configure CORS using environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers for better error reporting
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions with detailed logging"""
    # Print full traceback for debugging
    traceback.print_exc()
    
    # Log the error
    logging.error(f"Unhandled exception on {request.url.path}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )

# Include routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(documents_router, tags=["documents"])
app.include_router(queue_router, tags=["queue"])
app.include_router(cards_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Document Learning App API", "status": "running", "version": "0.1.0"}

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "Document Learning App API", "status": "running", "version": "0.1.0"}

@app.post("/api/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Simple test upload endpoint"""
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "message": "Upload test successful"
    }

# Document endpoints are now handled by the documents router



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)