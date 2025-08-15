"""
Integration test for enhanced search and filtering functionality (Task 16)
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


class TestSearchFilteringIntegration:
    """Integration tests for enhanced search and filtering functionality"""
    
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
    def comprehensive_sample_data(self, db_session):
        """Create comprehensive sample data for testing"""
        # Create document
        document = Document(
            filename="comprehensive_test.pdf",
            file_type="pdf",
            file_path="/tmp/test.pdf",
            file_size=2048,
            status="COMPLETED"
        )
        db_session.add(document)
        db_session.flush()
        
        # Create chapters
        chapters = []
        for i in range(3):
            chapter = Chapter(
                document_id=document.id,
                title=f"Chapter {i+1}: Advanced Topics",
                level=1,
                order_index=i+1,
                page_start=i*10 + 1,
                page_end=(i+1)*10,
                content=f"This chapter covers advanced topics in area {i+1}."
            )
            chapters.append(chapter)
            db_session.add(chapter)
        
        db_session.flush()
        
        # Create diverse knowledge points
        knowledge_points = []
        
        # Chapter 1 - Machine Learning
        ml_knowledge = [
            Knowledge(
                chapter_id=chapters[0].id,
                kind=KnowledgeType.DEFINITION,
                text="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
                entities=["machine learning", "data analysis", "artificial intelligence", "patterns"],
                anchors={"page": 1, "chapter": "Chapter 1", "position": 1},
                confidence_score=0.95
            ),
            Knowledge(
                chapter_id=chapters[0].id,
                kind=KnowledgeType.FACT,
                text="Supervised learning algorithms require labeled training data to learn patterns and make predictions on new, unseen data.",
                entities=["supervised learning", "labeled training data", "predictions"],
                anchors={"page": 2, "chapter": "Chapter 1", "position": 2},
                confidence_score=0.9
            ),
            Knowledge(
                chapter_id=chapters[0].id,
                kind=KnowledgeType.PROCESS,
                text="The machine learning workflow typically involves data collection, data preprocessing, model selection, training, evaluation, and deployment.",
                entities=["workflow", "data collection", "preprocessing", "model selection", "training", "evaluation", "deployment"],
                anchors={"page": 3, "chapter": "Chapter 1", "position": 3},
                confidence_score=0.85
            )
        ]
        
        # Chapter 2 - Deep Learning
        dl_knowledge = [
            Knowledge(
                chapter_id=chapters[1].id,
                kind=KnowledgeType.DEFINITION,
                text="Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to model and understand complex patterns in data.",
                entities=["deep learning", "neural networks", "multiple layers", "complex patterns"],
                anchors={"page": 11, "chapter": "Chapter 2", "position": 1},
                confidence_score=0.92
            ),
            Knowledge(
                chapter_id=chapters[1].id,
                kind=KnowledgeType.THEOREM,
                text="The Universal Approximation Theorem states that a feedforward network with a single hidden layer containing a finite number of neurons can approximate continuous functions on compact subsets of Rn.",
                entities=["Universal Approximation Theorem", "feedforward network", "hidden layer", "continuous functions"],
                anchors={"page": 12, "chapter": "Chapter 2", "position": 2},
                confidence_score=0.88
            ),
            Knowledge(
                chapter_id=chapters[1].id,
                kind=KnowledgeType.EXAMPLE,
                text="Convolutional Neural Networks (CNNs) are particularly effective for image recognition tasks. For example, ResNet-50 achieved 92.9% top-5 accuracy on ImageNet dataset.",
                entities=["Convolutional Neural Networks", "CNNs", "image recognition", "ResNet-50", "ImageNet"],
                anchors={"page": 13, "chapter": "Chapter 2", "position": 3},
                confidence_score=0.87
            )
        ]
        
        # Chapter 3 - Natural Language Processing
        nlp_knowledge = [
            Knowledge(
                chapter_id=chapters[2].id,
                kind=KnowledgeType.DEFINITION,
                text="Natural Language Processing (NLP) is a subfield of artificial intelligence that focuses on the interaction between computers and human language, enabling machines to understand, interpret, and generate human language.",
                entities=["Natural Language Processing", "NLP", "artificial intelligence", "human language", "computers"],
                anchors={"page": 21, "chapter": "Chapter 3", "position": 1},
                confidence_score=0.93
            ),
            Knowledge(
                chapter_id=chapters[2].id,
                kind=KnowledgeType.CONCEPT,
                text="Transformer architecture revolutionized NLP by introducing self-attention mechanisms that allow models to process sequences in parallel rather than sequentially.",
                entities=["Transformer", "self-attention", "sequences", "parallel processing"],
                anchors={"page": 22, "chapter": "Chapter 3", "position": 2},
                confidence_score=0.91
            )
        ]
        
        all_knowledge = ml_knowledge + dl_knowledge + nlp_knowledge
        knowledge_points.extend(all_knowledge)
        
        for kp in knowledge_points:
            db_session.add(kp)
        
        db_session.flush()
        
        # Create diverse cards
        cards = []
        
        # QA Cards
        qa_cards = [
            Card(
                knowledge_id=ml_knowledge[0].id,
                card_type=CardType.QA,
                front="What is machine learning?",
                back="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
                difficulty=2.0
            ),
            Card(
                knowledge_id=dl_knowledge[0].id,
                card_type=CardType.QA,
                front="What is deep learning?",
                back="Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to model and understand complex patterns in data.",
                difficulty=3.0
            )
        ]
        
        # Cloze Cards
        cloze_cards = [
            Card(
                knowledge_id=ml_knowledge[1].id,
                card_type=CardType.CLOZE,
                front="{{c1::Supervised learning}} algorithms require {{c2::labeled training data}} to learn patterns.",
                back="Supervised learning algorithms require labeled training data to learn patterns and make predictions on new, unseen data.",
                difficulty=2.5,
                card_metadata={"blanks": ["Supervised learning", "labeled training data"]}
            ),
            Card(
                knowledge_id=nlp_knowledge[1].id,
                card_type=CardType.CLOZE,
                front="{{c1::Transformer}} architecture uses {{c2::self-attention}} mechanisms.",
                back="Transformer architecture revolutionized NLP by introducing self-attention mechanisms that allow models to process sequences in parallel rather than sequentially.",
                difficulty=4.0,
                card_metadata={"blanks": ["Transformer", "self-attention"]}
            )
        ]
        
        # Image Hotspot Cards
        hotspot_cards = [
            Card(
                knowledge_id=dl_knowledge[2].id,
                card_type=CardType.IMAGE_HOTSPOT,
                front="cnn_architecture.png",
                back="Convolutional Neural Networks (CNNs) are particularly effective for image recognition tasks.",
                difficulty=3.5,
                card_metadata={
                    "hotspots": [
                        {"x": 100, "y": 50, "width": 80, "height": 30, "label": "Convolutional Layer"},
                        {"x": 200, "y": 50, "width": 60, "height": 30, "label": "Pooling Layer"}
                    ]
                }
            )
        ]
        
        all_cards = qa_cards + cloze_cards + hotspot_cards
        cards.extend(all_cards)
        
        for card in cards:
            db_session.add(card)
        
        db_session.commit()
        
        return {
            "document": document,
            "chapters": chapters,
            "knowledge": knowledge_points,
            "cards": cards
        }
    
    @pytest.mark.asyncio
    async def test_full_text_search_with_highlighting(self, db_session, comprehensive_sample_data):
        """Test full-text search with highlighting functionality"""
        # Update embeddings first
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Test search with highlighting
        results = search_service.search(
            db_session,
            query="machine learning artificial intelligence",
            search_type=SearchType.FULL_TEXT,
            limit=10
        )
        
        assert len(results) > 0
        
        # Check that results have highlights
        found_highlighted = False
        for result in results:
            if result.highlights:
                found_highlighted = True
                # Check that highlights contain query terms
                assert any("machine" in highlight.lower() or "learning" in highlight.lower() 
                          for highlight in result.highlights)
            
            # Check that content contains highlighting tags (if highlights exist)
            if result.highlights:
                assert "<mark>" in result.content or "machine learning" in result.content.lower()
        
        # At least some results should have highlights
        assert found_highlighted
    
    def test_advanced_filtering_combinations(self, db_session, comprehensive_sample_data):
        """Test advanced filtering with multiple filter combinations"""
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
        
        # Test filtering by multiple knowledge types
        filters = SearchFilters(knowledge_types=[KnowledgeType.DEFINITION, KnowledgeType.FACT])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        for result in results:
            if result.type == "knowledge":
                assert result.metadata.get("kind") in ["definition", "fact"]
        
        # Test filtering by card type
        filters = SearchFilters(card_types=[CardType.QA])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        for result in results:
            if result.type == "card":
                assert result.metadata.get("card_type") == "qa"
        
        # Test filtering by difficulty range
        filters = SearchFilters(difficulty_min=2.0, difficulty_max=3.0)
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        for result in results:
            if result.type == "card":
                difficulty = result.metadata.get("difficulty", 0)
                assert 2.0 <= difficulty <= 3.0
        
        # Test combined filters
        filters = SearchFilters(
            knowledge_types=[KnowledgeType.DEFINITION],
            card_types=[CardType.QA],
            difficulty_min=1.5,
            difficulty_max=3.5
        )
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        # Verify combined filters work
        for result in results:
            if result.type == "knowledge":
                assert result.metadata.get("kind") == "definition"
            elif result.type == "card":
                assert result.metadata.get("card_type") == "qa"
                difficulty = result.metadata.get("difficulty", 0)
                assert 1.5 <= difficulty <= 3.5
    
    def test_advanced_ranking_factors(self, db_session, comprehensive_sample_data):
        """Test advanced ranking with multiple factors"""
        results = search_service.search(
            db_session,
            query="machine learning artificial intelligence",
            search_type=SearchType.HYBRID,
            limit=10
        )
        
        assert len(results) > 0
        
        # Check that results have ranking factors
        found_rank_factors = False
        for result in results:
            if result.rank_factors:
                found_rank_factors = True
                
                # Check that ranking factors are present
                expected_factors = ['term_frequency', 'term_coverage', 'position_bonus', 'phrase_bonus']
                for factor in expected_factors:
                    assert factor in result.rank_factors
                    assert isinstance(result.rank_factors[factor], (int, float))
        
        # At least some results should have ranking factors
        assert found_rank_factors
        
        # Results should be sorted by score (descending)
        scores = [result.score for result in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_snippet_generation_with_query_context(self, db_session, comprehensive_sample_data):
        """Test snippet generation that focuses on query-relevant content"""
        results = search_service.search(
            db_session,
            query="neural networks deep learning",
            search_type=SearchType.FULL_TEXT,
            limit=5
        )
        
        assert len(results) > 0
        
        # Check that snippets contain query terms
        for result in results:
            snippet_lower = result.snippet.lower()
            # At least one query term should be in the snippet
            assert ("neural" in snippet_lower or "networks" in snippet_lower or 
                   "deep" in snippet_lower or "learning" in snippet_lower)
    
    def test_search_performance_metrics(self, db_session, comprehensive_sample_data):
        """Test search performance metrics calculation"""
        # Define test queries and expected results
        test_queries = [
            "machine learning",
            "deep learning neural networks",
            "natural language processing"
        ]
        
        # Get actual results to create expected results
        expected_results = []
        for query in test_queries:
            results = search_service.search(db_session, query, limit=5)
            expected_ids = [result.id for result in results[:2]]  # Take top 2 as relevant
            expected_results.append(expected_ids)
        
        # Calculate performance metrics
        metrics = search_service.get_search_performance_metrics(
            db_session,
            test_queries,
            expected_results,
            SearchType.HYBRID
        )
        
        # Check that all metrics are present
        required_metrics = ['mrr', 'avg_response_time', 'precision_at_1', 'precision_at_5', 'precision_at_10', 'total_queries']
        for metric in required_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
        
        # Check reasonable values
        assert 0 <= metrics['mrr'] <= 1
        assert metrics['avg_response_time'] > 0
        assert 0 <= metrics['precision_at_1'] <= 1
        assert 0 <= metrics['precision_at_5'] <= 1
        assert 0 <= metrics['precision_at_10'] <= 1
        assert metrics['total_queries'] == len(test_queries)
    
    def test_mrr_calculation(self, db_session):
        """Test MRR calculation with known data"""
        # Create mock search results
        from app.services.search_service import SearchResult
        
        # Test case 1: Perfect ranking (relevant result at position 1)
        search_results_1 = [
            [
                SearchResult("1", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("2", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
            ]
        ]
        relevant_results_1 = [["1"]]
        
        mrr = search_service.calculate_mrr(search_results_1, relevant_results_1)
        assert mrr == 1.0  # 1/1 = 1.0
        
        # Test case 2: Relevant result at position 2
        search_results_2 = [
            [
                SearchResult("2", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("1", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
            ]
        ]
        relevant_results_2 = [["1"]]
        
        mrr = search_service.calculate_mrr(search_results_2, relevant_results_2)
        assert mrr == 0.5  # 1/2 = 0.5
        
        # Test case 3: No relevant results found
        search_results_3 = [
            [
                SearchResult("3", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("4", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
            ]
        ]
        relevant_results_3 = [["1"]]
        
        mrr = search_service.calculate_mrr(search_results_3, relevant_results_3)
        assert mrr == 0.0
    
    def test_query_optimization(self, db_session):
        """Test query optimization functionality"""
        # Test stop word removal
        original_query = "what is the machine learning and artificial intelligence"
        optimized = search_service.optimize_search_query(original_query)
        
        # Should remove some stop words but keep meaningful terms
        assert "machine learning" in optimized
        assert "artificial intelligence" in optimized
        assert len(optimized.split()) <= len(original_query.split())
        
        # Test whitespace cleanup
        messy_query = "  machine   learning    "
        optimized = search_service.optimize_search_query(messy_query)
        assert optimized == "machine learning"
        
        # Test length limiting
        very_long_query = "machine learning " * 50
        optimized = search_service.optimize_search_query(very_long_query)
        assert len(optimized) <= 200
    
    def test_search_analytics(self, db_session, comprehensive_sample_data):
        """Test search analytics functionality"""
        analytics = search_service.get_search_analytics(db_session)
        
        # Check that all expected fields are present
        expected_fields = [
            'total_searchable_items', 'total_knowledge', 'total_cards',
            'knowledge_with_embeddings', 'embedding_coverage_percent',
            'knowledge_type_distribution', 'card_type_distribution',
            'search_capabilities'
        ]
        
        for field in expected_fields:
            assert field in analytics
        
        # Check reasonable values
        assert analytics['total_knowledge'] > 0
        assert analytics['total_cards'] > 0
        assert analytics['total_searchable_items'] == analytics['total_knowledge'] + analytics['total_cards']
        assert 0 <= analytics['embedding_coverage_percent'] <= 100
        
        # Check distributions
        assert isinstance(analytics['knowledge_type_distribution'], dict)
        assert isinstance(analytics['card_type_distribution'], dict)
        
        # Check capabilities
        capabilities = analytics['search_capabilities']
        assert capabilities['full_text_search'] is True
        assert capabilities['filtering'] is True
        assert capabilities['highlighting'] is True
    
    @pytest.mark.asyncio
    async def test_combined_search_results_ranking(self, db_session, comprehensive_sample_data):
        """Test that hybrid search properly combines and ranks results"""
        # Update embeddings first
        await embedding_service.update_knowledge_embeddings(db_session)
        
        # Perform hybrid search
        results = search_service.search(
            db_session,
            query="machine learning algorithms",
            search_type=SearchType.HYBRID,
            limit=10
        )
        
        assert len(results) > 0
        
        # Check that results are properly ranked
        scores = [result.score for result in results]
        assert scores == sorted(scores, reverse=True)
        
        # Check that we get both knowledge and card results
        result_types = set(result.type for result in results)
        # Should have at least knowledge results
        assert "knowledge" in result_types
        
        # Check that results contain relevant content
        found_relevant = False
        for result in results:
            content_lower = result.content.lower()
            if ("machine" in content_lower and "learning" in content_lower) or "algorithm" in content_lower:
                found_relevant = True
                break
        
        assert found_relevant
    
    def test_search_with_empty_and_edge_cases(self, db_session, comprehensive_sample_data):
        """Test search behavior with edge cases"""
        # Empty query
        results = search_service.search(db_session, "")
        assert results == []
        
        # Whitespace only
        results = search_service.search(db_session, "   ")
        assert results == []
        
        # Very short query
        results = search_service.search(db_session, "a")
        assert isinstance(results, list)  # Should not crash
        
        # Query with special characters
        results = search_service.search(db_session, "machine-learning & AI!")
        assert isinstance(results, list)  # Should handle gracefully
        
        # Very long query
        long_query = "machine learning " * 100
        results = search_service.search(db_session, long_query)
        assert isinstance(results, list)  # Should handle gracefully
        
        # Non-existent terms
        results = search_service.search(db_session, "quantum computing blockchain")
        assert isinstance(results, list)  # Should return empty or minimal results
    
    def test_filtering_by_chapter_and_document(self, db_session, comprehensive_sample_data):
        """Test filtering by chapter and document IDs"""
        chapters = comprehensive_sample_data["chapters"]
        document = comprehensive_sample_data["document"]
        
        # Test filtering by specific chapter
        filters = SearchFilters(chapter_ids=[str(chapters[0].id)])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        # All knowledge results should be from the specified chapter
        for result in results:
            if result.type == "knowledge":
                assert result.metadata.get("chapter_id") == str(chapters[0].id)
        
        # Test filtering by document
        filters = SearchFilters(document_ids=[str(document.id)])
        results = search_service.search(
            db_session,
            query="learning",
            filters=filters,
            limit=10
        )
        
        # Should return results (all our test data is from this document)
        assert len(results) > 0


if __name__ == "__main__":
    # Run the integration test
    pytest.main([__file__, "-v"])