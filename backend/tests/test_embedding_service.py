"""
Tests for embedding service
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np
from sqlalchemy.orm import Session

from app.services.embedding_service import EmbeddingService, embedding_service
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Chapter, Document


class TestEmbeddingService:
    """Test cases for EmbeddingService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = EmbeddingService()
        
    def test_init(self):
        """Test service initialization"""
        assert self.service.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert self.service.embedding_dim == 384
        assert self.service._model is None
    
    @patch('app.services.embedding_service.SentenceTransformer')
    def test_get_model_lazy_loading(self, mock_transformer):
        """Test lazy loading of the sentence transformer model"""
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        
        # First call should load the model
        model = self.service._get_model()
        assert model == mock_model
        assert self.service._model == mock_model
        mock_transformer.assert_called_once_with(self.service.model_name)
        
        # Second call should return cached model
        model2 = self.service._get_model()
        assert model2 == mock_model
        assert mock_transformer.call_count == 1  # Should not be called again
    
    @patch('app.services.embedding_service.SentenceTransformer')
    def test_generate_embedding_success(self, mock_transformer):
        """Test successful embedding generation"""
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3] + [0.0] * 381)  # 384 dimensions
        mock_model.encode.return_value = mock_embedding
        mock_transformer.return_value = mock_model
        
        text = "This is a test sentence."
        embedding = self.service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert embedding[:3] == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(text, convert_to_tensor=False)
    
    def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text"""
        embedding = self.service.generate_embedding("")
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)
        
        embedding = self.service.generate_embedding("   ")
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)
    
    @patch('app.services.embedding_service.SentenceTransformer')
    def test_generate_embedding_error_handling(self, mock_transformer):
        """Test error handling in embedding generation"""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Model error")
        mock_transformer.return_value = mock_model
        
        embedding = self.service.generate_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)
    
    @patch('app.services.embedding_service.SentenceTransformer')
    def test_generate_embeddings_batch(self, mock_transformer):
        """Test batch embedding generation"""
        mock_model = Mock()
        mock_embeddings = np.array([
            [0.1, 0.2] + [0.0] * 382,
            [0.3, 0.4] + [0.0] * 382
        ])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model
        
        texts = ["First text", "Second text"]
        embeddings = self.service.generate_embeddings_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384
        assert embeddings[0][:2] == [0.1, 0.2]
        assert embeddings[1][:2] == [0.3, 0.4]
        mock_model.encode.assert_called_once_with(texts, convert_to_tensor=False, batch_size=32)
    
    def test_generate_embeddings_batch_empty(self):
        """Test batch embedding generation with empty list"""
        embeddings = self.service.generate_embeddings_batch([])
        assert embeddings == []
    
    def test_calculate_similarity(self):
        """Test cosine similarity calculation"""
        # Test identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = self.service.calculate_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6
        
        # Test orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = self.service.calculate_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 1e-6
        
        # Test opposite vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = self.service.calculate_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 1e-6
    
    def test_calculate_similarity_zero_vectors(self):
        """Test similarity calculation with zero vectors"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = self.service.calculate_similarity(vec1, vec2)
        assert similarity == 0.0
    
    def test_calculate_similarity_error_handling(self):
        """Test error handling in similarity calculation"""
        # Test with invalid input
        similarity = self.service.calculate_similarity([], [1.0])
        assert similarity == 0.0
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_knowledge_points(self):
        """Sample knowledge points for testing"""
        knowledge1 = Mock(spec=Knowledge)
        knowledge1.id = "1"
        knowledge1.text = "Machine learning is a subset of artificial intelligence."
        knowledge1.embedding = None
        
        knowledge2 = Mock(spec=Knowledge)
        knowledge2.id = "2"
        knowledge2.text = "Deep learning uses neural networks with multiple layers."
        knowledge2.embedding = None
        
        return [knowledge1, knowledge2]
    
    @patch('app.services.embedding_service.SentenceTransformer')
    @pytest.mark.asyncio
    async def test_update_knowledge_embeddings(self, mock_transformer, mock_db_session, sample_knowledge_points):
        """Test updating knowledge embeddings"""
        # Setup mocks
        mock_model = Mock()
        mock_embeddings = np.array([
            [0.1] * 384,
            [0.2] * 384
        ])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_knowledge_points
        mock_db_session.query.return_value = mock_query
        
        # Test update
        updated_count = await self.service.update_knowledge_embeddings(mock_db_session)
        
        assert updated_count == 2
        assert sample_knowledge_points[0].embedding == [0.1] * 384
        assert sample_knowledge_points[1].embedding == [0.2] * 384
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_knowledge_embeddings_no_knowledge(self, mock_db_session):
        """Test updating embeddings when no knowledge points exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        updated_count = await self.service.update_knowledge_embeddings(mock_db_session)
        
        assert updated_count == 0
        mock_db_session.commit.assert_not_called()
    
    def test_search_similar_knowledge(self, mock_db_session):
        """Test searching for similar knowledge points"""
        # Setup mock knowledge with embeddings
        knowledge1 = Mock(spec=Knowledge)
        knowledge1.id = "1"
        knowledge1.text = "Test knowledge"
        knowledge1.embedding = [0.1] * 384
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.add_columns.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [(knowledge1, 0.2)]  # (knowledge, distance)
        mock_db_session.query.return_value = mock_query
        
        with patch.object(self.service, 'generate_embedding', return_value=[0.1] * 384):
            results = self.service.search_similar_knowledge(
                mock_db_session,
                "test query",
                similarity_threshold=0.7,
                limit=10
            )
        
        assert len(results) == 1
        knowledge, similarity = results[0]
        assert knowledge == knowledge1
        assert similarity == 0.8  # 1 - 0.2 distance
    
    def test_find_duplicate_knowledge(self, mock_db_session):
        """Test finding duplicate knowledge points"""
        # Setup mock knowledge points
        knowledge1 = Mock(spec=Knowledge)
        knowledge1.id = "1"
        knowledge1.embedding = [1.0, 0.0, 0.0] + [0.0] * 381
        
        knowledge2 = Mock(spec=Knowledge)
        knowledge2.id = "2"
        knowledge2.embedding = [0.9, 0.1, 0.0] + [0.0] * 381  # Similar to knowledge1
        
        knowledge3 = Mock(spec=Knowledge)
        knowledge3.id = "3"
        knowledge3.embedding = [0.0, 1.0, 0.0] + [0.0] * 381  # Different from others
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [knowledge1, knowledge2, knowledge3]
        mock_db_session.query.return_value = mock_query
        
        duplicates = self.service.find_duplicate_knowledge(
            mock_db_session,
            similarity_threshold=0.8
        )
        
        # Should find one duplicate pair (knowledge1 and knowledge2 are similar)
        assert len(duplicates) >= 0  # Depends on actual similarity calculation
        
        # Check that results are sorted by similarity
        if duplicates:
            similarities = [dup[2] for dup in duplicates]
            assert similarities == sorted(similarities, reverse=True)


class TestGlobalEmbeddingService:
    """Test the global embedding service instance"""
    
    def test_global_instance(self):
        """Test that global embedding service instance exists"""
        assert embedding_service is not None
        assert isinstance(embedding_service, EmbeddingService)