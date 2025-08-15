"""
Example usage of the card generation service
"""

import asyncio
from uuid import uuid4
from typing import List

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.card_generation_service import CardGenerationService, CardGenerationConfig
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Figure
from app.models.learning import CardType


async def demonstrate_card_generation():
    """Demonstrate card generation with various knowledge types."""
    
    print("Card Generation Service Demo")
    print("=" * 50)
    
    # Configure the service
    config = CardGenerationConfig(
        max_cloze_blanks=3,
        min_cloze_blanks=1,
        base_difficulty=1.0,
        complexity_weight=0.4,
        entity_density_weight=0.3
    )
    
    service = CardGenerationService(config)
    
    # Create sample knowledge points
    knowledge_points = create_sample_knowledge()
    
    # Create sample figure
    figure = create_sample_figure(knowledge_points[0].chapter_id)
    
    print(f"Created {len(knowledge_points)} knowledge points:")
    for i, kp in enumerate(knowledge_points, 1):
        print(f"  {i}. {kp.kind.value}: {kp.text[:60]}...")
    
    print(f"\nCreated 1 figure: {figure.caption}")
    
    # Generate cards
    print(f"\nGenerating cards...")
    generated_cards = await service.generate_cards_from_knowledge(
        knowledge_points, 
        figures=[figure]
    )
    
    print(f"Generated {len(generated_cards)} cards")
    
    # Display cards by type
    await display_cards_by_type(generated_cards)
    
    # Show generation statistics
    stats = service.get_generation_statistics(generated_cards)
    print(f"\nGeneration Statistics:")
    print(f"  Total cards: {stats['total_cards']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  Average difficulty: {stats['avg_difficulty']}")
    print(f"  Difficulty range: {stats['lowest_difficulty']} - {stats['highest_difficulty']}")
    
    # Demonstrate specific features
    await demonstrate_specific_features(service, knowledge_points[0])
    
    return generated_cards


def create_sample_knowledge() -> List[Knowledge]:
    """Create sample knowledge points for demonstration."""
    
    chapter_id = uuid4()
    
    return [
        # Definition
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.DEFINITION,
            text="Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems.",
            entities=["Artificial Intelligence", "AI", "human intelligence", "machines", "computer systems"],
            anchors={"page": 1, "chapter": "Introduction", "position": 0},
            confidence_score=0.95
        ),
        
        # Fact
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.FACT,
            text="The term 'Artificial Intelligence' was first coined by John McCarthy in 1956 at the Dartmouth Conference.",
            entities=["Artificial Intelligence", "John McCarthy", "1956", "Dartmouth Conference"],
            anchors={"page": 2, "chapter": "History", "position": 0},
            confidence_score=0.9
        ),
        
        # Theorem
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.THEOREM,
            text="Bayes' theorem: The probability of an event A given event B is equal to the probability of B given A times the probability of A, divided by the probability of B.",
            entities=["Bayes' theorem", "probability", "event A", "event B"],
            anchors={"page": 15, "chapter": "Probability", "position": 0},
            confidence_score=0.98
        ),
        
        # Process
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.PROCESS,
            text="Machine learning workflow: 1) Data collection, 2) Data preprocessing, 3) Model selection, 4) Training, 5) Evaluation, 6) Deployment.",
            entities=["machine learning", "workflow", "data collection", "preprocessing", "model selection", "training", "evaluation", "deployment"],
            anchors={"page": 25, "chapter": "ML Process", "position": 0},
            confidence_score=0.85
        ),
        
        # Example
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.EXAMPLE,
            text="For example, Google's PageRank algorithm uses the link structure of the web to determine the importance of web pages.",
            entities=["Google", "PageRank algorithm", "link structure", "web pages", "importance"],
            anchors={"page": 30, "chapter": "Applications", "position": 0},
            confidence_score=0.8
        ),
        
        # Concept
        Knowledge(
            id=uuid4(),
            chapter_id=chapter_id,
            kind=KnowledgeType.CONCEPT,
            text="Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data.",
            entities=["deep learning", "machine learning", "neural networks", "multiple layers", "complex patterns", "data"],
            anchors={"page": 35, "chapter": "Deep Learning", "position": 0},
            confidence_score=0.92
        )
    ]


def create_sample_figure(chapter_id) -> Figure:
    """Create a sample figure for demonstration."""
    
    return Figure(
        id=uuid4(),
        chapter_id=chapter_id,
        image_path="/images/neural_network_architecture.png",
        caption="Architecture of a deep neural network showing input layer, hidden layers, and output layer with connections between neurons",
        page_number=36,
        bbox={"x": 50, "y": 100, "width": 600, "height": 400},
        image_format="png"
    )


async def display_cards_by_type(generated_cards):
    """Display generated cards organized by type."""
    
    # Group cards by type
    cards_by_type = {}
    for card in generated_cards:
        card_type = card.card_type.value
        if card_type not in cards_by_type:
            cards_by_type[card_type] = []
        cards_by_type[card_type].append(card)
    
    # Display each type
    for card_type, cards in cards_by_type.items():
        print(f"\n{card_type.upper()} CARDS ({len(cards)} cards):")
        print("-" * 40)
        
        for i, card in enumerate(cards, 1):
            print(f"\nCard {i}:")
            print(f"  Difficulty: {card.difficulty}")
            print(f"  Front: {card.front}")
            print(f"  Back: {card.back[:100]}{'...' if len(card.back) > 100 else ''}")
            
            # Show type-specific metadata
            if card_type == "cloze" and "blanked_entities" in card.metadata:
                blanked = card.metadata["blanked_entities"]
                entities = [item["entity"] for item in blanked]
                print(f"  Blanked entities: {entities}")
            
            elif card_type == "image_hotspot" and "hotspots" in card.metadata:
                hotspots = card.metadata["hotspots"]
                print(f"  Hotspots: {len(hotspots)} regions")
                for j, hotspot in enumerate(hotspots):
                    print(f"    {j+1}. {hotspot['label']}: {hotspot['description'][:50]}...")


async def demonstrate_specific_features(service: CardGenerationService, sample_knowledge: Knowledge):
    """Demonstrate specific features of the card generation service."""
    
    print(f"\nDemonstrating Specific Features:")
    print("-" * 40)
    
    # 1. Definition parsing
    print(f"\n1. Definition Parsing:")
    definition_text = "Machine learning is a method of data analysis that automates analytical model building."
    parsed = service._parse_definition(definition_text)
    if parsed:
        term, definition = parsed
        print(f"   Term: '{term}'")
        print(f"   Definition: '{definition}'")
    else:
        print(f"   Could not parse definition from: {definition_text}")
    
    # 2. Key term extraction
    print(f"\n2. Key Term Extraction:")
    key_terms = service._extract_key_terms(sample_knowledge)
    print(f"   Extracted terms: {key_terms}")
    
    # 3. Entity selection for cloze
    print(f"\n3. Entity Selection for Cloze:")
    if sample_knowledge.entities:
        selected_entities = service._select_entities_for_cloze(
            sample_knowledge.entities, 
            sample_knowledge.text
        )
        print(f"   Available entities: {sample_knowledge.entities}")
        print(f"   Selected for cloze: {selected_entities}")
        
        # 4. Cloze text creation
        if selected_entities:
            print(f"\n4. Cloze Text Creation:")
            cloze_text, blanked_entities = service._create_cloze_text(
                sample_knowledge.text, 
                selected_entities
            )
            print(f"   Original: {sample_knowledge.text}")
            print(f"   Cloze: {cloze_text}")
            print(f"   Blanked: {[item['entity'] for item in blanked_entities]}")
    
    # 5. Difficulty calculation
    print(f"\n5. Difficulty Calculation:")
    test_texts = [
        ("Simple text", "AI is smart."),
        ("Medium text", "Artificial intelligence involves machine learning algorithms."),
        ("Complex text", "The implementation of sophisticated neural network architectures requires comprehensive understanding of backpropagation algorithms and gradient descent optimization techniques.")
    ]
    
    for label, text in test_texts:
        difficulty = service._calculate_card_difficulty(
            sample_knowledge, text, CardType.QA
        )
        print(f"   {label}: {difficulty}")
    
    # 6. Text similarity
    print(f"\n6. Text Similarity:")
    text1 = "machine learning artificial intelligence"
    text2 = "AI and ML algorithms"
    similarity = service._calculate_text_similarity(text1, text2)
    print(f"   '{text1}' vs '{text2}': {similarity:.3f}")


async def demonstrate_configuration_options():
    """Demonstrate different configuration options."""
    
    print(f"\nConfiguration Options Demo:")
    print("-" * 40)
    
    # Create sample knowledge
    knowledge = Knowledge(
        id=uuid4(),
        chapter_id=uuid4(),
        kind=KnowledgeType.DEFINITION,
        text="Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language.",
        entities=["Natural Language Processing", "NLP", "artificial intelligence", "computers", "human language"],
        anchors={"page": 1},
        confidence_score=0.9
    )
    
    # Test different configurations
    configs = [
        ("Conservative", CardGenerationConfig(max_cloze_blanks=2, base_difficulty=0.8)),
        ("Aggressive", CardGenerationConfig(max_cloze_blanks=4, base_difficulty=1.5)),
        ("Balanced", CardGenerationConfig(max_cloze_blanks=3, base_difficulty=1.0))
    ]
    
    for config_name, config in configs:
        print(f"\n{config_name} Configuration:")
        service = CardGenerationService(config)
        
        cards = await service.generate_cards_from_knowledge([knowledge])
        
        print(f"  Generated {len(cards)} cards")
        for card in cards:
            print(f"    {card.card_type.value}: difficulty {card.difficulty}")
            if card.card_type == CardType.CLOZE and "blanked_entities" in card.metadata:
                blank_count = len(card.metadata["blanked_entities"])
                print(f"      Blanks: {blank_count}")


async def main():
    """Run the card generation demonstration."""
    
    try:
        # Main demonstration
        cards = await demonstrate_card_generation()
        
        # Configuration options
        await demonstrate_configuration_options()
        
        print(f"\n" + "=" * 50)
        print(f"Demo completed successfully!")
        print(f"Generated {len(cards)} total cards")
        print("=" * 50)
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())