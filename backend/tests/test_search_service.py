"""
Tests for search service
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.search_service import SearchService, SearchType, SearchFilters, SearchResult, search_service
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, CardType
from app.models.document import Chapter


class TestSearchService:
    """Test cases for SearchService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = SearchService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service.default_limit == 20
        assert self.service.max_limit == 100
        assert self.service.snippet_length == 200
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_search_filters(self):
        """Sample search filters"""
        return SearchFilters(
            chapter_ids=["chapter1", "chapter2"],
            knowledge_types=[KnowledgeType.DEFINITION, KnowledgeType.FACT],
            card_types=[CardType.QA, CardType.CLOZE],
            difficulty_min=1.0,
            difficulty_max=3.0,
            document_ids=["doc1", "doc2"]
        )
    
    def test_search_empty_query(self, mock_db_session):
        """Test search with empty query"""
        results = self.service.search(mock_db_session, "")
        assert results == []
        
        results = self.service.search(mock_db_session, "   ")
        assert results == []
    
    def test_search_limit_validation(self, mock_db_session):
        """Test search limit validation"""
        with patch.object(self.service, '_hybrid_search', return_value=[]):
            # Test default limit
            self.service.search(mock_db_session, "test")
            
            # Test limit capping
            self.service.search(mock_db_session, "test", limit=200)
            
            # Test minimum limit
            self.service.search(mock_db_session, "test", limit=0)
    
    @patch('app.services.search_service.embedding_service')
    def test_search_full_text(self, mock_embedding_service, mock_db_session):
        """Test full-text search"""
        with patch.object(self.service, '_full_text_search', return_value=[]) as mock_full_text:
            results = self.service.search(
                mock_db_session,
                "test query",
                search_type=SearchType.FULL_TEXT
            )
            
            mock_full_text.assert_called_once()
            assert results == []
    
    @patch('app.services.search_service.embedding_service')
    def test_search_semantic(self, mock_embedding_service, mock_db_session):
        """Test semantic search"""
        with patch.object(self.service, '_semantic_search', return_value=[]) as mock_semantic:
            results = self.service.search(
                mock_db_session,
                "test query",
                search_type=SearchType.SEMANTIC
            )
            
            mock_semantic.assert_called_once()
            assert results == []
    
    @patch('app.services.search_service.embedding_service')
    def test_search_hybrid(self, mock_embedding_service, mock_db_session):
        """Test hybrid search"""
        with patch.object(self.service, '_hybrid_search', return_value=[]) as mock_hybrid:
            results = self.service.search(
                mock_db_session,
                "test query",
                search_type=SearchType.HYBRID
            )
            
            mock_hybrid.assert_called_once()
            assert results == []
    
    def test_search_invalid_type(self, mock_db_session):
        """Test search with invalid search type"""
        results = self.service.search(
            mock_db_session,
            "test query",
            search_type="invalid_type"
        )
        assert results == []
    
    def test_create_snippet_short_text(self):
        """Test snippet creation with short text"""
        text = "This is a short text."
        snippet = self.service._create_snippet(text)
        assert snippet == text
    
    def test_create_snippet_long_text(self):
        """Test snippet creation with long text"""
        text = "This is a very long text. " * 20  # Make it longer than snippet_length
        snippet = self.service._create_snippet(text)
        
        assert len(snippet) <= self.service.snippet_length + 3  # +3 for "..."
        assert snippet.endswith("...") or snippet.endswith(".")
    
    def test_create_snippet_sentence_boundary(self):
        """Test snippet creation respects sentence boundaries"""
        text = "First sentence. Second sentence. " + "Word " * 50
        snippet = self.service._create_snippet(text)
        
        # Should break at sentence boundary if possible
        assert "First sentence. Second sentence." in snippet or snippet.endswith("...")
    
    def test_calculate_simple_relevance(self):
        """Test simple relevance calculation"""
        text = "machine learning is a subset of artificial intelligence"
        query = "machine learning"
        
        score = self.service._calculate_simple_relevance(text, query)
        assert score > 0
        
        # Test with no matches
        score = self.service._calculate_simple_relevance(text, "quantum computing")
        assert score == 0
    
    def test_knowledge_to_search_result(self):
        """Test converting knowledge to search result"""
        knowledge = Mock(spec=Knowledge)
        knowledge.id = "test-id"
        knowledge.kind = KnowledgeType.DEFINITION
        knowledge.text = "Test knowledge text"
        knowledge.entities = ["entity1", "entity2"]
        knowledge.anchors = {"page": 1, "chapter": "Chapter 1"}
        knowledge.chapter_id = "chapter-id"
        knowledge.confidence_score = 0.9
        
        result = self.service._knowledge_to_search_result(knowledge, 0.8)
        
        assert isinstance(result, SearchResult)
        assert result.id == "test-id"
        assert result.type == "knowledge"
        assert result.title == "Definition Knowledge"
        assert result.content == "Test knowledge text"
        assert result.score == 0.8
        assert result.metadata["kind"] == "definition"
        assert result.metadata["entities"] == ["entity1", "entity2"]
        assert result.metadata["anchors"] == {"page": 1, "chapter": "Chapter 1"}
    
    def test_card_to_search_result(self):
        """Test converting card to search result"""
        card = Mock(spec=Card)
        card.id = "card-id"
        card.card_type = CardType.QA
        card.front = "What is machine learning?"
        card.back = "A subset of artificial intelligence"
        card.difficulty = 2.5
        card.knowledge_id = "knowledge-id"
        card.card_metadata = {"source": "textbook"}
        
        result = self.service._card_to_search_result(card, 0.7)
        
        assert isinstance(result, SearchResult)
        assert result.id == "card-id"
        assert result.type == "card"
        assert result.title == "Qa Card"
        assert "What is machine learning?" in result.content
        assert "A subset of artificial intelligence" in result.content
        assert result.score == 0.7
        assert result.metadata["card_type"] == "qa"
        assert result.metadata["difficulty"] == 2.5
    
    def test_apply_knowledge_filters(self, sample_search_filters):
        """Test applying filters to knowledge query"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        
        filtered_query = self.service._apply_knowledge_filters(mock_query, sample_search_filters)
        
        # Should have called filter multiple times for different filter types
        assert mock_query.filter.call_count >= 2  # chapter_ids and knowledge_types
        assert mock_query.join.call_count >= 1  # for document_ids filter
    
    def test_apply_card_filters(self, sample_search_filters):
        """Test applying filters to card query"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        
        filtered_query = self.service._apply_card_filters(mock_query, sample_search_filters)
        
        # Should have called filter multiple times for different filter types
        assert mock_query.filter.call_count >= 4  # Various card filters
    
    def test_get_search_suggestions_short_query(self, mock_db_session):
        """Test search suggestions with short query"""
        suggestions = self.service.get_search_suggestions(mock_db_session, "a")
        assert suggestions == []
    
    def test_get_search_suggestions_success(self, mock_db_session):
        """Test successful search suggestions"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            (["machine learning", "artificial intelligence"],),
            (["machine vision", "computer science"],),
        ]
        mock_db_session.query.return_value = mock_query
        
        suggestions = self.service.get_search_suggestions(mock_db_session, "machine", limit=3)
        
        assert "machine learning" in suggestions
        assert "machine vision" in suggestions
        assert len(suggestions) <= 3
    
    def test_get_search_suggestions_error_handling(self, mock_db_session):
        """Test error handling in search suggestions"""
        mock_db_session.query.side_effect = Exception("Database error")
        
        suggestions = self.service.get_search_suggestions(mock_db_session, "test")
        assert suggestions == []
    
    @patch('app.services.search_service.embedding_service')
    def test_semantic_search_with_filters(self, mock_embedding_service, mock_db_session, sample_search_filters):
        """Test semantic search with filters applied"""
        # Mock embedding service
        mock_embedding_service.generate_embedding.return_value = [0.1] * 384
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.add_columns.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        with patch.object(self.service, '_apply_knowledge_filters', return_value=mock_query):
            results = self.service._semantic_search(
                mock_db_session,
                "test query",
                sample_search_filters,
                limit=10,
                offset=0,
                similarity_threshold=0.7
            )
        
        assert results == []
        mock_embedding_service.generate_embedding.assert_called_once_with("test query")
    
    def test_hybrid_search_combination(self, mock_db_session):
        """Test hybrid search combines results properly"""
        # Mock full-text and semantic search results
        full_text_result = SearchResult(
            id="1", type="knowledge", title="Test", content="Content",
            snippet="Snippet", score=0.8, metadata={}
        )
        
        semantic_result = SearchResult(
            id="2", type="knowledge", title="Test2", content="Content2",
            snippet="Snippet2", score=0.9, metadata={}
        )
        
        duplicate_result = SearchResult(
            id="1", type="knowledge", title="Test", content="Content",
            snippet="Snippet", score=0.7, metadata={}
        )
        
        with patch.object(self.service, '_full_text_search', return_value=[full_text_result]):
            with patch.object(self.service, '_semantic_search', return_value=[semantic_result, duplicate_result]):
                results = self.service._hybrid_search(
                    mock_db_session,
                    "test query",
                    SearchFilters(),
                    limit=10,
                    offset=0,
                    similarity_threshold=0.7
                )
        
        # Should have 2 unique results (duplicate should be combined)
        assert len(results) == 2
        
        # Results should be sorted by score
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestSearchFilters:
    """Test SearchFilters dataclass"""
    
    def test_default_filters(self):
        """Test default filter values"""
        filters = SearchFilters()
        assert filters.chapter_ids is None
        assert filters.knowledge_types is None
        assert filters.card_types is None
        assert filters.difficulty_min is None
        assert filters.difficulty_max is None
        assert filters.document_ids is None
    
    def test_custom_filters(self):
        """Test custom filter values"""
        filters = SearchFilters(
            chapter_ids=["ch1", "ch2"],
            knowledge_types=[KnowledgeType.DEFINITION],
            card_types=[CardType.QA],
            difficulty_min=1.0,
            difficulty_max=3.0,
            document_ids=["doc1"]
        )
        
        assert filters.chapter_ids == ["ch1", "ch2"]
        assert filters.knowledge_types == [KnowledgeType.DEFINITION]
        assert filters.card_types == [CardType.QA]
        assert filters.difficulty_min == 1.0
        assert filters.difficulty_max == 3.0
        assert filters.document_ids == ["doc1"]


class TestSearchResult:
    """Test SearchResult dataclass"""
    
    def test_search_result_creation(self):
        """Test SearchResult creation"""
        result = SearchResult(
            id="test-id",
            type="knowledge",
            title="Test Title",
            content="Test content",
            snippet="Test snippet",
            score=0.85,
            metadata={"key": "value"},
            highlights=["highlight1", "highlight2"]
        )
        
        assert result.id == "test-id"
        assert result.type == "knowledge"
        assert result.title == "Test Title"
        assert result.content == "Test content"
        assert result.snippet == "Test snippet"
        assert result.score == 0.85
        assert result.metadata == {"key": "value"}
        assert result.highlights == ["highlight1", "highlight2"]


class TestGlobalSearchService:
    """Test the global search service instance"""
    
    def test_global_instance(self):
        """Test that global search service instance exists"""
        assert search_service is not None
        assert isinstance(search_service, SearchService)


class TestSearchHighlighting:
    """Test search highlighting functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = SearchService()
    
    def test_extract_query_terms(self):
        """Test query term extraction"""
        query = "machine learning and artificial intelligence"
        terms = self.service._extract_query_terms(query)
        
        assert "machine" in terms
        assert "learning" in terms
        assert "artificial" in terms
        assert "intelligence" in terms
        assert "and" not in terms  # Stop word should be removed
    
    def test_highlight_text_simple(self):
        """Test simple text highlighting"""
        text = "Machine learning is a subset of artificial intelligence."
        query = "machine learning"
        
        highlighted, highlights = self.service._highlight_text(text, query)
        
        assert "<mark>" in highlighted
        assert "</mark>" in highlighted
        assert len(highlights) > 0
        # Check that at least one highlight contains one of the query terms
        highlight_text = " ".join(highlights).lower()
        assert "machine" in highlight_text or "learning" in highlight_text
    
    def test_highlight_text_case_insensitive(self):
        """Test case-insensitive highlighting"""
        text = "MACHINE LEARNING is important."
        query = "machine learning"
        
        highlighted, highlights = self.service._highlight_text(text, query)
        
        assert "<mark>" in highlighted
        assert len(highlights) >= 1
    
    def test_highlight_text_word_boundaries(self):
        """Test that highlighting respects word boundaries"""
        text = "The machine learning algorithm uses machinelearning techniques."
        query = "machine learning"
        
        highlighted, highlights = self.service._highlight_text(text, query)
        
        # Should highlight "machine learning" but not "machinelearning"
        assert highlighted.count("<mark>") >= 2  # At least "machine" and "learning"
    
    def test_find_best_snippet(self):
        """Test finding best snippet with query terms"""
        long_text = "This is the beginning. " * 10 + "Machine learning is important. " * 5 + "This is the end. " * 10
        query = "machine learning"
        
        snippet = self.service._find_best_snippet(long_text, query)
        
        assert "machine learning" in snippet.lower()
        assert len(snippet) <= self.service.snippet_length + 50  # Allow some margin for ellipsis
    
    def test_create_snippet_with_query(self):
        """Test snippet creation with query context"""
        text = "Introduction paragraph. Machine learning is a powerful technique for data analysis. Conclusion paragraph."
        query = "machine learning"
        
        snippet = self.service._create_snippet(text, query)
        
        assert "machine learning" in snippet.lower()


class TestAdvancedRanking:
    """Test advanced ranking functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = SearchService()
    
    def test_calculate_advanced_ranking(self):
        """Test advanced ranking calculation"""
        text = "Machine learning is a subset of artificial intelligence that enables computers to learn from data."
        query = "machine learning artificial intelligence"
        metadata = {"kind": "definition", "confidence_score": 0.9}
        
        score, factors = self.service._calculate_advanced_ranking(text, query, metadata)
        
        assert score > 0
        assert isinstance(factors, dict)
        
        # Check that all expected factors are present
        expected_factors = ['term_frequency', 'term_coverage', 'position_bonus', 'phrase_bonus', 'content_bonus', 'confidence_bonus', 'length_penalty']
        for factor in expected_factors:
            assert factor in factors
            assert isinstance(factors[factor], (int, float))
    
    def test_ranking_term_coverage(self):
        """Test term coverage factor in ranking"""
        text = "Machine learning and artificial intelligence are related fields."
        
        # Query with all terms present
        query1 = "machine learning"
        score1, factors1 = self.service._calculate_advanced_ranking(text, query1, {})
        
        # Query with only some terms present
        query2 = "machine quantum"
        score2, factors2 = self.service._calculate_advanced_ranking(text, query2, {})
        
        # First query should have better term coverage
        assert factors1['term_coverage'] > factors2['term_coverage']
    
    def test_ranking_position_bonus(self):
        """Test position bonus in ranking"""
        text1 = "Machine learning is important. Other topics follow."
        text2 = "Other topics are discussed first. Machine learning is mentioned later."
        query = "machine learning"
        
        score1, factors1 = self.service._calculate_advanced_ranking(text1, query, {})
        score2, factors2 = self.service._calculate_advanced_ranking(text2, query, {})
        
        # Text with terms appearing earlier should get higher position bonus
        assert factors1['position_bonus'] > factors2['position_bonus']
    
    def test_ranking_phrase_bonus(self):
        """Test exact phrase bonus in ranking"""
        text1 = "Machine learning is a powerful technique."
        text2 = "Machine intelligence and learning algorithms are useful."
        query = "machine learning"
        
        score1, factors1 = self.service._calculate_advanced_ranking(text1, query, {})
        score2, factors2 = self.service._calculate_advanced_ranking(text2, query, {})
        
        # Text with exact phrase should get phrase bonus
        assert factors1['phrase_bonus'] > factors2['phrase_bonus']
    
    def test_ranking_content_bonus(self):
        """Test content type bonus in ranking"""
        text = "Machine learning is a method of data analysis."
        
        # Definition should get higher bonus than fact
        metadata_def = {"kind": "definition"}
        metadata_fact = {"kind": "fact"}
        
        score1, factors1 = self.service._calculate_advanced_ranking(text, "machine learning", metadata_def)
        score2, factors2 = self.service._calculate_advanced_ranking(text, "machine learning", metadata_fact)
        
        assert factors1['content_bonus'] > factors2['content_bonus']


class TestPerformanceMetrics:
    """Test search performance metrics"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = SearchService()
    
    def test_calculate_mrr_perfect(self):
        """Test MRR calculation with perfect results"""
        from app.services.search_service import SearchResult
        
        # All relevant results at position 1
        search_results = [
            [SearchResult("1", "knowledge", "Test", "Content", "Snippet", 1.0, {})],
            [SearchResult("2", "knowledge", "Test", "Content", "Snippet", 1.0, {})],
        ]
        relevant_results = [["1"], ["2"]]
        
        mrr = self.service.calculate_mrr(search_results, relevant_results)
        assert mrr == 1.0
    
    def test_calculate_mrr_mixed(self):
        """Test MRR calculation with mixed results"""
        from app.services.search_service import SearchResult
        
        # First query: relevant at position 1, second query: relevant at position 2
        search_results = [
            [
                SearchResult("1", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("2", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
            ],
            [
                SearchResult("3", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("4", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
            ]
        ]
        relevant_results = [["1"], ["4"]]
        
        mrr = self.service.calculate_mrr(search_results, relevant_results)
        expected_mrr = (1.0 + 0.5) / 2  # (1/1 + 1/2) / 2
        assert abs(mrr - expected_mrr) < 1e-6
    
    def test_calculate_precision_at_k(self):
        """Test precision at k calculation"""
        from app.services.search_service import SearchResult
        
        search_results = [
            [
                SearchResult("1", "knowledge", "Test", "Content", "Snippet", 1.0, {}),
                SearchResult("2", "knowledge", "Test", "Content", "Snippet", 0.8, {}),
                SearchResult("3", "knowledge", "Test", "Content", "Snippet", 0.6, {}),
            ]
        ]
        relevant_results = [["1", "3"]]  # 2 out of 3 are relevant
        
        # Precision at 3 should be 2/3
        precision = self.service._calculate_precision_at_k(search_results, relevant_results, 3)
        expected_precision = 2.0 / 3.0
        assert abs(precision - expected_precision) < 1e-6
        
        # Precision at 1 should be 1/1 (first result is relevant)
        precision_at_1 = self.service._calculate_precision_at_k(search_results, relevant_results, 1)
        assert precision_at_1 == 1.0
    
    def test_optimize_search_query(self):
        """Test search query optimization"""
        # Test stop word removal
        query = "what is the machine learning"
        optimized = self.service.optimize_search_query(query)
        assert "machine learning" in optimized
        assert len(optimized.split()) < len(query.split())
        
        # Test whitespace cleanup
        query = "  machine   learning  "
        optimized = self.service.optimize_search_query(query)
        assert optimized == "machine learning"
        
        # Test length limiting
        long_query = "word " * 100
        optimized = self.service.optimize_search_query(long_query)
        assert len(optimized) <= 200