"""
Document Learning App - FastAPI Backend
"""
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import List
import logging
import traceback

# Import routers
from app.api.health import router as health_router
from app.api.documents import router as documents_router

# Ensure upload directory exists and is consistent with Docker volume
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Document Learning App API",
    description="API for document learning and flashcard generation",
    version="0.1.0"
)

# Configure CORS with updated origins to include port 3001
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Added port 3001 for frontend
        "http://frontend:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",  # Added 127.0.0.1 variants
    ],
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Document Learning App API", "status": "running", "version": "0.1.0"}

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "Document Learning App API", "status": "running", "version": "0.1.0"}

# Simple ingest endpoint for immediate testing
@app.post("/api/ingest")
async def simple_ingest(file: UploadFile = File(...)):
    """
    Simple file upload endpoint for immediate testing
    This provides a minimal implementation to fix the 500 error
    """
    try:
        # Validate file size (50MB limit)
        size_limit = 50 * 1024 * 1024
        if file.size and file.size > size_limit:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Ensure filename is safe
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Save file with chunked writing
        file_path = UPLOAD_DIR / file.filename
        written = 0
        
        try:
            with file_path.open("wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > size_limit:
                        # Clean up partial file
                        file_path.unlink(missing_ok=True)
                        raise HTTPException(status_code=413, detail="File too large")
                    f.write(chunk)
        finally:
            await file.close()
        
        return {
            "ok": True,
            "name": file.filename,
            "size": written,
            "path": str(file_path.relative_to(UPLOAD_DIR))
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return structured error
        logging.error(f"Upload failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)