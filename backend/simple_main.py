from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Document Learning App API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document Learning App API", "status": "running", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/documents")
async def get_documents():
    return {"documents": [], "message": "API is working"}

@app.post("/api/ingest")
async def ingest_document():
    return {"message": "Upload endpoint is working", "status": "success"}