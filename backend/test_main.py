"""
Test version of main.py with real PDF processing
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from pathlib import Path
import logging
from improved_pdf_processor import ImprovedPDFProcessor

# Simple in-memory storage for testing
documents_db = {}
chapters_db = {}
knowledge_points_db = {}
cards_db = {}
document_counter = 0

# Initialize improved PDF processor
pdf_processor = ImprovedPDFProcessor()

app = FastAPI(
    title="Document Learning App API (Test)",
    description="Test API for document-based learning",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Document Learning App API (Test)", 
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    global document_counter
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx', '.md')):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Save file
    document_counter += 1
    doc_id = document_counter
    file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate PDF
        if file.filename.lower().endswith('.pdf'):
            validation = pdf_processor.validate_file(str(file_path))
            if not validation['valid']:
                os.remove(file_path)  # Clean up
                raise HTTPException(status_code=400, detail=validation['error'])
            
            page_count = validation['page_count']
            file_size = validation['file_size']
            
            # Process PDF with improved methods
            text_result = pdf_processor.extract_text_improved(str(file_path))
            if text_result['success']:
                # Extract chapters and knowledge points with improved algorithms
                chapters = pdf_processor.extract_chapters_improved(text_result['full_text'])
                knowledge_points = pdf_processor.extract_knowledge_points_improved(text_result['full_text'])
                
                # Store in databases
                chapters_db[doc_id] = chapters
                knowledge_points_db[doc_id] = knowledge_points
                
                status = "processed"
            else:
                status = "processing_failed"
                page_count = 0
        else:
            page_count = 1
            file_size = os.path.getsize(file_path)
            status = "uploaded"
        
        # Store document info
        documents_db[doc_id] = {
            "id": doc_id,
            "title": file.filename,
            "filename": file.filename,
            "file_path": str(file_path),
            "status": status,
            "page_count": page_count,
            "file_size": file_size
        }
        
        return documents_db[doc_id]
        
    except Exception as e:
        # Clean up file if it exists
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int):
    """Get document details"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return documents_db[doc_id]

@app.get("/api/documents/{doc_id}/chapters")
async def get_chapters(doc_id: int):
    """Get document chapters"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return chapters_db.get(doc_id, [])

@app.get("/api/documents/{doc_id}/knowledge-points")
async def get_knowledge_points(doc_id: int):
    """Get knowledge points"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return knowledge_points_db.get(doc_id, [])

@app.post("/api/documents/{doc_id}/generate-cards")
async def generate_cards(doc_id: int):
    """Generate flashcards"""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chapters = chapters_db.get(doc_id, [])
    knowledge_points = knowledge_points_db.get(doc_id, [])
    
    cards_result = pdf_processor.generate_flashcards_improved(chapters, knowledge_points)
    cards_db[doc_id] = cards_result['cards']
    
    return {"count": cards_result['count'], "message": "Cards generated successfully"}

@app.get("/api/search")
async def search(q: str):
    """Search documents (mock)"""
    # Mock search results
    return [
        {"id": 1, "title": f"Result for '{q}'", "snippet": f"Mock result containing {q}"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)