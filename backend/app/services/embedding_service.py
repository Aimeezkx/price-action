"""
Embedding service for semantic search functionality
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pgvector.sqlalchemy import Vector

from ..models.knowledge import Knowledge
from ..models.document import Chapter
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.embedding_dim = 384
        self._model: Optional[SentenceTransformer] = None
        
    def _get_model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
            
        try:
            model = self._get_model()
            embedding = model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return [0.0] * self.embedding_dim
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        try:
            model = self._get_model()
            embeddings = model.encode(texts, convert_to_tensor=False, batch_size=32)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * self.embedding_dim] * len(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def update_knowledge_embeddings(self, db: Session, knowledge_ids: Optional[List[str]] = None) -> int:
        """
        Update embeddings for knowledge points
        
        Args:
            db: Database session
            knowledge_ids: Optional list of specific knowledge IDs to update
            
        Returns:
            Number of knowledge points updated
        """
        try:
            # Build query
            query = db.query(Knowledge)
            if knowledge_ids:
                query = query.filter(Knowledge.id.in_(knowledge_ids))
            else:
                # Only update knowledge points without embeddings
                query = query.filter(Knowledge.embedding.is_(None))
            
            knowledge_points = query.all()
            
            if not knowledge_points:
                logger.info("No knowledge points to update")
                return 0
            
            # Extract texts for batch processing
            texts = [kp.text for kp in knowledge_points]
            
            # Generate embeddings in batch
            logger.info(f"Generating embeddings for {len(texts)} knowledge points")
            embeddings = self.generate_embeddings_batch(texts)
            
            # Update knowledge points with embeddings
            updated_count = 0
            for kp, embedding in zip(knowledge_points, embeddings):
                kp.embedding = embedding
                updated_count += 1
            
            db.commit()
            logger.info(f"Updated embeddings for {updated_count} knowledge points")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update knowledge embeddings: {e}")
            db.rollback()
            return 0
    
    def search_similar_knowledge(
        self, 
        db: Session, 
        query_text: str, 
        similarity_threshold: float = 0.7,
        limit: int = 10,
        chapter_ids: Optional[List[str]] = None
    ) -> List[Tuple[Knowledge, float]]:
        """
        Search for similar knowledge points using vector similarity
        
        Args:
            db: Database session
            query_text: Text to search for
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results
            chapter_ids: Optional list of chapter IDs to filter by
            
        Returns:
            List of tuples (Knowledge, similarity_score)
        """
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            
            # Build SQL query with vector similarity
            query = db.query(Knowledge).filter(Knowledge.embedding.isnot(None))
            
            # Filter by chapters if specified
            if chapter_ids:
                query = query.filter(Knowledge.chapter_id.in_(chapter_ids))
            
            # Add similarity calculation and filtering
            similarity_expr = Knowledge.embedding.cosine_distance(query_embedding)
            query = query.add_columns(similarity_expr.label('distance'))
            query = query.filter(similarity_expr < (1 - similarity_threshold))
            query = query.order_by(similarity_expr)
            query = query.limit(limit)
            
            results = query.all()
            
            # Convert distance to similarity and return
            similar_knowledge = []
            for knowledge, distance in results:
                similarity = 1 - distance  # Convert distance to similarity
                similar_knowledge.append((knowledge, similarity))
            
            logger.info(f"Found {len(similar_knowledge)} similar knowledge points")
            return similar_knowledge
            
        except Exception as e:
            logger.error(f"Failed to search similar knowledge: {e}")
            return []
    
    def find_duplicate_knowledge(
        self, 
        db: Session, 
        similarity_threshold: float = 0.9,
        chapter_ids: Optional[List[str]] = None
    ) -> List[Tuple[Knowledge, Knowledge, float]]:
        """
        Find duplicate knowledge points based on semantic similarity
        
        Args:
            db: Database session
            similarity_threshold: Minimum similarity to consider as duplicate
            chapter_ids: Optional list of chapter IDs to check
            
        Returns:
            List of tuples (knowledge1, knowledge2, similarity_score)
        """
        try:
            # Get all knowledge points with embeddings
            query = db.query(Knowledge).filter(Knowledge.embedding.isnot(None))
            if chapter_ids:
                query = query.filter(Knowledge.chapter_id.in_(chapter_ids))
            
            knowledge_points = query.all()
            
            if len(knowledge_points) < 2:
                return []
            
            duplicates = []
            
            # Compare each pair of knowledge points
            for i in range(len(knowledge_points)):
                for j in range(i + 1, len(knowledge_points)):
                    kp1, kp2 = knowledge_points[i], knowledge_points[j]
                    
                    similarity = self.calculate_similarity(kp1.embedding, kp2.embedding)
                    
                    if similarity >= similarity_threshold:
                        duplicates.append((kp1, kp2, similarity))
            
            # Sort by similarity (highest first)
            duplicates.sort(key=lambda x: x[2], reverse=True)
            
            logger.info(f"Found {len(duplicates)} potential duplicates")
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find duplicate knowledge: {e}")
            return []


# Global embedding service instance
embedding_service = EmbeddingService()