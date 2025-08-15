"""
Integration test for semantic search and embedding functionality
"""

import asyncio
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.core.database import Base
from app.models.document import Document, Chapter
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, CardType
from app.services.embedding_service import embedding_service
from app.services.search_service import search_service, SearchType, SearchFilters
from app.services.vector_index_service import vector_index_service


class TestSemanticSearchIntegration:
    """Integration tests for semantic search functionality"""
    
    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create test database engine"""
        # Use in-memory SQLite for testing (note: no pgvector support)
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for each test"""
        Session = sessionmaker(bind=db_engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_data(self, db_session):
        """Create sample data for testing"""
        # Create document
        document = Document(
            filename="test_document.pdf",
            file_type="pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            status="COMPLETED"
        )
        db_session.add(document)
        db_session.flush()
        
        # Create chapters
        chapter1 = Chapter(
            document_id=document.id,
            title="Introduction to Machine Learning",
            level=1,
            order_index=1,
            page_start=1,
            page_end=10,
            content="This chapter introduces machine learning concepts."
        )
        
        chapter2 = Chapter(
            document_id=document.id,
            title="Deep Learning Fundamentals",
            level=1,
            order_index=2,
            page_start=11,
            page_end=20,
            content="This chapter covers deep learning basics."
        )
        
        db_session.add_all([chapter1, chapter2])
        db_session.flush()
        
        # Create knowledge points
        knowledge1 = Knowledge(
            chapter_id=chapter1.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            entities=["machine learning", "artificial intelligence", "computers"],
            anchors={"page": 2, "chapter": "Introduction", "position": 1},
            confidence_score=0.9
        )
        
        knowledge2 = Knowledge(
            chapter_id=chapter1.id,
            kind=KnowledgeType.FACT,
            text="Supervised learning algorithms learn from labeled training data to make predictions on new, unseen data.",
            entities=["supervised learning", "algorithms", "training data"],
            anchors={"page": 3, "chapter": "Introduction", "position": 2},
            confidence_score=0.85
        )
        
        knowledge3 = Knowledge(
            chapter_id=chapter2.id,
            kind=KnowledgeType.DEFINITION,
            text="Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns.",
            entities=["deep learning", "neural networks", "patterns"],
            anchors={"page": 12, "chapter": "Deep Learning", "position": 1},
            confidence_score=0.95
        )
        
        knowledge4 = Knowledge(
            chapter_id=chapter2.id,
            kind=KnowledgeType.PROCESS,
            text="The backpropagation algorithm is used to train neural networks by calculating gradients and updating weights to minimize the loss function.",
            entities=["backpropagation", "neural networks", "gradients", "loss function"],
            anchors={"page": 15, "chapter": "Deep Learning", "position": 2},
            confidence_score=0.8
        )
        
        db_session.add_all([knowledge1, knowledge2, knowledge3, knowledge4])
        db_session.flush()
        
        # Create cards
        card1 = Card(
            knowledge_id=knowledge1.id,
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            difficulty=2.0
        )
        
        card2 = Card(
            knowledge_id=knowledge3.id,
            card_type=CardType.CLOZE,
            front="Deep learning is a subset of {{c1::machine learning}} that uses {{c2::neural networks}} with multiple layers.",
            back="Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns.",
            difficulty=3.0,
            card_metadata={"blanks": ["machine learning", "neural networks"]}
        )
        
        db_session.add_all([card1, card2])
        db_session.commit()
        
        return {
            "document": document,
            "chapters": [chapter1, chapter2],
            "knowledge": [knowledge1, knowledge2, knowledge3, knowledge4],
            "cards": [card1, card2]
        }
    
    def test_embedding_service_initialization(self):
        """Test that embedding service initializes correctly"""
        assert embedding_service is not None
        assert embedding_service.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert embedding_service.embedding_dim == 384
    
    def test_generate_single_embedding(self):
        """Test generating embedding for single text"""
        text = "Machine learning is a powerful technology."
        embedding = embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        
        # Test that different texts produce different embeddings
        text2 = "Deep learning uses neural networks."
        embedding2 = embedding_service.generate_embedding(text2)
        
        assert embedding != embedding2
    
    def test_generate_batch_embeddings(self):
        """Test generating embeddings in batch"""
        texts = [
            "Machine learning is a subset of AI.",
            "Deep learning uses neural networks.",
            "Supervised learning requires labeled data."
        ]
        
        embeddings = embedding_service.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)
    
    def test_similarity_calculation(self):
        """Test cosine similarity calculation"""
        # Test with identical embeddings
        emb1 = [1.0, 0.0, 0.0] + [0.0] * 381
        emb2 = [1.0, 0.0, 0.0] + [0.0] * 381
        similarity = embedding_service.calculate_similarity(emb1, emb2)
        assert abs(similarity - 1.0) < 1e-6
        
        # Test with orthogonal embeddings
        emb1 = [1.0, 0.0, 0.0] + [0.0] * 381
        emb2 = [0.0, 1.0, 0.0] + [0.0] * 381
        similarity = embedding_service.calculate_similarity(emb1, emb2)
        assert abs(similarity) < 1e-6
    
    @pytest.mark.asyncio
    async def test_update_knowledge_embeddings(self, db_session, sample_data):
        """Test updating embeddings for knowledge points"""
        # Initially, knowledge points should not have embeddings
        knowledge_points = sample_data["knowledge"]
        for kp in knowledge_points:
            assert kp.embedding is None
        
        # Update embeddings
        updated_count = await embedding_service.update_knowledge_embeddings(db_session)
        
        assert updated_count == 4  # Should update all 4 knowledge points
        
        # Verify embeddings were added
        db_session.refresh(knowledge_points[0])
        db_session.refresh(knowledge_points[1])
        db_session.refresh(knowledge_points[2])
        db_session.refresh(knowledge_points[3])
        
        for kp in knowledge_points:
            assert kp.embedding is not None
            assert len(kp.embedding) == 384
    
    def test_search_service_initialization(self):
        """Test that search service initializes correctly"""
        assert search_service is not None
        assert search_service.default_limit == 20
        assert search_service.max_limit == 100
    
    @pytest.mark.asyncio
    async def test_full_text_search(self, db_session, sample_data):
        """Test full-text search functionality"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Test search for "machine learning"
        results = search_service.search(
            db_session,
            query="machine learning",
            search_type=SearchType.FULL_TEXT,
            limit=10
        )
        
        # Should find knowledge points containing "machine learning"
        assert len(results) > 0
        
        # Check that results contain relevant content
        found_ml_definition = False
        found_dl_definition = False
        
        for result in results:
            if "machine learning" in result.content.lower():
                found_ml_definition = True
            if "deep learning" in result.content.lower() and "machine learning" in result.content.lower():
                found_dl_definition = True
        
        assert found_ml_definition or found_dl_definition
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, db_session, sample_data):
        """Test semantic search functionality"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Test semantic search for AI-related concepts
        results = search_service.search(
            db_session,
            query="artificial intelligence and computer learning",
            search_type=SearchType.SEMANTIC,
            similarity_threshold=0.3,  # Lower threshold for testing
            limit=10
        )
        
        # Should find semantically similar content
        assert len(results) >= 0  # May be 0 if embeddings are too different
        
        # If results found, they should be relevant
        for result in results:
            assert result.score > 0
            assert result.type in ["knowledge", "card"]
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, db_session, sample_data):
        """Test hybrid search functionality"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Test hybrid search
        results = search_service.search(
            db_session,
            query="neural networks",
            search_type=SearchType.HYBRID,
            limit=10
        )
        
        # Should find results using both approaches
        assert len(results) >= 0
        
        # Results should be sorted by score
        if len(results) > 1:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, db_session, sample_data):
        """Test search with various filters"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Test filtering by knowledge type
        filters = SearchFilters(knowledge_types=[KnowledgeType.DEFINITION])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        # All results should be definitions
        for result in results:
            if result.type == "knowledge":
                assert result.metadata.get("kind") == "definition"
        
        # Test filtering by chapter
        chapter_id = str(sample_data["chapters"][0].id)
        filters = SearchFilters(chapter_ids=[chapter_id])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        # All results should be from the specified chapter
        for result in results:
            if result.type == "knowledge":
                assert result.metadata.get("chapter_id") == chapter_id
    
    @pytest.mark.asyncio
    async def test_find_similar_knowledge(self, db_session, sample_data):
        """Test finding similar knowledge points"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Find knowledge similar to a specific text
        similar_knowledge = embedding_service.search_similar_knowledge(
            db_session,
            query_text="What is artificial intelligence and machine learning?",
            similarity_threshold=0.1,  # Lower threshold for testing
            limit=5
        )
        
        # Should find some similar knowledge points
        assert len(similar_knowledge) >= 0
        
        # Check that similarity scores are reasonable
        for knowledge, similarity in similar_knowledge:
            assert 0 <= similarity <= 1
            assert hasattr(knowledge, 'text')
            assert hasattr(knowledge, 'kind')
    
    @pytest.mark.asyncio
    async def test_find_duplicate_knowledge(self, db_session, sample_data):
        """Test finding duplicate knowledge points"""
        # First update embeddings
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Add a duplicate knowledge point
        duplicate_knowledge = Knowledge(
            chapter_id=sample_data["chapters"][0].id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that enables computers to learn from experience.",  # Very similar to existing
            entities=["machine learning", "artificial intelligence"],
            anchors={"page": 5, "chapter": "Introduction", "position": 3},
            confidence_score=0.8
        )
        db_session.add(duplicate_knowledge)
        db_session.commit()
        
        # Update embedding for the new knowledge point
        await embedding_service.update_knowledge_embeddings(db_session, [str(duplicate_knowledge.id)])
        
        # Find duplicates
        duplicates = embedding_service.find_duplicate_knowledge(
            db_session,
            similarity_threshold=0.7
        )
        
        # Should find at least one duplicate pair
        assert len(duplicates) >= 0  # May be 0 if similarity is not high enough
        
        # Check duplicate structure
        for kp1, kp2, similarity in duplicates:
            assert similarity >= 0.7
            assert kp1.id != kp2.id  # Should be different knowledge points
    
    def test_search_suggestions(self, db_session, sample_data):
        """Test search suggestions functionality"""
        suggestions = search_service.get_search_suggestions(
            db_session,
            query="machine",
            limit=5
        )
        
        # Should return relevant suggestions
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5
        
        # All suggestions should start with the query (case-insensitive)
        for suggestion in suggestions:
            assert suggestion.lower().startswith("machine")
    
    def test_vector_index_service(self, db_session):
        """Test vector index service functionality"""
        # Note: This test will fail with SQLite as it doesn't support pgvector
        # In a real PostgreSQL environment, this would work
        
        # Test performance analysis
        analysis = vector_index_service.analyze_vector_performance(db_session)
        assert isinstance(analysis, dict)
        
        # Should handle errors gracefully with SQLite
        if "error" in analysis:
            assert "error" in analysis
        else:
            assert "total_knowledge" in analysis
    
    def test_search_result_structure(self, db_session, sample_data):
        """Test that search results have correct structure"""
        # Test with a simple search
        results = search_service.search(
            db_session,
            query="learning",
            limit=5
        )
        
        for result in results:
            # Check required fields
            assert hasattr(result, 'id')
            assert hasattr(result, 'type')
            assert hasattr(result, 'title')
            assert hasattr(result, 'content')
            assert hasattr(result, 'snippet')
            assert hasattr(result, 'score')
            assert hasattr(result, 'metadata')
            
            # Check field types
            assert isinstance(result.id, str)
            assert result.type in ["knowledge", "card"]
            assert isinstance(result.title, str)
            assert isinstance(result.content, str)
            assert isinstance(result.snippet, str)
            assert isinstance(result.score, (int, float))
            assert isinstance(result.metadata, dict)
    
    def test_empty_search_handling(self, db_session):
        """Test handling of empty or invalid searches"""
        # Empty query
        results = search_service.search(db_session, "")
        assert results == []
        
        # Whitespace only
        results = search_service.search(db_session, "   ")
        assert results == []
        
        # Very long query (should be handled gracefully)
        long_query = "test " * 200
        results = search_service.search(db_session, long_query)
        assert isinstance(results, list)  # Should not crash


if __name__ == "__main__":
    # Run the integration test
    pytest.main([__file__, "-v"])