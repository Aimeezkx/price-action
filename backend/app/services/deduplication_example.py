"""
Example usage of the deduplication service
"""

import asyncio
import logging
from uuid import uuid4
from datetime import datetime

from app.services.deduplication_service import DeduplicationService, DeduplicationConfig
from app.models.learning import Card, CardType
from app.models.knowledge import Knowledge, KnowledgeType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_cards():
    """Create sample cards with intentional duplicates for demonstration"""
    
    cards = []
    
    # Group 1: Machine Learning Definition (3 similar cards)
    cards.extend([
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            difficulty=2.5,
            card_metadata={"knowledge_type": "definition", "topic": "machine learning"}
        ),
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a branch of AI that allows computers to learn automatically without explicit programming.",
            difficulty=2.3,
            card_metadata={"knowledge_type": "definition", "topic": "machine learning"}
        ),
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="Define machine learning.",
            back="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            difficulty=2.1,
            card_metadata={"knowledge_type": "definition", "topic": "machine learning"}
        )
    ])
    
    # Group 2: Neural Networks (2 similar cloze cards)
    cards.extend([
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.CLOZE,
            front="[1] are computational models inspired by biological neural networks.",
            back="Neural networks are computational models inspired by biological neural networks.",
            difficulty=2.8,
            card_metadata={
                "knowledge_type": "definition",
                "blanked_entities": [{"entity": "Neural networks", "blank_number": 1}]
            }
        ),
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.CLOZE,
            front="[1] are computing systems inspired by biological neural networks.",
            back="Neural networks are computing systems inspired by biological neural networks.",
            difficulty=2.6,
            card_metadata={
                "knowledge_type": "definition",
                "blanked_entities": [{"entity": "Neural networks", "blank_number": 1}]
            }
        )
    ])
    
    # Group 3: Deep Learning (unique cards - should not be deduplicated)
    cards.extend([
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is deep learning?",
            back="Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
            difficulty=3.2,
            card_metadata={"knowledge_type": "definition", "topic": "deep learning"}
        ),
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What are the advantages of deep learning?",
            back="Deep learning can automatically learn features from data and handle complex patterns.",
            difficulty=3.5,
            card_metadata={"knowledge_type": "fact", "topic": "deep learning"}
        )
    ])
    
    # Group 4: Image hotspot card (unique)
    cards.append(
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.IMAGE_HOTSPOT,
            front="/path/to/neural_network_diagram.png",
            back="Neural network architecture diagram showing input, hidden, and output layers.",
            difficulty=2.9,
            card_metadata={
                "question": "Click on the different layers of the neural network.",
                "hotspots": [
                    {"label": "Input Layer", "x": 50, "y": 100, "width": 80, "height": 60},
                    {"label": "Hidden Layer", "x": 200, "y": 100, "width": 80, "height": 60},
                    {"label": "Output Layer", "x": 350, "y": 100, "width": 80, "height": 60}
                ]
            }
        )
    )
    
    # Group 5: Exact duplicate (should be removed)
    cards.append(
        Card(
            id=uuid4(),
            knowledge_id=uuid4(),
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            difficulty=2.0,  # Lower difficulty than original
            card_metadata={"knowledge_type": "definition", "topic": "machine learning"}
        )
    )
    
    return cards


async def demonstrate_deduplication():
    """Demonstrate the deduplication process"""
    
    logger.info("🚀 Deduplication Service Demonstration")
    logger.info("=" * 50)
    
    # Create sample cards
    cards = create_sample_cards()
    logger.info(f"Created {len(cards)} sample cards with intentional duplicates")
    
    # Display original cards
    logger.info("\n📋 Original Cards:")
    logger.info("-" * 30)
    for i, card in enumerate(cards, 1):
        logger.info(f"{i}. [{card.card_type.value.upper()}] {card.front[:60]}...")
        logger.info(f"   Back: {card.back[:60]}...")
        logger.info(f"   Difficulty: {card.difficulty}")
        logger.info("")
    
    # Configure deduplication service
    config = DeduplicationConfig(
        semantic_similarity_threshold=0.9,
        exact_match_threshold=0.99,
        max_duplicate_rate=0.05,
        front_text_weight=0.6,
        back_text_weight=0.4,
        metadata_weight=0.1
    )
    
    dedup_service = DeduplicationService(config)
    logger.info(f"Configured deduplication with {config.semantic_similarity_threshold} similarity threshold")
    
    # Mock database session
    class MockDB:
        def __init__(self):
            self.added_objects = []
        
        def add(self, obj):
            self.added_objects.append(obj)
        
        def commit(self):
            logger.info(f"Mock DB: Committed {len(self.added_objects)} objects")
    
    mock_db = MockDB()
    
    # Perform deduplication
    logger.info("\n🔍 Performing Deduplication...")
    logger.info("-" * 30)
    
    start_time = datetime.now()
    deduplicated_cards, stats = await dedup_service.deduplicate_cards(mock_db, cards)
    end_time = datetime.now()
    
    processing_time = (end_time - start_time).total_seconds()
    
    # Display results
    logger.info("\n📊 Deduplication Results:")
    logger.info("-" * 30)
    logger.info(f"Original cards: {stats['total_cards']}")
    logger.info(f"Final cards: {stats['final_cards']}")
    logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
    logger.info(f"Duplicate rate: {stats['duplicate_rate']:.2%}")
    logger.info(f"Duplicate groups found: {stats['duplicate_groups']}")
    logger.info(f"Average similarity: {stats['average_similarity']:.3f}")
    logger.info(f"Meets target (<{config.max_duplicate_rate:.1%}): {stats['meets_target']}")
    logger.info(f"Processing time: {processing_time:.3f} seconds")
    
    # Display final cards
    logger.info("\n✅ Final Deduplicated Cards:")
    logger.info("-" * 30)
    for i, card in enumerate(deduplicated_cards, 1):
        logger.info(f"{i}. [{card.card_type.value.upper()}] {card.front[:60]}...")
        logger.info(f"   Back: {card.back[:60]}...")
        logger.info(f"   Difficulty: {card.difficulty}")
        
        # Show source traceability if available
        if card.card_metadata and "source_traceability" in card.card_metadata:
            traceability = card.card_metadata["source_traceability"]
            original_count = len(traceability.get("original_card_ids", []))
            if original_count > 1:
                logger.info(f"   📎 Merged from {original_count} original cards")
        
        logger.info("")
    
    # Validate deduplication quality
    logger.info("🔬 Validating Deduplication Quality...")
    logger.info("-" * 30)
    
    validation_results = await dedup_service.validate_deduplication_quality(
        mock_db, deduplicated_cards
    )
    
    logger.info(f"Remaining duplicate groups: {validation_results['remaining_duplicate_groups']}")
    logger.info(f"Remaining duplicate rate: {validation_results['remaining_duplicate_rate']:.2%}")
    logger.info(f"Quality threshold met: {validation_results['meets_quality_threshold']}")
    
    # Summary
    logger.info("\n🎯 Summary:")
    logger.info("-" * 30)
    if stats['meets_target'] and validation_results['meets_quality_threshold']:
        logger.info("✅ Deduplication successful!")
        logger.info(f"   • Reduced {len(cards)} cards to {len(deduplicated_cards)} cards")
        logger.info(f"   • Removed {stats['duplicates_removed']} duplicates ({stats['duplicate_rate']:.1%})")
        logger.info(f"   • Final duplicate rate: {validation_results['remaining_duplicate_rate']:.2%}")
        logger.info(f"   • Processing time: {processing_time:.3f}s")
    else:
        logger.warning("⚠️ Deduplication did not meet all targets")
        if not stats['meets_target']:
            logger.warning(f"   • Duplicate rate {stats['duplicate_rate']:.2%} exceeds target {config.max_duplicate_rate:.2%}")
        if not validation_results['meets_quality_threshold']:
            logger.warning(f"   • Quality validation failed")
    
    return deduplicated_cards, stats


async def demonstrate_similarity_calculation():
    """Demonstrate similarity calculation between cards"""
    
    logger.info("\n🔍 Similarity Calculation Demonstration")
    logger.info("=" * 50)
    
    # Create test card pairs
    test_pairs = [
        # High similarity pair
        (
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.QA,
                front="What is artificial intelligence?",
                back="Artificial intelligence is the simulation of human intelligence in machines.",
                difficulty=2.5,
                card_metadata={"knowledge_type": "definition"}
            ),
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.QA,
                front="What is artificial intelligence?",
                back="AI is the simulation of human intelligence processes by machines.",
                difficulty=2.3,
                card_metadata={"knowledge_type": "definition"}
            )
        ),
        # Medium similarity pair
        (
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.QA,
                front="What is machine learning?",
                back="Machine learning is a subset of AI that enables computers to learn.",
                difficulty=2.0,
                card_metadata={"knowledge_type": "definition"}
            ),
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.QA,
                front="What is deep learning?",
                back="Deep learning is a subset of machine learning using neural networks.",
                difficulty=3.0,
                card_metadata={"knowledge_type": "definition"}
            )
        ),
        # Low similarity pair
        (
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.QA,
                front="What is supervised learning?",
                back="Supervised learning uses labeled data to train models.",
                difficulty=2.8,
                card_metadata={"knowledge_type": "definition"}
            ),
            Card(
                id=uuid4(),
                knowledge_id=uuid4(),
                card_type=CardType.CLOZE,
                front="The capital of [1] is Paris.",
                back="The capital of France is Paris.",
                difficulty=1.5,
                card_metadata={"knowledge_type": "fact", "blanked_entities": [{"entity": "France", "blank_number": 1}]}
            )
        )
    ]
    
    dedup_service = DeduplicationService()
    
    for i, (card1, card2) in enumerate(test_pairs, 1):
        logger.info(f"\nPair {i}:")
        logger.info(f"Card A: [{card1.card_type.value}] {card1.front}")
        logger.info(f"Card B: [{card2.card_type.value}] {card2.front}")
        
        similarity = await dedup_service._calculate_card_similarity(card1, card2)
        logger.info(f"Similarity: {similarity:.3f}")
        
        if similarity >= 0.9:
            logger.info("🔴 HIGH similarity - Would be considered duplicate")
        elif similarity >= 0.7:
            logger.info("🟡 MEDIUM similarity - Might be related")
        else:
            logger.info("🟢 LOW similarity - Different content")


async def main():
    """Run the deduplication demonstration"""
    
    try:
        # Main deduplication demo
        await demonstrate_deduplication()
        
        # Similarity calculation demo
        await demonstrate_similarity_calculation()
        
        logger.info("\n🎉 Deduplication demonstration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())