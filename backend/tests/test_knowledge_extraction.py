"""
Tests for knowledge extraction service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from app.services.knowledge_extraction_service import (
    KnowledgeExtractionService,
    KnowledgeExtractionConfig,
    ExtractedKnowledge
)
from app.services.text_segmentation_service import TextSegment
from app.models.knowledge import KnowledgeType


@pytest.fixture
def knowledge_service():
    """Create a knowledge extraction service for testing."""
    config = KnowledgeExtractionConfig(
        use_llm=False,  # Disable LLM for testing
        enable_fallback=True,
        min_confidence=0.5
    )
    return KnowledgeExtractionService(config)


@pytest.fixture
def sample_segments():
    """Create sample text segments for testing."""
    return [
        TextSegment(
            text="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            character_count=120,
            word_count=18,
            sentence_count=1,
            anchors={"page": 1, "chapter_id": "ch1", "position": {"block_index": 0}},
            original_blocks=[0]
        ),
        TextSegment(
            text="For example, a neural network can recognize patterns in data by adjusting weights between nodes.",
            character_count=95,
            word_count=16,
            sentence_count=1,
            anchors={"page": 1, "chapter_id": "ch1", "position": {"block_index": 1}},
            original_blocks=[1]
        ),
        TextSegment(
            text="Theorem 1: If a function is continuous on a closed interval, then it attains its maximum and minimum values.",
            character_count=110,
            word_count=19,
            sentence_count=1,
            anchors={"page": 2, "chapter_id": "ch1", "position": {"block_index": 2}},
            original_blocks=[2]
        ),
        TextSegment(
            text="Step 1: Collect the data. Step 2: Clean and preprocess the data. Step 3: Train the model.",
            character_count=85,
            word_count=17,
            sentence_count=3,
            anchors={"page": 3, "chapter_id": "ch1", "position": {"block_index": 3}},
            original_blocks=[3]
        )
    ]


class TestKnowledgeExtractionService:
    """Test cases for KnowledgeExtractionService."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = KnowledgeExtractionService()
        
        assert service.config is not None
        assert service.text_segmentation is not None
        assert service.entity_extraction is not None
        assert service.compiled_patterns is not None
        assert len(service.compiled_patterns) == 5  # 5 knowledge types
    
    def test_pattern_compilation(self, knowledge_service):
        """Test that regex patterns are compiled correctly."""
        patterns = knowledge_service.compiled_patterns
        
        # Check that all knowledge types have patterns
        expected_types = [
            KnowledgeType.DEFINITION,
            KnowledgeType.FACT,
            KnowledgeType.THEOREM,
            KnowledgeType.PROCESS,
            KnowledgeType.EXAMPLE
        ]
        
        for knowledge_type in expected_types:
            assert knowledge_type in patterns
            assert len(patterns[knowledge_type]) > 0
            
            # Check that patterns are compiled regex objects
            for pattern in patterns[knowledge_type]:
                assert hasattr(pattern, 'finditer')
    
    @pytest.mark.asyncio
    async def test_extract_definition_knowledge(self, knowledge_service, sample_segments):
        """Test extraction of definition knowledge points."""
        # Use only the definition segment
        definition_segment = sample_segments[0]
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                Mock(text="machine learning", entity_type="CONCEPT"),
                Mock(text="artificial intelligence", entity_type="CONCEPT")
            ]
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [definition_segment], "ch1"
            )
        
        # Should extract at least one definition
        assert len(knowledge_points) > 0
        
        # Check for definition knowledge point
        definition_found = any(kp.kind == KnowledgeType.DEFINITION for kp in knowledge_points)
        assert definition_found
        
        # Check that entities are included
        for kp in knowledge_points:
            if kp.kind == KnowledgeType.DEFINITION:
                assert len(kp.entities) > 0
                assert kp.confidence >= 0.5
                assert "machine learning" in kp.text.lower()
    
    @pytest.mark.asyncio
    async def test_extract_example_knowledge(self, knowledge_service, sample_segments):
        """Test extraction of example knowledge points."""
        # Use only the example segment
        example_segment = sample_segments[1]
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                Mock(text="neural network", entity_type="CONCEPT")
            ]
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [example_segment], "ch1"
            )
        
        # Should extract at least one example
        assert len(knowledge_points) > 0
        
        # Check for example knowledge point
        example_found = any(kp.kind == KnowledgeType.EXAMPLE for kp in knowledge_points)
        assert example_found
        
        for kp in knowledge_points:
            if kp.kind == KnowledgeType.EXAMPLE:
                assert "example" in kp.text.lower()
                assert kp.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_extract_theorem_knowledge(self, knowledge_service, sample_segments):
        """Test extraction of theorem knowledge points."""
        # Use only the theorem segment
        theorem_segment = sample_segments[2]
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                Mock(text="function", entity_type="CONCEPT"),
                Mock(text="continuous", entity_type="CONCEPT")
            ]
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [theorem_segment], "ch1"
            )
        
        # Should extract at least one theorem
        assert len(knowledge_points) > 0
        
        # Check for theorem knowledge point
        theorem_found = any(kp.kind == KnowledgeType.THEOREM for kp in knowledge_points)
        assert theorem_found
        
        for kp in knowledge_points:
            if kp.kind == KnowledgeType.THEOREM:
                assert "theorem" in kp.text.lower()
                assert kp.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_extract_process_knowledge(self, knowledge_service, sample_segments):
        """Test extraction of process knowledge points."""
        # Use only the process segment
        process_segment = sample_segments[3]
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                Mock(text="data", entity_type="CONCEPT"),
                Mock(text="model", entity_type="CONCEPT")
            ]
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [process_segment], "ch1"
            )
        
        # Should extract at least one process
        assert len(knowledge_points) > 0
        
        # Check for process knowledge point
        process_found = any(kp.kind == KnowledgeType.PROCESS for kp in knowledge_points)
        assert process_found
        
        for kp in knowledge_points:
            if kp.kind == KnowledgeType.PROCESS:
                assert "step" in kp.text.lower()
                assert kp.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_extract_all_knowledge_types(self, knowledge_service, sample_segments):
        """Test extraction of multiple knowledge types from all segments."""
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                Mock(text="machine learning", entity_type="CONCEPT"),
                Mock(text="neural network", entity_type="CONCEPT"),
                Mock(text="function", entity_type="CONCEPT"),
                Mock(text="data", entity_type="CONCEPT")
            ]
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                sample_segments, "ch1"
            )
        
        # Should extract multiple knowledge points
        assert len(knowledge_points) >= 3
        
        # Check that different types are extracted
        extracted_types = set(kp.kind for kp in knowledge_points)
        assert len(extracted_types) >= 2  # At least 2 different types
        
        # Check that all knowledge points have required fields
        for kp in knowledge_points:
            assert kp.text
            assert kp.kind in KnowledgeType
            assert kp.confidence >= 0.5
            assert kp.anchors
            assert "chapter_id" in kp.anchors
            assert kp.anchors["chapter_id"] == "ch1"
            assert "extraction_method" in kp.anchors
    
    def test_calculate_rule_confidence(self, knowledge_service):
        """Test confidence calculation for rule-based extraction."""
        import re
        
        # Test with a definition pattern match
        text = "Machine learning is a subset of artificial intelligence."
        pattern = re.compile(r'(.+?)\s+(?:is|are)\s+(.+?)(?:\.|$)', re.IGNORECASE)
        match = pattern.search(text)
        
        assert match is not None
        
        confidence = knowledge_service._calculate_rule_confidence(
            KnowledgeType.DEFINITION, match, text
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.5  # Should be reasonably confident for definitions
    
    def test_deduplicate_knowledge_points(self, knowledge_service):
        """Test deduplication of similar knowledge points."""
        
        # Create duplicate knowledge points
        kp1 = ExtractedKnowledge(
            text="Machine learning is a subset of AI",
            kind=KnowledgeType.DEFINITION,
            entities=["machine learning", "AI"],
            confidence=0.8,
            anchors={"page": 1}
        )
        
        kp2 = ExtractedKnowledge(
            text="Machine learning is a subset of artificial intelligence",
            kind=KnowledgeType.DEFINITION,
            entities=["machine learning", "artificial intelligence"],
            confidence=0.9,
            anchors={"page": 1}
        )
        
        kp3 = ExtractedKnowledge(
            text="Neural networks are computational models",
            kind=KnowledgeType.DEFINITION,
            entities=["neural networks"],
            confidence=0.7,
            anchors={"page": 2}
        )
        
        knowledge_points = [kp1, kp2, kp3]
        deduplicated = knowledge_service._deduplicate_knowledge_points(knowledge_points)
        
        # Should remove one of the similar definitions
        assert len(deduplicated) == 2
        
        # Should keep the higher confidence one
        ml_definitions = [kp for kp in deduplicated if "machine learning" in kp.text.lower()]
        assert len(ml_definitions) == 1
        assert ml_definitions[0].confidence == 0.9  # Higher confidence one kept
    
    def test_calculate_text_overlap(self, knowledge_service):
        """Test text overlap calculation."""
        
        text1 = "Machine learning is a subset of artificial intelligence"
        text2 = "Machine learning is part of artificial intelligence"
        text3 = "Neural networks are computational models"
        
        # High overlap
        overlap1 = knowledge_service._calculate_text_overlap(text1, text2)
        assert overlap1 > 0.7
        
        # Low overlap
        overlap2 = knowledge_service._calculate_text_overlap(text1, text3)
        assert overlap2 < 0.3
        
        # Identical texts
        overlap3 = knowledge_service._calculate_text_overlap(text1, text1)
        assert overlap3 == 1.0
    
    def test_get_extraction_statistics(self, knowledge_service):
        """Test extraction statistics generation."""
        
        knowledge_points = [
            ExtractedKnowledge(
                text="Definition 1",
                kind=KnowledgeType.DEFINITION,
                entities=["term1"],
                confidence=0.8,
                anchors={"extraction_method": "rule_based"}
            ),
            ExtractedKnowledge(
                text="Definition 2",
                kind=KnowledgeType.DEFINITION,
                entities=["term2"],
                confidence=0.9,
                anchors={"extraction_method": "rule_based"}
            ),
            ExtractedKnowledge(
                text="Example 1",
                kind=KnowledgeType.EXAMPLE,
                entities=["term3"],
                confidence=0.7,
                anchors={"extraction_method": "llm"}
            )
        ]
        
        stats = knowledge_service.get_extraction_statistics(knowledge_points)
        
        assert stats["total_knowledge_points"] == 3
        assert stats["by_type"]["definition"] == 2
        assert stats["by_type"]["example"] == 1
        assert stats["avg_confidence"] == 0.8  # (0.8 + 0.9 + 0.7) / 3
        assert stats["extraction_methods"]["rule_based"] == 2
        assert stats["extraction_methods"]["llm"] == 1
        assert "highest_confidence" in stats
    
    def test_empty_segments(self, knowledge_service):
        """Test handling of empty segments."""
        
        @pytest.mark.asyncio
        async def test_empty():
            knowledge_points = await knowledge_service.extract_knowledge_from_segments([], "ch1")
            assert knowledge_points == []
        
        # Run the async test
        import asyncio
        asyncio.run(test_empty())
    
    def test_configuration_options(self):
        """Test different configuration options."""
        
        # Test with LLM enabled
        config_llm = KnowledgeExtractionConfig(
            use_llm=True,
            enable_fallback=False,
            min_confidence=0.8
        )
        service_llm = KnowledgeExtractionService(config_llm)
        assert service_llm.config.use_llm is True
        assert service_llm.config.enable_fallback is False
        assert service_llm.config.min_confidence == 0.8
        
        # Test with custom patterns
        custom_patterns = ["custom pattern 1", "custom pattern 2"]
        config_custom = KnowledgeExtractionConfig(
            definition_patterns=custom_patterns
        )
        service_custom = KnowledgeExtractionService(config_custom)
        assert service_custom.config.definition_patterns == custom_patterns
    
    @pytest.mark.asyncio
    async def test_error_handling(self, knowledge_service):
        """Test error handling in knowledge extraction."""
        
        # Test with malformed segment
        malformed_segment = TextSegment(
            text="",  # Empty text
            character_count=0,
            word_count=0,
            sentence_count=0,
            anchors={}
        )
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.side_effect = Exception("Entity extraction failed")
            
            # Should not raise exception, but return empty list
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [malformed_segment], "ch1"
            )
            
            assert knowledge_points == []
    
    def test_llm_prompt_creation(self, knowledge_service):
        """Test LLM prompt creation."""
        
        text = "Machine learning is a subset of artificial intelligence."
        entities = ["machine learning", "artificial intelligence"]
        
        prompt = knowledge_service._create_llm_prompt(text, entities)
        
        assert text in prompt
        assert "machine learning" in prompt
        assert "artificial intelligence" in prompt
        assert "JSON" in prompt
        assert "definition" in prompt
        assert "fact" in prompt
        assert "theorem" in prompt
        assert "process" in prompt
        assert "example" in prompt
        assert "concept" in prompt
    
    @pytest.mark.asyncio
    async def test_confidence_filtering(self, knowledge_service):
        """Test that low confidence knowledge points are filtered out."""
        
        # Set high minimum confidence
        knowledge_service.config.min_confidence = 0.9
        
        segment = TextSegment(
            text="This is a weak example of something.",
            character_count=35,
            word_count=7,
            sentence_count=1,
            anchors={"page": 1, "chapter_id": "ch1"}
        )
        
        with patch.object(knowledge_service.entity_extraction, 'extract_entities') as mock_entities:
            mock_entities.return_value = []
            
            knowledge_points = await knowledge_service.extract_knowledge_from_segments(
                [segment], "ch1"
            )
            
            # Should filter out low confidence matches
            for kp in knowledge_points:
                assert kp.confidence >= 0.9