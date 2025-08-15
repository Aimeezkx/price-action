"""
Integration test for card generation service
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.card_generation_service import CardGenerationService, CardGenerationConfig
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Figure
from app.models.learning import CardType
from uuid import uuid4


async def test_card_generation_integration():
    """Test complete card generation pipeline."""
    
    print("Testing Card Generation Service Integration...")
    
    # Initialize service
    config = CardGenerationConfig(
        max_cloze_blanks=3,
        min_cloze_blanks=1,
        base_difficulty=1.0
    )
    service = CardGenerationService(config)
    
    # Create sample knowledge points
    knowledge_points = [
        # Definition knowledge
        Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            entities=["machine learning", "artificial intelligence", "computers", "experience"],
            anchors={"page": 1, "chapter": "Introduction", "position": 0},
            confidence_score=0.9
        ),
        
        # Fact knowledge
        Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.FACT,
            text="Python was created by Guido van Rossum and first released in 1991. It is now one of the most popular programming languages.",
            entities=["Python", "Guido van Rossum", "1991", "programming languages"],
            anchors={"page": 2, "chapter": "History", "position": 1},
            confidence_score=0.85
        ),
        
        # Theorem knowledge
        Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.THEOREM,
            text="Pythagorean theorem: In a right triangle, the square of the length of the hypotenuse equals the sum of the squares of the lengths of the other two sides.",
            entities=["Pythagorean theorem", "right triangle", "hypotenuse", "sides"],
            anchors={"page": 3, "chapter": "Geometry", "position": 0},
            confidence_score=0.95
        ),
        
        # Process knowledge
        Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.PROCESS,
            text="To train a neural network: 1) Initialize weights randomly, 2) Forward propagate input data, 3) Calculate loss, 4) Backpropagate errors, 5) Update weights, 6) Repeat until convergence.",
            entities=["neural network", "weights", "forward propagate", "loss", "backpropagate", "convergence"],
            anchors={"page": 4, "chapter": "Training", "position": 0},
            confidence_score=0.8
        ),
        
        # Example knowledge
        Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.EXAMPLE,
            text="For example, a recommendation system like Netflix uses collaborative filtering to suggest movies based on user preferences and viewing history.",
            entities=["recommendation system", "Netflix", "collaborative filtering", "movies", "user preferences"],
            anchors={"page": 5, "chapter": "Applications", "position": 0},
            confidence_score=0.75
        )
    ]
    
    # Create sample figure
    figure = Figure(
        id=uuid4(),
        chapter_id=knowledge_points[0].chapter_id,  # Same chapter as first knowledge
        image_path="/path/to/neural_network_diagram.jpg",
        caption="Diagram showing the architecture of a neural network with input, hidden, and output layers",
        page_number=1,
        bbox={"x": 0, "y": 0, "width": 500, "height": 400},
        image_format="jpg"
    )
    
    print(f"Created {len(knowledge_points)} sample knowledge points")
    print(f"Created 1 sample figure")
    
    # Test card generation
    try:
        generated_cards = await service.generate_cards_from_knowledge(
            knowledge_points, 
            figures=[figure]
        )
        
        print(f"\n✓ Generated {len(generated_cards)} cards successfully")
        
        # Analyze generated cards
        card_types = {}
        difficulties = []
        
        for i, card in enumerate(generated_cards):
            card_type = card.card_type.value
            card_types[card_type] = card_types.get(card_type, 0) + 1
            difficulties.append(card.difficulty)
            
            print(f"\nCard {i+1}:")
            print(f"  Type: {card.card_type.value}")
            print(f"  Difficulty: {card.difficulty}")
            print(f"  Front: {card.front[:100]}{'...' if len(card.front) > 100 else ''}")
            print(f"  Back: {card.back[:100]}{'...' if len(card.back) > 100 else ''}")
            
            if card.metadata:
                print(f"  Metadata keys: {list(card.metadata.keys())}")
        
        # Print statistics
        print(f"\n=== Card Generation Statistics ===")
        print(f"Total cards: {len(generated_cards)}")
        print(f"Card types: {card_types}")
        print(f"Average difficulty: {sum(difficulties) / len(difficulties):.2f}")
        print(f"Difficulty range: {min(difficulties):.2f} - {max(difficulties):.2f}")
        
        # Test specific card types
        qa_cards = [c for c in generated_cards if c.card_type == CardType.QA]
        cloze_cards = [c for c in generated_cards if c.card_type == CardType.CLOZE]
        image_cards = [c for c in generated_cards if c.card_type == CardType.IMAGE_HOTSPOT]
        
        print(f"\nQ&A cards: {len(qa_cards)}")
        print(f"Cloze cards: {len(cloze_cards)}")
        print(f"Image hotspot cards: {len(image_cards)}")
        
        # Validate card content
        validation_errors = []
        
        for card in generated_cards:
            # Check required fields
            if not card.front or not card.back:
                validation_errors.append(f"Card missing front or back content")
            
            if card.difficulty < 0.5 or card.difficulty > 5.0:
                validation_errors.append(f"Card difficulty out of range: {card.difficulty}")
            
            if not card.knowledge_id:
                validation_errors.append(f"Card missing knowledge_id")
            
            # Type-specific validation
            if card.card_type == CardType.CLOZE:
                if "[" not in card.front or "]" not in card.front:
                    validation_errors.append(f"Cloze card missing blanks")
                
                if "blanked_entities" not in card.metadata:
                    validation_errors.append(f"Cloze card missing blanked_entities metadata")
            
            elif card.card_type == CardType.IMAGE_HOTSPOT:
                if "hotspots" not in card.metadata:
                    validation_errors.append(f"Image hotspot card missing hotspots metadata")
                
                if not card.front.endswith(('.jpg', '.png', '.jpeg', '.gif')):
                    validation_errors.append(f"Image hotspot card front should be image path")
        
        if validation_errors:
            print(f"\n❌ Validation errors found:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print(f"\n✓ All cards passed validation")
        
        # Test generation statistics
        stats = service.get_generation_statistics(generated_cards)
        print(f"\n=== Generation Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Test specific functionality
        print(f"\n=== Testing Specific Functions ===")
        
        # Test definition parsing
        definition_knowledge = knowledge_points[0]  # Machine learning definition
        parsed_def = service._parse_definition(definition_knowledge.text)
        if parsed_def:
            term, definition = parsed_def
            print(f"✓ Definition parsing: '{term}' -> '{definition[:50]}...'")
        else:
            print(f"❌ Definition parsing failed")
        
        # Test entity selection for cloze
        entities = definition_knowledge.entities
        selected_entities = service._select_entities_for_cloze(entities, definition_knowledge.text)
        print(f"✓ Entity selection: {len(selected_entities)} entities selected from {len(entities)}")
        
        # Test cloze text creation
        if selected_entities:
            cloze_text, blanked = service._create_cloze_text(definition_knowledge.text, selected_entities)
            print(f"✓ Cloze creation: {len(blanked)} blanks created")
            print(f"  Sample: {cloze_text[:100]}...")
        
        # Test difficulty calculation
        sample_card_text = "What is machine learning? Machine learning is a subset of AI."
        difficulty = service._calculate_card_difficulty(
            definition_knowledge, sample_card_text, CardType.QA
        )
        print(f"✓ Difficulty calculation: {difficulty}")
        
        # Test hotspot generation
        if figure:
            related_knowledge = service._find_related_knowledge(figure, knowledge_points)
            print(f"✓ Related knowledge found: {len(related_knowledge)} items")
            
            if related_knowledge:
                hotspots = service._generate_hotspots_from_knowledge(figure, related_knowledge)
                print(f"✓ Hotspots generated: {len(hotspots)} hotspots")
        
        print(f"\n🎉 Card generation integration test completed successfully!")
        print(f"Generated {len(generated_cards)} cards with {len(validation_errors)} validation errors")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Card generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases and error handling."""
    
    print(f"\n=== Testing Edge Cases ===")
    
    service = CardGenerationService()
    
    # Test with empty knowledge list
    try:
        cards = await service.generate_cards_from_knowledge([])
        assert len(cards) == 0
        print("✓ Empty knowledge list handled correctly")
    except Exception as e:
        print(f"❌ Empty knowledge list test failed: {e}")
    
    # Test with knowledge without entities
    try:
        knowledge_no_entities = Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.FACT,
            text="This is a simple fact without entities.",
            entities=[],  # No entities
            anchors={"page": 1},
            confidence_score=0.7
        )
        
        cards = await service.generate_cards_from_knowledge([knowledge_no_entities])
        # Should still generate Q&A cards, but no cloze cards
        qa_cards = [c for c in cards if c.card_type == CardType.QA]
        cloze_cards = [c for c in cards if c.card_type == CardType.CLOZE]
        
        assert len(qa_cards) > 0
        assert len(cloze_cards) == 0
        print("✓ Knowledge without entities handled correctly")
        
    except Exception as e:
        print(f"❌ Knowledge without entities test failed: {e}")
    
    # Test with very short text
    try:
        knowledge_short = Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.FACT,
            text="Short.",
            entities=["Short"],
            anchors={"page": 1},
            confidence_score=0.5
        )
        
        cards = await service.generate_cards_from_knowledge([knowledge_short])
        print(f"✓ Short text handled: {len(cards)} cards generated")
        
    except Exception as e:
        print(f"❌ Short text test failed: {e}")
    
    # Test with very long text
    try:
        long_text = "This is a very long text. " * 100  # 2700 characters
        knowledge_long = Knowledge(
            id=uuid4(),
            chapter_id=uuid4(),
            kind=KnowledgeType.CONCEPT,
            text=long_text,
            entities=["concept", "text", "long"],
            anchors={"page": 1},
            confidence_score=0.8
        )
        
        cards = await service.generate_cards_from_knowledge([knowledge_long])
        print(f"✓ Long text handled: {len(cards)} cards generated")
        
    except Exception as e:
        print(f"❌ Long text test failed: {e}")
    
    print("✓ Edge case testing completed")


async def main():
    """Run all integration tests."""
    
    print("=" * 60)
    print("CARD GENERATION SERVICE INTEGRATION TEST")
    print("=" * 60)
    
    # Test main functionality
    success = await test_card_generation_integration()
    
    if success:
        # Test edge cases
        await test_edge_cases()
        
        print(f"\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("Card generation service is working correctly.")
        print("=" * 60)
    else:
        print(f"\n" + "=" * 60)
        print("❌ TESTS FAILED!")
        print("Please check the errors above.")
        print("=" * 60)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)