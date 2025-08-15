"""
Integration test for deduplication service
"""

import asyncio
import logging
from uuid import uuid4
from datetime import datetime

from app.services.deduplication_service import DeduplicationService, DeduplicationConfig
from app.services.card_generation_service import CardGenerationService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.models.learning import Card, CardType
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Document, Chapter
from app.core.database import get_async_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_data():
    """Create test data with intentional duplicates"""
    
    # Create test document and chapter
    document = Document(
        id=uuid4(),
        filename="test_document.pdf",
        file_type="pdf",
        status="completed",
        metadata={}
    )
    
    chapter = Chapter(
        id=uuid4(),
        document_id=document.id,
        title="Machine Learning Basics",
        level=1,
        order_index=1,
        page_start=1,
        page_end=10
    )
    
    # Create knowledge points with similar content
    knowledge_points = [
        Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            entities=["machine learning", "artificial intelligence", "computers"],
            anchors={"page": 1, "chapter": "Machine Learning Basics"}
        ),
        Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a branch of AI that allows computers to learn automatically without explicit programming.",
            entities=["machine learning", "AI", "computers"],
            anchors={"page": 1, "chapter": "Machine Learning Basics"}
        ),
        Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
            entities=["deep learning", "machine learning", "neural networks"],
            anchors={"page": 2, "chapter": "Machine Learning Basics"}
        ),
        Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.FACT,
            text="Neural networks are inspired by the structure and function of biological neural networks.",
            entities=["neural networks", "biological neural networks"],
            anchors={"page": 3, "chapter": "Machine Learning Basics"}
        ),
        Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",  # Exact duplicate
            entities=["machine learning", "artificial intelligence", "computers"],
            anchors={"page": 5, "chapter": "Machine Learning Basics"}
        )
    ]
    
    return document, chapter, knowledge_points


async def generate_test_cards(knowledge_points):
    """Generate cards from knowledge points"""
    
    card_service = CardGenerationService()
    generated_cards = await card_service.generate_cards_from_knowledge(knowledge_points)
    
    # Convert GeneratedCard objects to Card models
    cards = []
    for gen_card in generated_cards:
        card = Card(
            id=uuid4(),
            knowledge_id=gen_card.knowledge_id,
            card_type=gen_card.card_type,
            front=gen_card.front,
            back=gen_card.back,
            difficulty=gen_card.difficulty,
            card_metadata=gen_card.metadata
        )
        cards.append(card)
    
    return cards


async def test_deduplication_integration():
    """Test complete deduplication integration"""
    
    logger.info("Starting deduplication integration test")
    
    try:
        # Create test data
        document, chapter, knowledge_points = await create_test_data()
        logger.info(f"Created {len(knowledge_points)} knowledge points")
        
        # Generate cards
        cards = await generate_test_cards(knowledge_points)
        logger.info(f"Generated {len(cards)} cards")
        
        # Print card details before deduplication
        logger.info("\n=== Cards Before Deduplication ===")
        for i, card in enumerate(cards):
            logger.info(f"Card {i+1}: {card.card_type}")
            logger.info(f"  Front: {card.front[:100]}...")
            logger.info(f"  Back: {card.back[:100]}...")
            logger.info(f"  Difficulty: {card.difficulty}")
            logger.info("")
        
        # Configure deduplication service
        config = DeduplicationConfig(
            semantic_similarity_threshold=0.9,
            max_duplicate_rate=0.05
        )
        dedup_service = DeduplicationService(config)
        
        # Mock database session
        class MockDB:
            def add(self, obj):
                pass
            
            def commit(self):
                pass
        
        mock_db = MockDB()
        
        # Perform deduplication
        logger.info("Performing deduplication...")
        deduplicated_cards, stats = await dedup_service.deduplicate_cards(
            mock_db, cards
        )
        
        # Print results
        logger.info("\n=== Deduplication Results ===")
        logger.info(f"Original cards: {stats['total_cards']}")
        logger.info(f"Final cards: {stats['final_cards']}")
        logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
        logger.info(f"Duplicate rate: {stats['duplicate_rate']:.2%}")
        logger.info(f"Duplicate groups: {stats['duplicate_groups']}")
        logger.info(f"Average similarity: {stats['average_similarity']:.3f}")
        logger.info(f"Meets target: {stats['meets_target']}")
        
        # Print remaining cards
        logger.info("\n=== Cards After Deduplication ===")
        for i, card in enumerate(deduplicated_cards):
            logger.info(f"Card {i+1}: {card.card_type}")
            logger.info(f"  Front: {card.front[:100]}...")
            logger.info(f"  Back: {card.back[:100]}...")
            logger.info(f"  Difficulty: {card.difficulty}")
            if card.card_metadata and "source_traceability" in card.card_metadata:
                traceability = card.card_metadata["source_traceability"]
                logger.info(f"  Source cards: {len(traceability.get('original_card_ids', []))}")
            logger.info("")
        
        # Validate deduplication quality
        logger.info("Validating deduplication quality...")
        validation_results = await dedup_service.validate_deduplication_quality(
            mock_db, deduplicated_cards
        )
        
        logger.info("\n=== Validation Results ===")
        logger.info(f"Remaining duplicate groups: {validation_results['remaining_duplicate_groups']}")
        logger.info(f"Remaining duplicate rate: {validation_results['remaining_duplicate_rate']:.2%}")
        logger.info(f"Meets quality threshold: {validation_results['meets_quality_threshold']}")
        
        # Test assertions
        assert stats['duplicate_rate'] <= config.max_duplicate_rate, \
            f"Duplicate rate {stats['duplicate_rate']:.2%} exceeds target {config.max_duplicate_rate:.2%}"
        
        assert validation_results['meets_quality_threshold'], \
            "Deduplication quality does not meet threshold"
        
        assert len(deduplicated_cards) < len(cards), \
            "No duplicates were removed"
        
        logger.info("\n✅ Deduplication integration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Deduplication integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_similarity_calculation():
    """Test similarity calculation with real embeddings"""
    
    logger.info("Testing similarity calculation...")
    
    try:
        config = DeduplicationConfig()
        dedup_service = DeduplicationService(config)
        
        # Create test cards with known similarity levels
        card1 = Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence.",
            difficulty=2.0,
            card_metadata={"knowledge_type": "definition"}
        )
        
        card2 = Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a branch of artificial intelligence.",
            difficulty=2.1,
            card_metadata={"knowledge_type": "definition"}
        )
        
        card3 = Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is deep learning?",
            back="Deep learning uses neural networks with multiple layers.",
            difficulty=2.5,
            card_metadata={"knowledge_type": "definition"}
        )
        
        # Calculate similarities
        similarity_12 = await dedup_service._calculate_card_similarity(card1, card2)
        similarity_13 = await dedup_service._calculate_card_similarity(card1, card3)
        similarity_23 = await dedup_service._calculate_card_similarity(card2, card3)
        
        logger.info(f"Similarity card1-card2 (similar): {similarity_12:.3f}")
        logger.info(f"Similarity card1-card3 (different): {similarity_13:.3f}")
        logger.info(f"Similarity card2-card3 (different): {similarity_23:.3f}")
        
        # Assertions
        assert similarity_12 > similarity_13, "Similar cards should have higher similarity"
        assert similarity_12 > similarity_23, "Similar cards should have higher similarity"
        assert similarity_12 > 0.8, "Similar cards should have high similarity score"
        assert similarity_13 < 0.7, "Different cards should have lower similarity score"
        
        logger.info("✅ Similarity calculation test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Similarity calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance():
    """Test deduplication performance with larger dataset"""
    
    logger.info("Testing deduplication performance...")
    
    try:
        # Create larger dataset
        cards = []
        for i in range(100):
            # Create some duplicates intentionally
            if i % 10 == 0 and i > 0:
                # Duplicate of card i-10
                base_card = cards[i-10]
                card = Card(
                    id=uuid4(),
                    knowledge_id=uuid4(),
                    card_type=base_card.card_type,
                    front=base_card.front,
                    back=base_card.back + " (duplicate)",  # Slight variation
                    difficulty=base_card.difficulty + 0.1,
                    card_metadata=base_card.card_metadata
                )
            else:
                # Unique card
                card = Card(
                    id=uuid4(),
                    knowledge_id=uuid4(),
                    card_type=CardType.QA,
                    front=f"What is concept {i}?",
                    back=f"Concept {i} is a unique concept in our test dataset.",
                    difficulty=1.0 + (i % 5),
                    card_metadata={"knowledge_type": "definition"}
                )
            cards.append(card)
        
        logger.info(f"Created {len(cards)} cards for performance test")
        
        # Configure deduplication
        config = DeduplicationConfig(
            semantic_similarity_threshold=0.85,  # Lower threshold for performance test
            max_duplicate_rate=0.15  # Allow higher duplicate rate
        )
        dedup_service = DeduplicationService(config)
        
        # Mock database
        class MockDB:
            def add(self, obj):
                pass
            def commit(self):
                pass
        
        mock_db = MockDB()
        
        # Measure performance
        start_time = datetime.now()
        
        deduplicated_cards, stats = await dedup_service.deduplicate_cards(
            mock_db, cards
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Cards per second: {len(cards) / processing_time:.1f}")
        logger.info(f"Duplicates found: {stats['duplicates_removed']}")
        logger.info(f"Final duplicate rate: {stats['duplicate_rate']:.2%}")
        
        # Performance assertions
        assert processing_time < 30, f"Processing took too long: {processing_time:.2f}s"
        assert len(deduplicated_cards) <= len(cards), "Result should not have more cards than input"
        
        logger.info("✅ Performance test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all deduplication tests"""
    
    logger.info("🚀 Starting deduplication integration tests")
    
    tests = [
        ("Integration Test", test_deduplication_integration),
        ("Similarity Calculation", test_similarity_calculation),
        ("Performance Test", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name}")
        logger.info(f"{'='*50}")
        
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All deduplication tests passed!")
        return True
    else:
        logger.error("💥 Some deduplication tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)