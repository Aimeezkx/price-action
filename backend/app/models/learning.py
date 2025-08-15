"""
Learning and flashcard models
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Float, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from datetime import datetime

from .base import BaseModel


class CardType(str, Enum):
    """Types of flashcards"""
    QA = "qa"
    CLOZE = "cloze"
    IMAGE_HOTSPOT = "image_hotspot"


class Card(BaseModel):
    """Flashcard model"""
    
    __tablename__ = "cards"
    
    knowledge_id = Column(UUID(as_uuid=True), ForeignKey("knowledge.id"), nullable=False, index=True)
    card_type = Column(SQLEnum(CardType), nullable=False, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    difficulty = Column(Float, default=1.0, nullable=False)
    card_metadata = Column(JSON, default=dict)  # hotspots, blanks, etc.
    
    # Relationships
    knowledge = relationship("Knowledge", back_populates="cards")
    srs_records = relationship("SRS", back_populates="card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Card(id={self.id}, type='{self.card_type}', difficulty={self.difficulty})>"


class SRS(BaseModel):
    """Spaced Repetition System model"""
    
    __tablename__ = "srs"
    
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # For future multi-user support
    ease_factor = Column(Float, default=2.5, nullable=False)
    interval = Column(Integer, default=1, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    due_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_reviewed = Column(DateTime, nullable=True)
    last_grade = Column(Integer, nullable=True)  # 0-5 scale
    
    # Relationships
    card = relationship("Card", back_populates="srs_records")
    
    def __repr__(self):
        return f"<SRS(id={self.id}, ease_factor={self.ease_factor}, interval={self.interval}, due_date={self.due_date})>"