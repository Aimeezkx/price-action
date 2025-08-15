"""
Tests for entity extraction service.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.entity_extraction_service import (
    EntityExtractionService,
    EntityExtractionConfig,
    Entity,
    EntityType,
    Language
)


class TestEntityExtractionService:
    """Test cases for EntityExtractionService."""
    
    @pytest.fixture
    def service(self):
        """Create entity extraction service for testing."""
        config = EntityExtractionConfig(
            min_entity_length=2,
            min_confidence=0.5,
            enable_deduplication=True
        )
        return EntityExtractionService(config)
    
    @pytest.fixture
    def sample_english_text(self):
        """Sample English text for testing."""
        return """
        Machine learning is a subset of artificial intelligence (AI) that focuses on 
        algorithms that can learn from data. Companies like Google and Microsoft are 
        investing heavily in AI research. The neural network model achieved 95% accuracy 
        on the test dataset.
        """
    
    @pytest.fixture
    def sample_chinese_text(self):
        """Sample Chinese text for testing."""
        return """
        机器学习是人工智能的一个分支，专注于能够从数据中学习的算法。
        像谷歌和微软这样的公司正在大力投资人工智能研究。
        神经网络模型在测试数据集上达到了95%的准确率。
        """
    
    def test_language_detection_english(self, service, sample_english_text):
        """Test language detection for English text."""
        language = service.detect_language(sample_english_text)
        assert language == Language.ENGLISH
    
    def test_language_detection_chinese(self, service, sample_chinese_text):
        """Test language detection for Chinese text."""
        language = service.detect_language(sample_chinese_text)
        assert language == Language.CHINESE
    
    def test_language_detection_empty_text(self, service):
        """Test language detection for empty text."""
        language = service.detect_language("")
        assert language == Language.ENGLISH  # Default fallback
    
    @pytest.mark.asyncio
    async def test_extract_entities_english(self, service, sample_english_text):
        """Test entity extraction from English text."""
        entities = await service.extract_entities(sample_english_text, Language.ENGLISH)
        
        assert len(entities) > 0
        
        # Check for expected entity types
        entity_types = {entity.entity_type for entity in entities}
        assert EntityType.ORGANIZATION in entity_types or EntityType.CONCEPT in entity_types
        
        # Check that entities have required attributes
        for entity in entities:
            assert entity.text
            assert entity.entity_type
            assert entity.confidence > 0
            assert entity.start_pos >= 0
            assert entity.end_pos > entity.start_pos
    
    @pytest.mark.asyncio
    async def test_extract_entities_chinese(self, service, sample_chinese_text):
        """Test entity extraction from Chinese text."""
        entities = await service.extract_entities(sample_chinese_text, Language.CHINESE)
        
        assert len(entities) > 0
        
        # Check that entities have required attributes
        for entity in entities:
            assert entity.text
            assert entity.entity_type
            assert entity.confidence > 0
            assert entity.start_pos >= 0
            assert entity.end_pos > entity.start_pos
    
    @pytest.mark.asyncio
    async def test_extract_technical_terms(self, service):
        """Test technical term extraction."""
        text = "The API uses HTTP protocol and SQL database. The ML algorithm processes JSON data."
        
        entities = await service._extract_technical_terms(text)
        
        # Should find technical terms like API, HTTP, SQL, ML, JSON
        technical_entities = [e for e in entities if e.entity_type == EntityType.TECHNICAL_TERM]
        assert len(technical_entities) > 0
        
        # Check for specific technical terms
        entity_texts = {entity.text.upper() for entity in technical_entities}
        expected_terms = {'API', 'HTTP', 'SQL', 'ML', 'JSON'}
        assert len(entity_texts.intersection(expected_terms)) > 0
    
    def test_entity_filtering(self, service):
        """Test entity filtering functionality."""
        entities = [
            Entity("AI", EntityType.TECHNICAL_TERM, 0, 2, 0.8),
            Entity("a", EntityType.TERM, 3, 4, 0.7),  # Too short
            Entity("the", EntityType.TERM, 5, 8, 0.6),  # Stopword
            Entity("machine learning", EntityType.CONCEPT, 9, 25, 0.9),
            Entity("123", EntityType.NUMBER, 26, 29, 0.5),  # Numbers only
            Entity("!!!", EntityType.TERM, 30, 33, 0.4),  # Punctuation only
        ]
        
        filtered = service._filter_entities(entities, Language.ENGLISH)
        
        # Should keep AI and machine learning, filter out others
        assert len(filtered) <= 2
        filtered_texts = {entity.text for entity in filtered}
        assert "AI" in filtered_texts
        assert "machine learning" in filtered_texts
        assert "a" not in filtered_texts
        assert "the" not in filtered_texts
    
    def test_entity_deduplication(self, service):
        """Test entity deduplication."""
        entities = [
            Entity("machine learning", EntityType.CONCEPT, 0, 16, 0.9),
            Entity("Machine Learning", EntityType.CONCEPT, 20, 36, 0.8),  # Duplicate
            Entity("ML", EntityType.TECHNICAL_TERM, 40, 42, 0.7),
            Entity("artificial intelligence", EntityType.CONCEPT, 50, 72, 0.9),
            Entity("AI", EntityType.TECHNICAL_TERM, 80, 82, 0.8),
        ]
        
        deduplicated = service._deduplicate_entities(entities)
        
        # Should remove the duplicate "Machine Learning"
        assert len(deduplicated) == 4
        
        # Check that the higher confidence version is kept
        ml_entities = [e for e in deduplicated if "machine" in e.text.lower()]
        assert len(ml_entities) == 1
        assert ml_entities[0].confidence == 0.9
    
    def test_entity_similarity_calculation(self, service):
        """Test entity similarity calculation."""
        entity1 = Entity("machine learning", EntityType.CONCEPT, 0, 16, 0.9)
        entity2 = Entity("Machine Learning", EntityType.CONCEPT, 0, 16, 0.8)
        entity3 = Entity("deep learning", EntityType.CONCEPT, 0, 13, 0.8)
        
        # Exact match (case insensitive)
        similarity1 = service._calculate_entity_similarity(entity1, entity2)
        assert similarity1 == 1.0
        
        # Partial similarity
        similarity2 = service._calculate_entity_similarity(entity1, entity3)
        assert 0.0 < similarity2 < 1.0
    
    def test_frequency_calculation(self, service):
        """Test entity frequency calculation."""
        text = "Machine learning and deep learning are subsets of artificial intelligence. Machine learning is popular."
        entities = [
            Entity("machine learning", EntityType.CONCEPT, 0, 16, 0.9),
            Entity("deep learning", EntityType.CONCEPT, 21, 34, 0.8),
            Entity("artificial intelligence", EntityType.CONCEPT, 50, 72, 0.9),
        ]
        
        entities_with_freq = service._calculate_frequencies(entities, text)
        
        # "machine learning" appears twice
        ml_entity = next(e for e in entities_with_freq if e.text == "machine learning")
        assert ml_entity.frequency == 2
        
        # "deep learning" appears once
        dl_entity = next(e for e in entities_with_freq if e.text == "deep learning")
        assert dl_entity.frequency == 1
    
    def test_entity_ranking(self, service):
        """Test entity ranking by importance."""
        entities = [
            Entity("AI", EntityType.TECHNICAL_TERM, 0, 2, 0.9, frequency=3),
            Entity("machine learning", EntityType.CONCEPT, 3, 19, 0.8, frequency=2),
            Entity("Google", EntityType.ORGANIZATION, 20, 26, 0.7, frequency=1),
            Entity("2023", EntityType.DATE, 27, 31, 0.6, frequency=1),
        ]
        
        ranked = service.rank_entities_by_importance(entities)
        
        # Technical terms and concepts should rank higher
        assert ranked[0].entity_type in [EntityType.TECHNICAL_TERM, EntityType.CONCEPT]
        
        # Check that ranking considers multiple factors
        assert all(hasattr(entity, 'importance_score') for entity in ranked)
    
    def test_entity_statistics(self, service):
        """Test entity statistics calculation."""
        entities = [
            Entity("AI", EntityType.TECHNICAL_TERM, 0, 2, 0.9, frequency=3),
            Entity("machine learning", EntityType.CONCEPT, 3, 19, 0.8, frequency=2),
            Entity("Google", EntityType.ORGANIZATION, 20, 26, 0.7, frequency=1),
            Entity("AI", EntityType.TECHNICAL_TERM, 27, 29, 0.9, frequency=3),  # Duplicate text
        ]
        
        stats = service.get_entity_statistics(entities)
        
        assert stats['total_entities'] == 4
        assert stats['unique_entities'] == 3  # "AI" appears twice
        assert EntityType.TECHNICAL_TERM in stats['entity_types']
        assert stats['avg_confidence'] > 0
        assert stats['avg_frequency'] > 0
        assert stats['most_frequent'] == "AI"
    
    def test_empty_text_handling(self, service):
        """Test handling of empty or whitespace text."""
        @pytest.mark.asyncio
        async def test_empty():
            entities = await service.extract_entities("")
            assert entities == []
        
        @pytest.mark.asyncio
        async def test_whitespace():
            entities = await service.extract_entities("   \n\t  ")
            assert entities == []
    
    def test_context_extraction(self, service):
        """Test context extraction around entities."""
        text = "Machine learning is a powerful technique for data analysis and prediction."
        start_pos = 0
        end_pos = 16  # "Machine learning"
        
        context = service._extract_context(text, start_pos, end_pos, window=20)
        
        assert "Machine learning" in context
        assert len(context) > len("Machine learning")
    
    def test_config_customization(self):
        """Test service configuration customization."""
        custom_config = EntityExtractionConfig(
            min_entity_length=3,
            min_confidence=0.8,
            custom_stopwords={'custom', 'stop'},
            detect_technical_terms=False
        )
        
        service = EntityExtractionService(custom_config)
        
        assert service.config.min_entity_length == 3
        assert service.config.min_confidence == 0.8
        assert 'custom' in service.stopwords[Language.ENGLISH]
        assert not service.config.detect_technical_terms


class TestEntityClass:
    """Test cases for Entity class."""
    
    def test_entity_creation(self):
        """Test entity creation and attributes."""
        entity = Entity(
            text="machine learning",
            entity_type=EntityType.CONCEPT,
            start_pos=0,
            end_pos=16,
            confidence=0.9,
            frequency=2,
            context="Machine learning is a subset of AI"
        )
        
        assert entity.text == "machine learning"
        assert entity.entity_type == EntityType.CONCEPT
        assert entity.start_pos == 0
        assert entity.end_pos == 16
        assert entity.confidence == 0.9
        assert entity.frequency == 2
        assert "Machine learning" in entity.context
    
    def test_entity_equality(self):
        """Test entity equality comparison."""
        entity1 = Entity("AI", EntityType.TECHNICAL_TERM, 0, 2, 0.9)
        entity2 = Entity("AI", EntityType.TECHNICAL_TERM, 10, 12, 0.8)
        entity3 = Entity("ML", EntityType.TECHNICAL_TERM, 0, 2, 0.9)
        
        # Same text and type should be equal
        assert entity1 == entity2
        
        # Different text should not be equal
        assert entity1 != entity3
    
    def test_entity_hashing(self):
        """Test entity hashing for use in sets."""
        entity1 = Entity("AI", EntityType.TECHNICAL_TERM, 0, 2, 0.9)
        entity2 = Entity("AI", EntityType.TECHNICAL_TERM, 10, 12, 0.8)
        entity3 = Entity("ML", EntityType.TECHNICAL_TERM, 0, 2, 0.9)
        
        entity_set = {entity1, entity2, entity3}
        
        # Should only contain 2 unique entities (entity1 and entity2 are considered same)
        assert len(entity_set) == 2


@pytest.mark.integration
class TestEntityExtractionIntegration:
    """Integration tests for entity extraction service."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_english(self):
        """Test full entity extraction pipeline with English text."""
        service = EntityExtractionService()
        
        text = """
        Artificial Intelligence (AI) and Machine Learning (ML) are transformative technologies.
        Companies like Google, Microsoft, and OpenAI are leading the research. The GPT-3 model
        achieved remarkable results with 175 billion parameters. Deep learning algorithms
        process vast amounts of data to identify patterns and make predictions.
        """
        
        entities = await service.extract_entities(text)
        
        # Should extract various types of entities
        assert len(entities) > 5
        
        # Check for expected entity types
        entity_types = {entity.entity_type for entity in entities}
        expected_types = {
            EntityType.TECHNICAL_TERM,
            EntityType.CONCEPT,
            EntityType.ORGANIZATION
        }
        assert len(entity_types.intersection(expected_types)) > 0
        
        # Rank entities and get statistics
        ranked_entities = service.rank_entities_by_importance(entities, max_entities=10)
        stats = service.get_entity_statistics(entities)
        
        assert len(ranked_entities) <= 10
        assert stats['total_entities'] > 0
        assert stats['unique_entities'] > 0
    
    @pytest.mark.asyncio
    async def test_full_pipeline_chinese(self):
        """Test full entity extraction pipeline with Chinese text."""
        service = EntityExtractionService()
        
        text = """
        人工智能（AI）和机器学习（ML）是变革性技术。像谷歌、微软和OpenAI这样的公司
        正在引领研究。GPT-3模型以1750亿参数取得了显著成果。深度学习算法处理大量数据
        以识别模式并进行预测。自然语言处理是人工智能的重要分支。
        """
        
        entities = await service.extract_entities(text)
        
        # Should extract entities from Chinese text
        assert len(entities) > 0
        
        # Check that Chinese entities are properly extracted
        chinese_entities = [e for e in entities if any('\u4e00' <= c <= '\u9fff' for c in e.text)]
        assert len(chinese_entities) > 0
        
        # Get statistics
        stats = service.get_entity_statistics(entities)
        assert stats['total_entities'] > 0
    
    @pytest.mark.asyncio
    async def test_mixed_language_text(self):
        """Test entity extraction from mixed language text."""
        service = EntityExtractionService()
        
        text = """
        Machine Learning (机器学习) is a subset of Artificial Intelligence (人工智能).
        Companies like Google (谷歌) and Microsoft (微软) are investing in AI research.
        The neural network (神经网络) achieved 95% accuracy.
        """
        
        entities = await service.extract_entities(text)
        
        # Should extract entities from both languages
        assert len(entities) > 0
        
        # Check for both English and Chinese entities
        english_entities = [e for e in entities if any('a' <= c.lower() <= 'z' for c in e.text)]
        chinese_entities = [e for e in entities if any('\u4e00' <= c <= '\u9fff' for c in e.text)]
        
        assert len(english_entities) > 0
        assert len(chinese_entities) > 0