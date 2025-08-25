"""
Knowledge extraction models
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from .base import BaseModel, UUID
from app.core.config import settings

# Conditional imports for PostgreSQL-specific features
IS_POSTGRESQL = settings.database_url.startswith('postgresql://')

if IS_POSTGRESQL:
    try:
        from sqlalchemy import ARRAY
        from pgvector.sqlalchemy import Vector
        HAS_PGVECTOR = True
    except ImportError:
        HAS_PGVECTOR = False
        ARRAY = None
        Vector = None
else:
    HAS_PGVECTOR = False
    ARRAY = None
    Vector = None


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
    
    chapter_id = Column(UUID(), ForeignKey("chapters.id"), nullable=False, index=True)
    kind = Column(SQLEnum(KnowledgeType), nullable=False, index=True)
    text = Column(Text, nullable=False)
    entities = Column(ARRAY(String) if IS_POSTGRESQL and ARRAY else JSON, default=list)
    anchors = Column(JSON, default=dict)  # {page, chapter, position}
    embedding = Column(Vector(384) if IS_POSTGRESQL and Vector else JSON, nullable=True)  # sentence-transformers embedding dimension
    confidence_score = Column(Float, default=1.0)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="knowledge_points")
    cards = relationship("Card", back_populates="knowledge", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Knowledge(id={self.id}, kind='{self.kind}', text='{self.text[:50]}...')>"