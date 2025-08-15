"""
Document-related models
"""

from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import uuid

from .base import BaseModel


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Document model"""
    
    __tablename__ = "documents"
    
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False, index=True)
    doc_metadata = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    chapters = relationship("Chapter", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Chapter(BaseModel):
    """Chapter model"""
    
    __tablename__ = "chapters"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    level = Column(Integer, nullable=False, default=1)
    order_index = Column(Integer, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chapters")
    figures = relationship("Figure", back_populates="chapter", cascade="all, delete-orphan")
    knowledge_points = relationship("Knowledge", back_populates="chapter", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chapter(id={self.id}, title='{self.title}', level={self.level})>"


class Figure(BaseModel):
    """Figure/Image model"""
    
    __tablename__ = "figures"
    
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    caption = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    bbox = Column(JSON, nullable=True)  # {x, y, width, height}
    image_format = Column(String(10), nullable=True)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="figures")
    
    def __repr__(self):
        return f"<Figure(id={self.id}, caption='{self.caption[:50] if self.caption else 'No caption'}')>"