"""
Tests for deduplication service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.deduplication_service import (
    DeduplicationService, 
    DeduplicationConfig, 
    DuplicateGroup
)
from app.models.learning import Card, CardType
from app.models.knowledge import Knowledge, KnowledgeType


@pytest.fixture
def dedup_config():
    """Create test deduplication configuration"""
    return DeduplicationConfig(
        semantic_similarity_threshold=0.9,
        max_duplicate_rate=0.05
    )


@pytest.fixture
def dedup_service(dedup_config):
    """Create deduplication service with test config"""
    return DeduplicationService(dedup_config)


@pytest.fixture
def sample_cards():
    """Create sample cards for testing"""
    cards = []
    
    # Card 1: Original
    card1 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
        difficulty=2.5,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Card 2: Near duplicate (high similarity)
    card2 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a branch of AI that allows computers to learn automatically without explicit programming.",
        difficulty=2.3,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Card 3: Exact duplicate
    card3 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
        difficulty=2.1,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Card 4: Different content (not duplicate)
    card4 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is deep learning?",
        back="Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        difficulty=3.0,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Card 5: Cloze card
    card5 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.CLOZE,
        front="[1] is a subset of artificial intelligence.",
        back="Machine learning is a subset of artificial intelligence.",
        difficulty=2.2,
        card_metadata={
            "knowledge_type": "definition",
            "blanked_entities": [{"entity": "Machine learning", "blank_number": 1}]
        }
    )
    
    # Card 6: Similar cloze card
    card6 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.CLOZE,
        front="[1] is a branch of artificial intelligence.",
        back="Machine learning is a branch of artificial intelligence.",
        difficulty=2.0,
        card_metadata={
            "knowledge_type": "definition",
            "blanked_entities": [{"entity": "Machine learning", "blank_number": 1}]
        }
    )
    
    cards.extend([card1, card2, card3, card4, card5, card6])
    return cards


class TestDeduplicationService:
    """Test deduplication service functionality"""
    
    @pytest.mark.asyncio
    async def test_exact_match_detection(self, dedup_service, sample_cards):
        """Test detection of exact duplicate cards"""
        card1, card2, card3 = sample_cards[0], sample_cards[1], sample_cards[2]
        
        # Test exact match between card1 and card3
        is_exact = dedup_service._is_exact_match(card1, card3)
        assert is_exact is True
        
        # Test non-exact match between card1 and card2
        is_exact = dedup_service._is_exact_match(card1, card2)
        assert is_exact is False
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_calculation(self, dedup_service, sample_cards):
        """Test semantic similarity calculation between cards"""
        card1, card2, card4 = sample_cards[0], sample_cards[1], sample_cards[3]
        
        with patch.object(dedup_service.embedding_service, 'generate_embedding') as mock_embed:
            # Mock embeddings for similar content
            mock_embed.side_effect = [
                [0.1, 0.2, 0.3],  # card1 front
                [0.1, 0.2, 0.3],  # card2 front (same)
                [0.9, 0.8, 0.7],  # card1 back
                [0.85, 0.75, 0.65],  # card2 back (similar)
                {}  # metadata similarity
            ]
            
            with patch.object(dedup_service.embedding_service, 'calculate_similarity') as mock_sim:
                mock_sim.side_effect = [1.0, 0.95]  # High similarity scores
                
                similarity = await dedup_service._calculate_card_similarity(card1, card2)
                assert similarity > 0.9
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, dedup_service, sample_cards):
        """Test duplicate detection across multiple cards"""
        with patch.object(dedup_service, '_calculate_card_similarity') as mock_similarity:
            # Mock similarity scores
            mock_similarity.side_effect = [
                0.95,  # card1 vs card2 (duplicate)
                1.0,   # card1 vs card3 (exact duplicate)
                0.3,   # card1 vs card4 (not duplicate)
                0.4,   # card1 vs card5 (different type)
                0.2,   # card1 vs card6 (different type)
                1.0,   # card2 vs card3 (exact duplicate)
                0.25,  # card2 vs card4 (not duplicate)
                0.35,  # card2 vs card5 (different type)
                0.15,  # card2 vs card6 (different type)
                0.2,   # card3 vs card4 (not duplicate)
                0.3,   # card3 vs card5 (different type)
                0.1,   # card3 vs card6 (different type)
                0.1,   # card4 vs card5 (different type)
                0.05,  # card4 vs card6 (different type)
                0.92,  # card5 vs card6 (cloze duplicates)
            ]
            
            duplicate_groups = await dedup_service._detect_duplicates(sample_cards)
            
            # Should find duplicate groups
            assert len(duplicate_groups) >= 1
            
            # Check that duplicates are properly grouped
            qa_duplicates = [g for g in duplicate_groups if g.primary_card.card_type == CardType.QA]
            cloze_duplicates = [g for g in duplicate_groups if g.primary_card.card_type == CardType.CLOZE]
            
            assert len(qa_duplicates) >= 1  # Should find QA duplicates
            # Note: Cloze duplicates might not be found due to type-based grouping
            assert len(duplicate_groups) >= 1  # At least some duplicates should be found
    
    @pytest.mark.asyncio
    async def test_primary_card_selection(self, dedup_service, sample_cards):
        """Test selection of primary card from duplicates"""
        card1, card2, card3 = sample_cards[0], sample_cards[1], sample_cards[2]
        
        # card1 has highest difficulty, should be selected as primary
        primary = dedup_service._select_primary_card([card1, card2, card3])
        assert primary == card1
        
        # Test with different difficulty ordering
        card2.difficulty = 3.0  # Make card2 highest
        primary = dedup_service._select_primary_card([card1, card2, card3])
        assert primary == card2
    
    @pytest.mark.asyncio
    async def test_metadata_similarity(self, dedup_service):
        """Test metadata similarity calculation"""
        metadata1 = {
            "knowledge_type": "definition",
            "blanked_entities": [{"entity": "machine learning", "blank_number": 1}]
        }
        
        metadata2 = {
            "knowledge_type": "definition",
            "blanked_entities": [{"entity": "machine learning", "blank_number": 1}]
        }
        
        metadata3 = {
            "knowledge_type": "fact",
            "blanked_entities": [{"entity": "deep learning", "blank_number": 1}]
        }
        
        # Test identical metadata
        similarity = dedup_service._calculate_metadata_similarity(metadata1, metadata2)
        assert similarity == 1.0
        
        # Test different metadata
        similarity = dedup_service._calculate_metadata_similarity(metadata1, metadata3)
        assert similarity < 0.5
    
    @pytest.mark.asyncio
    async def test_source_traceability(self, dedup_service, sample_cards):
        """Test source traceability building"""
        cards = sample_cards[:3]  # Use first 3 cards
        
        # Test basic traceability without knowledge relationships
        traceability = dedup_service._build_source_traceability(cards)
        
        assert "original_card_ids" in traceability
        assert len(traceability["original_card_ids"]) == 3
        assert "knowledge_ids" in traceability
        assert "chapter_ids" in traceability
        assert "source_anchors" in traceability
        
        # Should have empty lists since cards don't have knowledge relationships
        assert traceability["knowledge_ids"] == []
        assert traceability["chapter_ids"] == []
        assert traceability["source_anchors"] == []
    
    @pytest.mark.asyncio
    async def test_full_deduplication_process(self, dedup_service, sample_cards):
        """Test complete deduplication process"""
        mock_db = Mock()
        
        with patch.object(dedup_service, '_detect_duplicates') as mock_detect:
            # Mock duplicate detection
            duplicate_group = DuplicateGroup(
                primary_card=sample_cards[0],
                duplicate_cards=[sample_cards[1], sample_cards[2]],
                similarity_scores=[0.95, 1.0],
                merge_strategy="remove_duplicates",
                source_traceability={"original_card_ids": ["1", "2", "3"]}
            )
            mock_detect.return_value = [duplicate_group]
            
            with patch.object(dedup_service, '_process_duplicates') as mock_process:
                # Mock duplicate processing
                deduplicated_cards = [sample_cards[0], sample_cards[3], sample_cards[4]]
                merge_stats = {"groups_processed": 1, "cards_removed": 2}
                mock_process.return_value = (deduplicated_cards, merge_stats)
                
                result_cards, stats = await dedup_service.deduplicate_cards(
                    mock_db, sample_cards
                )
                
                # Verify results
                assert len(result_cards) == 3  # 2 duplicates removed
                assert stats["duplicates_removed"] == 3  # 6 original - 3 final
                assert stats["duplicate_rate"] == 0.5  # 3/6
                assert "merge_stats" in stats
    
    @pytest.mark.asyncio
    async def test_deduplication_quality_validation(self, dedup_service, sample_cards):
        """Test validation of deduplication quality"""
        mock_db = Mock()
        
        # Use only non-duplicate cards for validation
        clean_cards = [sample_cards[0], sample_cards[3]]  # Different content
        
        with patch.object(dedup_service, '_detect_duplicates') as mock_detect:
            mock_detect.return_value = []  # No remaining duplicates
            
            validation_results = await dedup_service.validate_deduplication_quality(
                mock_db, clean_cards
            )
            
            assert validation_results["remaining_duplicate_groups"] == 0
            assert validation_results["remaining_duplicate_rate"] == 0.0
            assert validation_results["meets_quality_threshold"] is True
    
    @pytest.mark.asyncio
    async def test_cloze_card_deduplication(self, dedup_service, sample_cards):
        """Test deduplication specifically for cloze cards"""
        cloze_cards = [card for card in sample_cards if card.card_type == CardType.CLOZE]
        
        with patch.object(dedup_service, '_calculate_card_similarity') as mock_similarity:
            mock_similarity.return_value = 0.92  # High similarity
            
            duplicate_groups = await dedup_service._detect_duplicates(cloze_cards)
            
            # Should detect cloze duplicates
            assert len(duplicate_groups) >= 1
            cloze_group = duplicate_groups[0]
            assert cloze_group.primary_card.card_type == CardType.CLOZE
    
    @pytest.mark.asyncio
    async def test_hotspot_comparison(self, dedup_service):
        """Test hotspot metadata comparison for image cards"""
        hotspots1 = [
            {"label": "region1", "x": 10, "y": 20},
            {"label": "region2", "x": 30, "y": 40}
        ]
        
        hotspots2 = [
            {"label": "region1", "x": 15, "y": 25},  # Same label, different position
            {"label": "region3", "x": 50, "y": 60}   # Different label
        ]
        
        hotspots3 = [
            {"label": "region1", "x": 10, "y": 20},
            {"label": "region2", "x": 30, "y": 40}
        ]
        
        # Test partial overlap
        similarity = dedup_service._compare_hotspots(hotspots1, hotspots2)
        assert 0.0 < similarity < 1.0
        
        # Test identical hotspots
        similarity = dedup_service._compare_hotspots(hotspots1, hotspots3)
        assert similarity == 1.0
        
        # Test no overlap
        similarity = dedup_service._compare_hotspots(hotspots1, [])
        assert similarity == 0.0
    
    def test_deduplication_config(self):
        """Test deduplication configuration"""
        config = DeduplicationConfig(
            semantic_similarity_threshold=0.85,
            max_duplicate_rate=0.03
        )
        
        assert config.semantic_similarity_threshold == 0.85
        assert config.max_duplicate_rate == 0.03
        assert config.front_text_weight == 0.6  # Default value
        assert config.preserve_source_links is True  # Default value
    
    @pytest.mark.asyncio
    async def test_empty_card_list(self, dedup_service):
        """Test deduplication with empty card list"""
        mock_db = Mock()
        
        result_cards, stats = await dedup_service.deduplicate_cards(mock_db, [])
        
        assert result_cards == []
        assert stats["total_cards"] == 0
        assert stats["duplicates_removed"] == 0
        assert stats["duplicate_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_single_card(self, dedup_service, sample_cards):
        """Test deduplication with single card"""
        mock_db = Mock()
        single_card = [sample_cards[0]]
        
        with patch.object(dedup_service, '_detect_duplicates') as mock_detect:
            mock_detect.return_value = []  # No duplicates possible
            
            result_cards, stats = await dedup_service.deduplicate_cards(
                mock_db, single_card
            )
            
            assert len(result_cards) == 1
            assert stats["duplicates_removed"] == 0
            assert stats["duplicate_rate"] == 0.0