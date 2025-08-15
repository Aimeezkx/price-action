"""
Example usage of the knowledge extraction service.
"""

import asyncio
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.knowledge_extraction_service import (
    KnowledgeExtractionService,
    KnowledgeExtractionConfig
)
from app.services.text_segmentation_service import TextSegment
from app.models.knowledge import KnowledgeType


async def demonstrate_knowledge_extraction():
    """Demonstrate knowledge extraction capabilities."""
    
    print("Knowledge Extraction Service Demo")
    print("=" * 50)
    
    # Configure the service
    config = KnowledgeExtractionConfig(
        use_llm=False,  # Use rule-based extraction for demo
        enable_fallback=True,
        min_confidence=0.5,
        max_knowledge_points_per_segment=3
    )
    
    service = KnowledgeExtractionService(config)
    
    # Sample academic text segments
    sample_segments = [
        # Definition example
        TextSegment(
            text="Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data. It is inspired by the structure and function of the human brain.",
            character_count=200,
            word_count=35,
            sentence_count=2,
            anchors={
                "page": 1,
                "chapter_id": "intro_to_ai",
                "position": {"block_index": 0}
            },
            original_blocks=[0]
        ),
        
        # Example with multiple instances
        TextSegment(
            text="For example, convolutional neural networks (CNNs) are used for image recognition tasks. Another example is recurrent neural networks (RNNs), which excel at processing sequential data like text and speech.",
            character_count=190,
            word_count=32,
            sentence_count=2,
            anchors={
                "page": 1,
                "chapter_id": "intro_to_ai",
                "position": {"block_index": 1}
            },
            original_blocks=[1]
        ),
        
        # Process description
        TextSegment(
            text="The training process involves several key steps: Step 1: Initialize the network weights randomly. Step 2: Forward propagate the input through the network. Step 3: Calculate the loss using a loss function. Step 4: Backpropagate the error to update weights. Step 5: Repeat until convergence.",
            character_count=320,
            word_count=52,
            sentence_count=6,
            anchors={
                "page": 2,
                "chapter_id": "intro_to_ai",
                "position": {"block_index": 2}
            },
            original_blocks=[2]
        ),
        
        # Fact with research citation
        TextSegment(
            text="Research shows that transformer architectures have revolutionized natural language processing. Studies indicate that models like GPT and BERT achieve state-of-the-art performance on various NLP benchmarks.",
            character_count=200,
            word_count=30,
            sentence_count=2,
            anchors={
                "page": 3,
                "chapter_id": "intro_to_ai",
                "position": {"block_index": 3}
            },
            original_blocks=[3]
        ),
        
        # Mathematical theorem
        TextSegment(
            text="Universal Approximation Theorem: A feedforward network with a single hidden layer containing a finite number of neurons can approximate any continuous function on a compact subset of Rn to any desired degree of accuracy.",
            character_count=220,
            word_count=35,
            sentence_count=1,
            anchors={
                "page": 4,
                "chapter_id": "intro_to_ai",
                "position": {"block_index": 4}
            },
            original_blocks=[4]
        )
    ]
    
    print(f"Processing {len(sample_segments)} text segments...")
    print()
    
    # Extract knowledge points
    knowledge_points = await service.extract_knowledge_from_segments(
        sample_segments, "intro_to_ai"
    )
    
    print(f"Extracted {len(knowledge_points)} knowledge points:")
    print()
    
    # Display results by type
    knowledge_by_type = {}
    for kp in knowledge_points:
        if kp.kind not in knowledge_by_type:
            knowledge_by_type[kp.kind] = []
        knowledge_by_type[kp.kind].append(kp)
    
    for knowledge_type, points in knowledge_by_type.items():
        print(f"{knowledge_type.value.upper()} ({len(points)} found):")
        print("-" * 40)
        
        for i, kp in enumerate(points, 1):
            print(f"{i}. Text: {kp.text}")
            print(f"   Entities: {', '.join(kp.entities) if kp.entities else 'None'}")
            print(f"   Confidence: {kp.confidence:.3f}")
            print(f"   Page: {kp.anchors.get('page', 'Unknown')}")
            print()
    
    # Show extraction statistics
    stats = service.get_extraction_statistics(knowledge_points)
    print("EXTRACTION STATISTICS:")
    print("-" * 40)
    print(f"Total knowledge points: {stats['total_knowledge_points']}")
    print(f"Average confidence: {stats['avg_confidence']}")
    print(f"Knowledge types found: {list(stats['by_type'].keys())}")
    print(f"Extraction methods: {list(stats['extraction_methods'].keys())}")
    print()
    
    return knowledge_points


async def demonstrate_custom_patterns():
    """Demonstrate custom pattern configuration."""
    
    print("Custom Pattern Configuration Demo")
    print("=" * 50)
    
    # Configure with custom patterns for domain-specific content
    custom_config = KnowledgeExtractionConfig(
        use_llm=False,
        enable_fallback=True,
        min_confidence=0.4,
        definition_patterns=[
            r'(.+?)\s+(?:is defined as|can be defined as|is)\s+(.+?)(?:\.|$)',
            r'(?:Definition|Def)[:：]?\s*(.+?)(?:\.|$)',
        ],
        fact_patterns=[
            r'(?:It is known that|It has been proven that|Evidence shows)\s+(.+?)(?:\.|$)',
            r'(?:Empirical studies|Experiments)\s+(?:show|demonstrate|reveal)\s+(?:that\s+)?(.+?)(?:\.|$)',
        ]
    )
    
    service = KnowledgeExtractionService(custom_config)
    
    # Domain-specific text (medical/scientific)
    medical_segment = TextSegment(
        text="Hypertension is defined as a systolic blood pressure of 140 mmHg or higher, or a diastolic blood pressure of 90 mmHg or higher. It is known that untreated hypertension significantly increases the risk of cardiovascular disease.",
        character_count=220,
        word_count=38,
        sentence_count=2,
        anchors={
            "page": 1,
            "chapter_id": "medical_conditions",
            "position": {"block_index": 0}
        },
        original_blocks=[0]
    )
    
    knowledge_points = await service.extract_knowledge_from_segments(
        [medical_segment], "medical_conditions"
    )
    
    print(f"Extracted {len(knowledge_points)} knowledge points from medical text:")
    print()
    
    for kp in knowledge_points:
        print(f"Type: {kp.kind.value}")
        print(f"Text: {kp.text}")
        print(f"Confidence: {kp.confidence:.3f}")
        print()


async def demonstrate_entity_linking():
    """Demonstrate entity linking within knowledge points."""
    
    print("Entity Linking Demo")
    print("=" * 50)
    
    service = KnowledgeExtractionService()
    
    # Text with clear entities
    entity_rich_segment = TextSegment(
        text="Machine learning algorithms like support vector machines (SVM) and random forests are supervised learning methods. These algorithms require labeled training data to learn patterns and make predictions on new, unseen data.",
        character_count=220,
        word_count=35,
        sentence_count=2,
        anchors={
            "page": 1,
            "chapter_id": "ml_algorithms",
            "position": {"block_index": 0}
        },
        original_blocks=[0]
    )
    
    knowledge_points = await service.extract_knowledge_from_segments(
        [entity_rich_segment], "ml_algorithms"
    )
    
    print("Knowledge points with linked entities:")
    print()
    
    for kp in knowledge_points:
        print(f"Knowledge: {kp.text}")
        print(f"Type: {kp.kind.value}")
        print(f"Linked entities: {', '.join(kp.entities) if kp.entities else 'None'}")
        print(f"Confidence: {kp.confidence:.3f}")
        print()


async def demonstrate_confidence_filtering():
    """Demonstrate confidence-based filtering."""
    
    print("Confidence Filtering Demo")
    print("=" * 50)
    
    # Test with different confidence thresholds
    thresholds = [0.3, 0.5, 0.7, 0.9]
    
    test_segment = TextSegment(
        text="Artificial intelligence is the simulation of human intelligence in machines. For example, chatbots use AI to understand and respond to user queries. The process involves natural language processing and machine learning.",
        character_count=200,
        word_count=32,
        sentence_count=3,
        anchors={
            "page": 1,
            "chapter_id": "ai_overview",
            "position": {"block_index": 0}
        },
        original_blocks=[0]
    )
    
    for threshold in thresholds:
        config = KnowledgeExtractionConfig(
            use_llm=False,
            min_confidence=threshold
        )
        service = KnowledgeExtractionService(config)
        
        knowledge_points = await service.extract_knowledge_from_segments(
            [test_segment], "ai_overview"
        )
        
        print(f"Confidence threshold {threshold}: {len(knowledge_points)} knowledge points")
        for kp in knowledge_points:
            print(f"  - {kp.kind.value}: {kp.confidence:.3f}")
        print()


async def main():
    """Run all demonstration examples."""
    
    print("KNOWLEDGE EXTRACTION SERVICE EXAMPLES")
    print("=" * 60)
    print()
    
    try:
        # Basic extraction demo
        await demonstrate_knowledge_extraction()
        print()
        
        # Custom patterns demo
        await demonstrate_custom_patterns()
        print()
        
        # Entity linking demo
        await demonstrate_entity_linking()
        print()
        
        # Confidence filtering demo
        await demonstrate_confidence_filtering()
        
        print("=" * 60)
        print("All demonstrations completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())