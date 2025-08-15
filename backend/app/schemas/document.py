"""
Document-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.document import ProcessingStatus


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, md)")


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    file_path: str = Field(..., description="Path to uploaded file")
    file_size: int = Field(..., description="File size in bytes")


class DocumentResponse(DocumentBase):
    """Schema for document API responses"""
    id: UUID
    file_size: int
    status: ProcessingStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentStatusUpdate(BaseModel):
    """Schema for updating document status"""
    status: ProcessingStatus
    error_message: Optional[str] = None