"""
Verification script for deduplication implementation
"""

import asyncio
import logging
from uuid import uuid4

from app.services.deduplication_service import DeduplicationService, DeduplicationConfig
from app.models.learning import Card, CardType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_cards():
    """Create test cards with known duplicates"""
    
    cards = []
    
    # Exact duplicates
    card1 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a subset of artificial intelligence.",
        difficulty=2.5,
        card_metadata={"knowledge_type": "definition"}
    )
    
    card2 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a subset of artificial intelligence.",
        difficulty=2.3,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Near duplicates
    card3 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is machine learning?",
        back="Machine learning is a branch of AI that enables computers to learn.",
        difficulty=2.1,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Different content
    card4 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is deep learning?",
        back="Deep learning uses neural networks with multiple layers.",
        difficulty=3.0,
        card_metadata={"knowledge_type": "definition"}
    )
    
    # Cloze duplicates
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


async def test_deduplication_functionality():
    """Test core deduplication functionality"""
    
    logger.info("Testing deduplication functionality...")
    
    # Create test cards
    cards = create_test_cards()
    logger.info(f"Created {len(cards)} test cards")
    
    # Configure deduplication service
    config = DeduplicationConfig(
        semantic_similarity_threshold=0.9,
        max_duplicate_rate=0.05
    )
    dedup_service = DeduplicationService(config)
    
    # Mock database
    class MockDB:
        def add(self, obj):
            pass
        def commit(self):
            pass
    
    mock_db = MockDB()
    
    # Perform deduplication
    deduplicated_cards, stats = await dedup_service.deduplicate_cards(mock_db, cards)
    
    # Verify results
    logger.info(f"Original cards: {stats['total_cards']}")
    logger.info(f"Final cards: {stats['final_cards']}")
    logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
    logger.info(f"Duplicate rate: {stats['duplicate_rate']:.2%}")
    
    # Assertions
    assert stats['total_cards'] == 6, f"Expected 6 total cards, got {stats['total_cards']}"
    assert stats['duplicates_removed'] > 0, "Should have removed some duplicates"
    assert len(deduplicated_cards) < len(cards), "Should have fewer cards after deduplication"
    
    logger.info("✅ Deduplication functionality test passed")
    return True


async def test_similarity_calculation():
    """Test similarity calculation accuracy"""
    
    logger.info("Testing similarity calculation...")
    
    dedup_service = DeduplicationService()
    
    # Test exact match
    card1 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is AI?",
        back="Artificial Intelligence",
        difficulty=2.0,
        card_metadata={}
    )
    
    card2 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is AI?",
        back="Artificial Intelligence",
        difficulty=2.0,
        card_metadata={}
    )
    
    # Test exact match detection
    is_exact = dedup_service._is_exact_match(card1, card2)
    assert is_exact is True, "Should detect exact match"
    
    # Test semantic similarity
    card3 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is AI?",
        back="AI is artificial intelligence",
        difficulty=2.0,
        card_metadata={}
    )
    
    similarity = await dedup_service._calculate_card_similarity(card1, card3)
    logger.info(f"Similarity between similar cards: {similarity:.3f}")
    assert similarity > 0.8, f"Similar cards should have high similarity, got {similarity}"
    
    # Test different cards
    card4 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="What is the weather?",
        back="It's sunny today",
        difficulty=1.0,
        card_metadata={}
    )
    
    similarity = await dedup_service._calculate_card_similarity(card1, card4)
    logger.info(f"Similarity between different cards: {similarity:.3f}")
    assert similarity < 0.5, f"Different cards should have low similarity, got {similarity}"
    
    logger.info("✅ Similarity calculation test passed")
    return True


async def test_configuration():
    """Test deduplication configuration"""
    
    logger.info("Testing configuration...")
    
    # Test default configuration
    default_config = DeduplicationConfig()
    assert default_config.semantic_similarity_threshold == 0.9
    assert default_config.max_duplicate_rate == 0.05
    
    # Test custom configuration
    custom_config = DeduplicationConfig(
        semantic_similarity_threshold=0.85,
        max_duplicate_rate=0.1
    )
    assert custom_config.semantic_similarity_threshold == 0.85
    assert custom_config.max_duplicate_rate == 0.1
    
    # Test service with custom config
    dedup_service = DeduplicationService(custom_config)
    assert dedup_service.config.semantic_similarity_threshold == 0.85
    
    logger.info("✅ Configuration test passed")
    return True


async def test_metadata_similarity():
    """Test metadata similarity calculation"""
    
    logger.info("Testing metadata similarity...")
    
    dedup_service = DeduplicationService()
    
    # Test identical metadata
    metadata1 = {
        "knowledge_type": "definition",
        "blanked_entities": [{"entity": "test", "blank_number": 1}]
    }
    
    metadata2 = {
        "knowledge_type": "definition",
        "blanked_entities": [{"entity": "test", "blank_number": 1}]
    }
    
    similarity = dedup_service._calculate_metadata_similarity(metadata1, metadata2)
    assert similarity == 1.0, f"Identical metadata should have similarity 1.0, got {similarity}"
    
    # Test different metadata
    metadata3 = {
        "knowledge_type": "fact",
        "blanked_entities": [{"entity": "different", "blank_number": 1}]
    }
    
    similarity = dedup_service._calculate_metadata_similarity(metadata1, metadata3)
    assert similarity < 0.5, f"Different metadata should have low similarity, got {similarity}"
    
    logger.info("✅ Metadata similarity test passed")
    return True


async def test_primary_card_selection():
    """Test primary card selection logic"""
    
    logger.info("Testing primary card selection...")
    
    dedup_service = DeduplicationService()
    
    # Create cards with different difficulties
    card1 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="Test question",
        back="Test answer",
        difficulty=2.0,
        card_metadata={}
    )
    
    card2 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="Test question",
        back="Test answer with more detail",
        difficulty=3.0,
        card_metadata={}
    )
    
    card3 = Card(
        id=uuid4(),
        knowledge_id=uuid4(),
        card_type=CardType.QA,
        front="Test question",
        back="Test answer",
        difficulty=1.5,
        card_metadata={}
    )
    
    # Test selection (should prefer higher difficulty and more content)
    primary = dedup_service._select_primary_card([card1, card2, card3])
    assert primary == card2, "Should select card with highest difficulty and most content"
    
    logger.info("✅ Primary card selection test passed")
    return True


async def test_source_traceability():
    """Test source traceability functionality"""
    
    logger.info("Testing source traceability...")
    
    dedup_service = DeduplicationService()
    
    # Create test cards
    cards = create_test_cards()[:3]
    
    # Test traceability building
    traceability = dedup_service._build_source_traceability(cards)
    
    assert "original_card_ids" in traceability
    assert len(traceability["original_card_ids"]) == 3
    assert "knowledge_ids" in traceability
    assert "chapter_ids" in traceability
    assert "source_anchors" in traceability
    
    logger.info("✅ Source traceability test passed")
    return True


async def main():
    """Run all verification tests"""
    
    logger.info("🚀 Starting deduplication implementation verification")
    
    tests = [
        ("Deduplication Functionality", test_deduplication_functionality),
        ("Similarity Calculation", test_similarity_calculation),
        ("Configuration", test_configuration),
        ("Metadata Similarity", test_metadata_similarity),
        ("Primary Card Selection", test_primary_card_selection),
        ("Source Traceability", test_source_traceability)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("VERIFICATION SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All deduplication implementation tests passed!")
        return True
    else:
        logger.error("💥 Some deduplication implementation tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)