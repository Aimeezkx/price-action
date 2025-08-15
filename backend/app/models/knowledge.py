"""
Knowledge extraction models
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Float, ARRAY, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from enum import Enum

from .base import BaseModel


class KnowledgeType(str, Enum):
    """Types of knowledge points"""
    DEFINITION = "definition"
    FACT = "fact"
    THEOREM = "theorem"
    PROCESS = "process"
    EXAMPLE = "example"
    CONCEPT = "concept"


class Knowledge(BaseModel):
    """Knowledge point model"""
    
    __tablename__ = "knowledge"
    
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False, index=True)
    kind = Column(SQLEnum(KnowledgeType), nullable=False, index=True)
    text = Column(Text, nullable=False)
    entities = Column(ARRAY(String), default=list)
    anchors = Column(JSON, default=dict)  # {page, chapter, position}
    embedding = Column(Vector(384), nullable=True)  # sentence-transformers embedding dimension
    confidence_score = Column(Float, default=1.0)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="knowledge_points")
    cards = relationship("Card", back_populates="knowledge", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Knowledge(id={self.id}, kind='{self.kind}', text='{self.text[:50]}...')>"