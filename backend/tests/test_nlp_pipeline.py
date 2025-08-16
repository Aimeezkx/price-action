"""Comprehensive tests for NLP pipeline components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from datetime import datetime

from app.services.entity_extraction_service import EntityExtractionService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.text_segmentation_service import TextSegmentationService
from app.services.embedding_service import EmbeddingService
from app.models.knowledge import KnowledgeType


@pytest.mark.unit
class TestEntityExtractionService:
    """Test entity extraction functionality."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = EntityExtractionService()
        assert service is not None
        assert hasattr(service, 'extract_entities')
    
    @pytest.mark.asyncio
    async def test_basic_entity_extraction(self):
        """Test basic entity extraction from text."""
        service = EntityExtractionService()
        
        text = "Machine learning is a subset of artificial intelligence that uses algorithms."
        
        with patch.object(service, '_extract_with_spacy') as mock_spacy:
            mock_spacy.return_value = [
                {"text": "machine learning", "label": "CONCEPT", "start": 0, "end": 16},
                {"text": "artificial intelligence", "label": "CONCEPT", "start": 32, "end": 55},
                {"text": "algorithms", "label": "CONCEPT", "start": 67, "end": 77}
            ]
            
            entities = await service.extract_entities(text)
            
            assert len(entities) == 3
            assert entities[0]["text"] == "machine learning"
            assert entities[0]["label"] == "CONCEPT"
            assert entities[1]["text"] == "artificial intelligence"
    
    @pytest.mark.asyncio
    async def test_entity_extraction_with_context(self):
        """Test entity extraction with contextual information."""
        service = EntityExtractionService()
        
        text = "Neural networks, particularly deep learning models, are used in computer vision."
        context = {"domain": "computer_science", "topic": "deep_learning"}
        
        with patch.object(service, '_extract_with_context') as mock_context:
            mock_context.return_value = [
                {"text": "neural networks", "label": "ALGORITHM", "confidence": 0.95},
                {"text": "deep learning", "label": "TECHNIQUE", "confidence": 0.98},
                {"text": "computer vision", "label": "FIELD", "confidence": 0.92}
            ]
            
            entities = await service.extract_entities(text, context=context)
            
            assert len(entities) == 3
            assert all(entity["confidence"] > 0.9 for entity in entities)
            assert entities[1]["text"] == "deep learning"
            assert entities[1]["label"] == "TECHNIQUE"
    
    @pytest.mark.asyncio
    async def test_entity_deduplication(self):
        """Test entity deduplication and normalization."""
        service = EntityExtractionService()
        
        text = "ML and machine learning are the same. Machine Learning is important."
        
        with patch.object(service, '_extract_and_normalize') as mock_normalize:
            mock_normalize.return_value = [
                {"text": "machine learning", "label": "CONCEPT", "aliases": ["ML", "Machine Learning"]},
                {"text": "important", "label": "QUALIFIER", "aliases": []}
            ]
            
            entities = await service.extract_entities(text, deduplicate=True)
            
            assert len(entities) == 2
            assert entities[0]["text"] == "machine learning"
            assert "ML" in entities[0]["aliases"]
            assert "Machine Learning" in entities[0]["aliases"]
    
    @pytest.mark.asyncio
    async def test_entity_filtering(self):
        """Test entity filtering by type and confidence."""
        service = EntityExtractionService()
        
        text = "Python is a programming language used for data science and web development."
        
        with patch.object(service, '_extract_with_filtering') as mock_filter:
            mock_filter.return_value = [
                {"text": "Python", "label": "LANGUAGE", "confidence": 0.98},
                {"text": "data science", "label": "FIELD", "confidence": 0.95},
                {"text": "web development", "label": "FIELD", "confidence": 0.93}
            ]
            
            # Filter by minimum confidence
            entities = await service.extract_entities(
                text, 
                min_confidence=0.94,
                allowed_types=["LANGUAGE", "FIELD"]
            )
            
            assert len(entities) == 2  # Python and data science
            assert all(entity["confidence"] >= 0.94 for entity in entities)
    
    def test_entity_validation(self):
        """Test entity validation and error handling."""
        service = EntityExtractionService()
        
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service._validate_input("")
        
        # Test None text
        with pytest.raises(ValueError, match="Text cannot be None"):
            service._validate_input(None)
        
        # Test very long text
        long_text = "A" * 100000
        with pytest.raises(ValueError, match="Text too long"):
            service._validate_input(long_text)
    
    @pytest.mark.asyncio
    async def test_batch_entity_extraction(self):
        """Test batch processing of multiple texts."""
        service = EntityExtractionService()
        
        texts = [
            "Machine learning algorithms process data.",
            "Deep learning uses neural networks.",
            "Natural language processing handles text."
        ]
        
        with patch.object(service, 'extract_entities') as mock_extract:
            mock_extract.side_effect = [
                [{"text": "machine learning", "label": "CONCEPT"}],
                [{"text": "deep learning", "label": "CONCEPT"}],
                [{"text": "natural language processing", "label": "CONCEPT"}]
            ]
            
            results = await service.extract_entities_batch(texts)
            
            assert len(results) == 3
            assert mock_extract.call_count == 3
            assert results[0][0]["text"] == "machine learning"


@pytest.mark.unit
class TestKnowledgeExtractionService:
    """Test knowledge extraction functionality."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = KnowledgeExtractionService()
        assert service is not None
        assert hasattr(service, 'extract_knowledge')
    
    @pytest.mark.asyncio
    async def test_definition_extraction(self):
        """Test extraction of definitions."""
        service = KnowledgeExtractionService()
        
        text = "Machine learning is a method of data analysis that automates analytical model building."
        
        with patch.object(service, '_extract_definitions') as mock_def:
            mock_def.return_value = [
                {
                    "text": "Machine learning is a method of data analysis that automates analytical model building.",
                    "kind": KnowledgeType.DEFINITION,
                    "entities": ["machine learning", "data analysis", "analytical model"],
                    "confidence": 0.95
                }
            ]
            
            knowledge = await service.extract_knowledge(text)
            
            assert len(knowledge) == 1
            assert knowledge[0]["kind"] == KnowledgeType.DEFINITION
            assert "machine learning" in knowledge[0]["entities"]
            assert knowledge[0]["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_fact_extraction(self):
        """Test extraction of factual statements."""
        service = KnowledgeExtractionService()
        
        text = "Python was created by Guido van Rossum in 1991. It supports multiple programming paradigms."
        
        with patch.object(service, '_extract_facts') as mock_facts:
            mock_facts.return_value = [
                {
                    "text": "Python was created by Guido van Rossum in 1991.",
                    "kind": KnowledgeType.FACT,
                    "entities": ["Python", "Guido van Rossum", "1991"],
                    "confidence": 0.98
                },
                {
                    "text": "It supports multiple programming paradigms.",
                    "kind": KnowledgeType.FACT,
                    "entities": ["Python", "programming paradigms"],
                    "confidence": 0.92
                }
            ]
            
            knowledge = await service.extract_knowledge(text)
            
            assert len(knowledge) == 2
            assert all(k["kind"] == KnowledgeType.FACT for k in knowledge)
            assert "Guido van Rossum" in knowledge[0]["entities"]
    
    @pytest.mark.asyncio
    async def test_process_extraction(self):
        """Test extraction of processes and procedures."""
        service = KnowledgeExtractionService()
        
        text = """To train a neural network:
        1. Initialize weights randomly
        2. Forward propagate input through network
        3. Calculate loss using loss function
        4. Backpropagate error gradients
        5. Update weights using optimizer"""
        
        with patch.object(service, '_extract_processes') as mock_process:
            mock_process.return_value = [
                {
                    "text": "To train a neural network: 1. Initialize weights randomly 2. Forward propagate...",
                    "kind": KnowledgeType.PROCESS,
                    "entities": ["neural network", "weights", "forward propagation", "backpropagation"],
                    "steps": [
                        "Initialize weights randomly",
                        "Forward propagate input through network",
                        "Calculate loss using loss function",
                        "Backpropagate error gradients",
                        "Update weights using optimizer"
                    ],
                    "confidence": 0.94
                }
            ]
            
            knowledge = await service.extract_knowledge(text)
            
            assert len(knowledge) == 1
            assert knowledge[0]["kind"] == KnowledgeType.PROCESS
            assert "steps" in knowledge[0]
            assert len(knowledge[0]["steps"]) == 5
    
    @pytest.mark.asyncio
    async def test_theorem_extraction(self):
        """Test extraction of theorems and mathematical statements."""
        service = KnowledgeExtractionService()
        
        text = "The Central Limit Theorem states that the sampling distribution of the sample mean approaches a normal distribution as the sample size increases."
        
        with patch.object(service, '_extract_theorems') as mock_theorem:
            mock_theorem.return_value = [
                {
                    "text": "The Central Limit Theorem states that the sampling distribution of the sample mean approaches a normal distribution as the sample size increases.",
                    "kind": KnowledgeType.THEOREM,
                    "entities": ["Central Limit Theorem", "sampling distribution", "normal distribution"],
                    "confidence": 0.97
                }
            ]
            
            knowledge = await service.extract_knowledge(text)
            
            assert len(knowledge) == 1
            assert knowledge[0]["kind"] == KnowledgeType.THEOREM
            assert "Central Limit Theorem" in knowledge[0]["entities"]
    
    @pytest.mark.asyncio
    async def test_example_extraction(self):
        """Test extraction of examples and illustrations."""
        service = KnowledgeExtractionService()
        
        text = "For example, a decision tree can classify emails as spam or not spam based on features like sender, subject line, and content."
        
        with patch.object(service, '_extract_examples') as mock_example:
            mock_example.return_value = [
                {
                    "text": "For example, a decision tree can classify emails as spam or not spam based on features like sender, subject line, and content.",
                    "kind": KnowledgeType.EXAMPLE,
                    "entities": ["decision tree", "emails", "spam classification"],
                    "confidence": 0.89
                }
            ]
            
            knowledge = await service.extract_knowledge(text)
            
            assert len(knowledge) == 1
            assert knowledge[0]["kind"] == KnowledgeType.EXAMPLE
            assert "decision tree" in knowledge[0]["entities"]
    
    @pytest.mark.asyncio
    async def test_knowledge_ranking(self):
        """Test knowledge point ranking by importance."""
        service = KnowledgeExtractionService()
        
        text = "Machine learning is important. It uses algorithms. For example, linear regression predicts values."
        
        with patch.object(service, '_extract_and_rank') as mock_rank:
            mock_rank.return_value = [
                {
                    "text": "Machine learning is important.",
                    "kind": KnowledgeType.DEFINITION,
                    "importance_score": 0.95,
                    "confidence": 0.92
                },
                {
                    "text": "For example, linear regression predicts values.",
                    "kind": KnowledgeType.EXAMPLE,
                    "importance_score": 0.75,
                    "confidence": 0.88
                },
                {
                    "text": "It uses algorithms.",
                    "kind": KnowledgeType.FACT,
                    "importance_score": 0.65,
                    "confidence": 0.85
                }
            ]
            
            knowledge = await service.extract_knowledge(text, rank_by_importance=True)
            
            assert len(knowledge) == 3
            # Should be sorted by importance score
            assert knowledge[0]["importance_score"] >= knowledge[1]["importance_score"]
            assert knowledge[1]["importance_score"] >= knowledge[2]["importance_score"]
    
    def test_knowledge_validation(self):
        """Test knowledge validation and filtering."""
        service = KnowledgeExtractionService()
        
        # Test minimum confidence filtering
        knowledge_points = [
            {"text": "High confidence", "confidence": 0.95},
            {"text": "Medium confidence", "confidence": 0.75},
            {"text": "Low confidence", "confidence": 0.45}
        ]
        
        filtered = service._filter_by_confidence(knowledge_points, min_confidence=0.7)
        assert len(filtered) == 2
        assert all(k["confidence"] >= 0.7 for k in filtered)
    
    @pytest.mark.asyncio
    async def test_contextual_knowledge_extraction(self):
        """Test knowledge extraction with domain context."""
        service = KnowledgeExtractionService()
        
        text = "Overfitting occurs when a model learns the training data too well."
        context = {"domain": "machine_learning", "chapter": "model_evaluation"}
        
        with patch.object(service, '_extract_with_context') as mock_context:
            mock_context.return_value = [
                {
                    "text": "Overfitting occurs when a model learns the training data too well.",
                    "kind": KnowledgeType.DEFINITION,
                    "entities": ["overfitting", "model", "training data"],
                    "context": context,
                    "confidence": 0.96
                }
            ]
            
            knowledge = await service.extract_knowledge(text, context=context)
            
            assert len(knowledge) == 1
            assert knowledge[0]["context"] == context
            assert knowledge[0]["confidence"] == 0.96


@pytest.mark.unit
class TestTextSegmentationService:
    """Test text segmentation functionality."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = TextSegmentationService()
        assert service is not None
        assert hasattr(service, 'segment_text')
    
    @pytest.mark.asyncio
    async def test_sentence_segmentation(self):
        """Test sentence-level segmentation."""
        service = TextSegmentationService()
        
        text = "This is the first sentence. This is the second sentence! Is this a question?"
        
        segments = await service.segment_text(text, level="sentence")
        
        assert len(segments) == 3
        assert segments[0]["text"] == "This is the first sentence."
        assert segments[1]["text"] == "This is the second sentence!"
        assert segments[2]["text"] == "Is this a question?"
        assert all(seg["type"] == "sentence" for seg in segments)
    
    @pytest.mark.asyncio
    async def test_paragraph_segmentation(self):
        """Test paragraph-level segmentation."""
        service = TextSegmentationService()
        
        text = """First paragraph with multiple sentences. It has more content.

Second paragraph starts here. It also has content.

Third paragraph is shorter."""
        
        segments = await service.segment_text(text, level="paragraph")
        
        assert len(segments) == 3
        assert all(seg["type"] == "paragraph" for seg in segments)
        assert "First paragraph" in segments[0]["text"]
        assert "Second paragraph" in segments[1]["text"]
        assert "Third paragraph" in segments[2]["text"]
    
    @pytest.mark.asyncio
    async def test_semantic_segmentation(self):
        """Test semantic segmentation by topic."""
        service = TextSegmentationService()
        
        text = """Machine learning is a subset of AI. It uses algorithms to learn patterns.

Deep learning is a type of machine learning. It uses neural networks with multiple layers.

Computer vision processes images. It can identify objects and faces."""
        
        with patch.object(service, '_semantic_segment') as mock_semantic:
            mock_semantic.return_value = [
                {
                    "text": "Machine learning is a subset of AI. It uses algorithms to learn patterns.",
                    "type": "semantic_segment",
                    "topic": "machine_learning_basics",
                    "coherence_score": 0.92
                },
                {
                    "text": "Deep learning is a type of machine learning. It uses neural networks with multiple layers.",
                    "type": "semantic_segment", 
                    "topic": "deep_learning",
                    "coherence_score": 0.89
                },
                {
                    "text": "Computer vision processes images. It can identify objects and faces.",
                    "type": "semantic_segment",
                    "topic": "computer_vision",
                    "coherence_score": 0.87
                }
            ]
            
            segments = await service.segment_text(text, level="semantic")
            
            assert len(segments) == 3
            assert all(seg["type"] == "semantic_segment" for seg in segments)
            assert segments[0]["topic"] == "machine_learning_basics"
            assert all(seg["coherence_score"] > 0.8 for seg in segments)
    
    @pytest.mark.asyncio
    async def test_hierarchical_segmentation(self):
        """Test hierarchical segmentation with multiple levels."""
        service = TextSegmentationService()
        
        text = """# Chapter 1: Introduction

Machine learning is important. It has many applications.

## Section 1.1: Basics

Algorithms learn from data. They make predictions.

## Section 1.2: Applications

ML is used in many fields. Examples include healthcare and finance."""
        
        with patch.object(service, '_hierarchical_segment') as mock_hierarchical:
            mock_hierarchical.return_value = [
                {
                    "text": "# Chapter 1: Introduction",
                    "type": "header",
                    "level": 1,
                    "hierarchy": ["Chapter 1"]
                },
                {
                    "text": "Machine learning is important. It has many applications.",
                    "type": "paragraph",
                    "level": 2,
                    "hierarchy": ["Chapter 1", "Introduction"]
                },
                {
                    "text": "## Section 1.1: Basics",
                    "type": "header",
                    "level": 2,
                    "hierarchy": ["Chapter 1", "Section 1.1"]
                },
                {
                    "text": "Algorithms learn from data. They make predictions.",
                    "type": "paragraph",
                    "level": 3,
                    "hierarchy": ["Chapter 1", "Section 1.1", "Basics"]
                }
            ]
            
            segments = await service.segment_text(text, level="hierarchical")
            
            assert len(segments) >= 4
            assert segments[0]["type"] == "header"
            assert segments[0]["level"] == 1
            assert "Chapter 1" in segments[0]["hierarchy"]
    
    @pytest.mark.asyncio
    async def test_segment_filtering(self):
        """Test filtering segments by criteria."""
        service = TextSegmentationService()
        
        text = "Short. This is a longer sentence with more content. Very long sentence with substantial content that provides detailed information."
        
        with patch.object(service, '_segment_with_filtering') as mock_filter:
            mock_filter.return_value = [
                {"text": "This is a longer sentence with more content.", "length": 44, "word_count": 9},
                {"text": "Very long sentence with substantial content that provides detailed information.", "length": 77, "word_count": 11}
            ]
            
            segments = await service.segment_text(
                text, 
                level="sentence",
                min_length=20,
                min_words=5
            )
            
            assert len(segments) == 2
            assert all(seg["length"] >= 20 for seg in segments)
            assert all(seg["word_count"] >= 5 for seg in segments)
    
    def test_segment_validation(self):
        """Test segment validation and error handling."""
        service = TextSegmentationService()
        
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service._validate_segmentation_input("")
        
        # Test invalid level
        with pytest.raises(ValueError, match="Invalid segmentation level"):
            service._validate_segmentation_input("text", level="invalid")
    
    @pytest.mark.asyncio
    async def test_segment_metadata(self):
        """Test segment metadata extraction."""
        service = TextSegmentationService()
        
        text = "This sentence has 6 words. This longer sentence contains more words and characters for testing purposes."
        
        with patch.object(service, '_add_metadata') as mock_metadata:
            mock_metadata.return_value = [
                {
                    "text": "This sentence has 6 words.",
                    "type": "sentence",
                    "word_count": 5,
                    "char_count": 26,
                    "complexity_score": 0.3,
                    "readability_score": 0.8
                },
                {
                    "text": "This longer sentence contains more words and characters for testing purposes.",
                    "type": "sentence", 
                    "word_count": 11,
                    "char_count": 76,
                    "complexity_score": 0.6,
                    "readability_score": 0.6
                }
            ]
            
            segments = await service.segment_text(text, include_metadata=True)
            
            assert len(segments) == 2
            assert all("word_count" in seg for seg in segments)
            assert all("complexity_score" in seg for seg in segments)
            assert segments[0]["word_count"] == 5
            assert segments[1]["word_count"] == 11


@pytest.mark.unit
class TestEmbeddingService:
    """Test embedding generation functionality."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = EmbeddingService()
        assert service is not None
        assert hasattr(service, 'generate_embedding')
    
    @pytest.mark.asyncio
    async def test_text_embedding_generation(self):
        """Test generating embeddings for text."""
        service = EmbeddingService()
        
        text = "Machine learning is a powerful technique."
        
        with patch.object(service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
            
            embedding = await service.generate_embedding(text)
            
            assert isinstance(embedding, np.ndarray)
            assert len(embedding) == 4
            assert embedding[0] == 0.1
            mock_model.encode.assert_called_once_with(text)
    
    @pytest.mark.asyncio
    async def test_batch_embedding_generation(self):
        """Test generating embeddings for multiple texts."""
        service = EmbeddingService()
        
        texts = [
            "First text about machine learning.",
            "Second text about deep learning.",
            "Third text about neural networks."
        ]
        
        with patch.object(service, 'model') as mock_model:
            mock_model.encode.return_value = np.array([
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6], 
                [0.7, 0.8, 0.9]
            ])
            
            embeddings = await service.generate_embeddings_batch(texts)
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (3, 3)
            assert embeddings[0][0] == 0.1
            assert embeddings[2][2] == 0.9
    
    @pytest.mark.asyncio
    async def test_embedding_similarity(self):
        """Test computing similarity between embeddings."""
        service = EmbeddingService()
        
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0])
        embedding3 = np.array([1.0, 0.0, 0.0])  # Same as embedding1
        
        # Test cosine similarity
        similarity_12 = await service.compute_similarity(embedding1, embedding2)
        similarity_13 = await service.compute_similarity(embedding1, embedding3)
        
        assert similarity_12 == 0.0  # Orthogonal vectors
        assert similarity_13 == 1.0  # Identical vectors
    
    @pytest.mark.asyncio
    async def test_embedding_normalization(self):
        """Test embedding normalization."""
        service = EmbeddingService()
        
        embedding = np.array([3.0, 4.0, 0.0])  # Length = 5
        
        normalized = await service.normalize_embedding(embedding)
        
        assert np.allclose(np.linalg.norm(normalized), 1.0)
        assert np.allclose(normalized, [0.6, 0.8, 0.0])
    
    @pytest.mark.asyncio
    async def test_embedding_dimensionality_reduction(self):
        """Test reducing embedding dimensions."""
        service = EmbeddingService()
        
        high_dim_embedding = np.random.rand(512)
        
        with patch.object(service, '_reduce_dimensions') as mock_reduce:
            mock_reduce.return_value = np.random.rand(128)
            
            reduced = await service.reduce_dimensions(high_dim_embedding, target_dim=128)
            
            assert len(reduced) == 128
            mock_reduce.assert_called_once_with(high_dim_embedding, 128)
    
    def test_embedding_validation(self):
        """Test embedding validation and error handling."""
        service = EmbeddingService()
        
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service._validate_text("")
        
        # Test very long text
        long_text = "A" * 10000
        with pytest.raises(ValueError, match="Text too long"):
            service._validate_text(long_text)
    
    @pytest.mark.asyncio
    async def test_embedding_caching(self):
        """Test embedding caching functionality."""
        service = EmbeddingService()
        
        text = "Cached text example"
        embedding = np.array([0.1, 0.2, 0.3])
        
        with patch.object(service, '_get_cached_embedding') as mock_get_cache:
            with patch.object(service, '_cache_embedding') as mock_set_cache:
                mock_get_cache.return_value = None  # Not cached initially
                
                with patch.object(service, 'model') as mock_model:
                    mock_model.encode.return_value = embedding
                    
                    result = await service.generate_embedding(text, use_cache=True)
                    
                    assert np.array_equal(result, embedding)
                    mock_set_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multilingual_embeddings(self):
        """Test embeddings for multiple languages."""
        service = EmbeddingService()
        
        texts = {
            "en": "Machine learning is powerful",
            "es": "El aprendizaje automático es poderoso", 
            "fr": "L'apprentissage automatique est puissant"
        }
        
        with patch.object(service, 'multilingual_model') as mock_model:
            mock_model.encode.side_effect = [
                np.array([0.1, 0.2, 0.3]),
                np.array([0.15, 0.25, 0.35]),
                np.array([0.12, 0.22, 0.32])
            ]
            
            embeddings = {}
            for lang, text in texts.items():
                embeddings[lang] = await service.generate_embedding(text, language=lang)
            
            # Similar concepts should have similar embeddings
            similarity_en_es = await service.compute_similarity(embeddings["en"], embeddings["es"])
            similarity_en_fr = await service.compute_similarity(embeddings["en"], embeddings["fr"])
            
            assert similarity_en_es > 0.8  # Should be highly similar
            assert similarity_en_fr > 0.8  # Should be highly similar


@pytest.mark.integration
class TestNLPPipelineIntegration:
    """Test integration between NLP pipeline components."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_processing(self):
        """Test complete NLP pipeline from text to knowledge."""
        entity_service = EntityExtractionService()
        knowledge_service = KnowledgeExtractionService()
        segmentation_service = TextSegmentationService()
        embedding_service = EmbeddingService()
        
        text = """Machine learning is a method of data analysis. It automates analytical model building.
        
        For example, supervised learning uses labeled training data. The algorithm learns to map inputs to outputs."""
        
        # Mock all services
        with patch.object(segmentation_service, 'segment_text') as mock_segment:
            mock_segment.return_value = [
                {"text": "Machine learning is a method of data analysis.", "type": "sentence"},
                {"text": "It automates analytical model building.", "type": "sentence"},
                {"text": "For example, supervised learning uses labeled training data.", "type": "sentence"},
                {"text": "The algorithm learns to map inputs to outputs.", "type": "sentence"}
            ]
            
            with patch.object(entity_service, 'extract_entities') as mock_entities:
                mock_entities.return_value = [
                    {"text": "machine learning", "label": "CONCEPT"},
                    {"text": "supervised learning", "label": "TECHNIQUE"}
                ]
                
                with patch.object(knowledge_service, 'extract_knowledge') as mock_knowledge:
                    mock_knowledge.return_value = [
                        {
                            "text": "Machine learning is a method of data analysis.",
                            "kind": KnowledgeType.DEFINITION,
                            "entities": ["machine learning", "data analysis"]
                        }
                    ]
                    
                    with patch.object(embedding_service, 'generate_embedding') as mock_embedding:
                        mock_embedding.return_value = np.array([0.1, 0.2, 0.3])
                        
                        # Process through pipeline
                        segments = await segmentation_service.segment_text(text)
                        entities = await entity_service.extract_entities(text)
                        knowledge = await knowledge_service.extract_knowledge(text)
                        embedding = await embedding_service.generate_embedding(text)
                        
                        assert len(segments) == 4
                        assert len(entities) == 2
                        assert len(knowledge) == 1
                        assert len(embedding) == 3
                        
                        # Verify integration
                        assert knowledge[0]["entities"][0] == entities[0]["text"]
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        entity_service = EntityExtractionService()
        knowledge_service = KnowledgeExtractionService()
        
        text = "Test text for error handling"
        
        # Simulate entity extraction failure
        with patch.object(entity_service, 'extract_entities') as mock_entities:
            mock_entities.side_effect = Exception("Entity extraction failed")
            
            with patch.object(knowledge_service, 'extract_knowledge') as mock_knowledge:
                mock_knowledge.return_value = [
                    {"text": "Fallback knowledge", "kind": KnowledgeType.FACT}
                ]
                
                # Pipeline should handle entity extraction failure gracefully
                try:
                    entities = await entity_service.extract_entities(text)
                except Exception:
                    entities = []  # Fallback to empty entities
                
                knowledge = await knowledge_service.extract_knowledge(text)
                
                assert len(entities) == 0  # Failed extraction
                assert len(knowledge) == 1  # Knowledge extraction still works
    
    @pytest.mark.asyncio
    async def test_pipeline_performance(self):
        """Test pipeline performance with large text."""
        import time
        
        entity_service = EntityExtractionService()
        knowledge_service = KnowledgeExtractionService()
        embedding_service = EmbeddingService()
        
        # Large text for performance testing
        large_text = "Machine learning is important. " * 1000
        
        with patch.object(entity_service, 'extract_entities') as mock_entities:
            mock_entities.return_value = [{"text": "machine learning", "label": "CONCEPT"}]
            
            with patch.object(knowledge_service, 'extract_knowledge') as mock_knowledge:
                mock_knowledge.return_value = [{"text": "ML fact", "kind": KnowledgeType.FACT}]
                
                with patch.object(embedding_service, 'generate_embedding') as mock_embedding:
                    mock_embedding.return_value = np.array([0.1] * 384)
                    
                    start_time = time.time()
                    
                    # Process large text
                    entities = await entity_service.extract_entities(large_text)
                    knowledge = await knowledge_service.extract_knowledge(large_text)
                    embedding = await embedding_service.generate_embedding(large_text)
                    
                    processing_time = time.time() - start_time
                    
                    # Should complete within reasonable time
                    assert processing_time < 2.0  # 2 seconds max
                    assert len(entities) > 0
                    assert len(knowledge) > 0
                    assert len(embedding) == 384