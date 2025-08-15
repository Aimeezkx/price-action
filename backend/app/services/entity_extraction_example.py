"""
Example usage of the entity extraction service.
"""

import asyncio
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.entity_extraction_service import (
    EntityExtractionService,
    EntityExtractionConfig,
    Entity,
    EntityType,
    Language
)
from app.services.text_segmentation_service import TextSegmentationService, TextSegment


async def basic_entity_extraction_example():
    """Basic example of entity extraction."""
    print("=== Basic Entity Extraction Example ===")
    
    # Initialize the service
    service = EntityExtractionService()
    
    # Sample text
    text = """
    Machine learning is a method of data analysis that automates analytical model building.
    Companies like Google and Microsoft are investing heavily in AI research.
    The GPT-3 model achieved remarkable results with natural language processing.
    """
    
    # Extract entities
    entities = await service.extract_entities(text)
    
    print(f"Extracted {len(entities)} entities:")
    for entity in entities:
        print(f"  - '{entity.text}' ({entity.entity_type}) [confidence: {entity.confidence:.2f}]")
    
    return entities


async def multilingual_extraction_example():
    """Example of multilingual entity extraction."""
    print("\n=== Multilingual Entity Extraction Example ===")
    
    service = EntityExtractionService()
    
    # English text
    english_text = "Google and Microsoft are leading AI companies in Silicon Valley."
    english_entities = await service.extract_entities(english_text, Language.ENGLISH)
    
    print(f"English entities ({len(english_entities)}):")
    for entity in english_entities:
        print(f"  - '{entity.text}' ({entity.entity_type})")
    
    # Chinese text
    chinese_text = "谷歌和微软是硅谷领先的人工智能公司。"
    chinese_entities = await service.extract_entities(chinese_text, Language.CHINESE)
    
    print(f"\nChinese entities ({len(chinese_entities)}):")
    for entity in chinese_entities:
        print(f"  - '{entity.text}' ({entity.entity_type})")
    
    return english_entities, chinese_entities


async def custom_configuration_example():
    """Example with custom configuration."""
    print("\n=== Custom Configuration Example ===")
    
    # Create custom configuration
    config = EntityExtractionConfig(
        min_entity_length=3,
        min_confidence=0.7,
        enable_deduplication=True,
        similarity_threshold=0.9,
        detect_technical_terms=True,
        custom_stopwords={'example', 'sample', 'test'}
    )
    
    service = EntityExtractionService(config)
    
    text = """
    This is an example of API usage with HTTP protocol and JSON data.
    The ML algorithm processes data using TensorFlow and PyTorch frameworks.
    Sample results show 95% accuracy on the test dataset.
    """
    
    entities = await service.extract_entities(text)
    
    print(f"Extracted {len(entities)} entities with custom config:")
    for entity in entities:
        print(f"  - '{entity.text}' ({entity.entity_type}) [conf: {entity.confidence:.2f}, freq: {entity.frequency}]")
    
    return entities


async def entity_ranking_example():
    """Example of entity ranking and statistics."""
    print("\n=== Entity Ranking and Statistics Example ===")
    
    service = EntityExtractionService()
    
    text = """
    Artificial intelligence and machine learning are transforming industries.
    Deep learning algorithms use neural networks to process data.
    Companies like Google, Microsoft, and OpenAI are leading research.
    The GPT-3 model has 175 billion parameters and shows remarkable capabilities.
    Natural language processing is a key application of AI technology.
    """
    
    entities = await service.extract_entities(text)
    
    # Rank entities by importance
    ranked_entities = service.rank_entities_by_importance(entities, max_entities=10)
    
    print(f"Top 10 most important entities:")
    for i, entity in enumerate(ranked_entities, 1):
        print(f"  {i}. '{entity.text}' ({entity.entity_type}) [score: {entity.importance_score:.3f}]")
    
    # Get statistics
    stats = service.get_entity_statistics(entities)
    
    print(f"\nEntity Statistics:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Unique entities: {stats['unique_entities']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"  Average frequency: {stats['avg_frequency']}")
    print(f"  Most frequent entity: {stats['most_frequent']}")
    print(f"  Highest confidence entity: {stats['highest_confidence']}")
    print(f"  Entity type distribution: {stats['entity_types']}")
    
    return ranked_entities, stats


async def integration_with_text_segmentation_example():
    """Example of integrating entity extraction with text segmentation."""
    print("\n=== Integration with Text Segmentation Example ===")
    
    # Initialize services
    entity_service = EntityExtractionService()
    segmentation_service = TextSegmentationService()
    
    # Sample long text
    long_text = """
    Machine learning is a method of data analysis that automates analytical model building.
    It is a branch of artificial intelligence (AI) based on the idea that systems can learn
    from data, identify patterns and make decisions with minimal human intervention.
    
    The process of machine learning is similar to that of data mining. Both systems search
    through data to look for patterns. However, instead of extracting data for human
    comprehension, machine learning uses that data to detect patterns in data and adjust
    program actions accordingly.
    
    Machine learning algorithms build a mathematical model based on training data in order
    to make predictions or decisions without being explicitly programmed to do so.
    Machine learning algorithms are used in a wide variety of applications, such as email
    filtering and computer vision, where it is difficult or infeasible to develop
    conventional algorithms to perform the needed tasks.
    
    Companies like Google, Microsoft, Amazon, and Facebook are heavily investing in
    machine learning research and development. Popular frameworks include TensorFlow,
    PyTorch, scikit-learn, and Keras for implementing machine learning models.
    """
    
    # First, segment the text
    from app.parsers.base import TextBlock
    
    # Create a text block (simulating parsed content)
    text_block = TextBlock(
        text=long_text,
        page=1,
        bbox={'x': 0, 'y': 0, 'width': 100, 'height': 100},
        font_info={'size': 12, 'family': 'Arial'}
    )
    
    # Segment the text
    segments = await segmentation_service.segment_text_blocks([text_block])
    
    print(f"Text segmented into {len(segments)} segments")
    
    # Extract entities from each segment
    all_entities = []
    for i, segment in enumerate(segments):
        print(f"\nSegment {i+1} ({len(segment.text)} chars):")
        print(f"  Text preview: {segment.text[:100]}...")
        
        # Extract entities from this segment
        segment_entities = await entity_service.extract_entities(segment.text)
        all_entities.extend(segment_entities)
        
        print(f"  Entities found: {len(segment_entities)}")
        for entity in segment_entities[:5]:  # Show first 5 entities
            print(f"    - '{entity.text}' ({entity.entity_type})")
    
    # Deduplicate entities across all segments
    if entity_service.config.enable_deduplication:
        all_entities = entity_service._deduplicate_entities(all_entities)
    
    print(f"\nTotal unique entities across all segments: {len(all_entities)}")
    
    # Rank all entities
    ranked_entities = entity_service.rank_entities_by_importance(all_entities, max_entities=15)
    
    print(f"\nTop 15 entities from segmented text:")
    for i, entity in enumerate(ranked_entities, 1):
        print(f"  {i}. '{entity.text}' ({entity.entity_type}) [score: {entity.importance_score:.3f}]")
    
    return segments, all_entities


async def entity_filtering_comparison_example():
    """Example comparing different filtering configurations."""
    print("\n=== Entity Filtering Comparison Example ===")
    
    text = """
    AI, ML, NLP, and CV are key areas of artificial intelligence research.
    The year 2023 saw investments of $10.5 billion in AI startups.
    Accuracy rates improved from 85% to 97.3% using new algorithms.
    Companies like Google, Meta, and OpenAI are leading the field.
    """
    
    # Strict filtering
    strict_config = EntityExtractionConfig(
        min_entity_length=3,
        min_confidence=0.8,
        filter_punctuation=True,
        filter_numbers_only=True,
        use_stopwords=True
    )
    strict_service = EntityExtractionService(strict_config)
    strict_entities = await strict_service.extract_entities(text)
    
    # Lenient filtering
    lenient_config = EntityExtractionConfig(
        min_entity_length=1,
        min_confidence=0.3,
        filter_punctuation=False,
        filter_numbers_only=False,
        use_stopwords=False
    )
    lenient_service = EntityExtractionService(lenient_config)
    lenient_entities = await lenient_service.extract_entities(text)
    
    print(f"Strict filtering ({len(strict_entities)} entities):")
    for entity in strict_entities:
        print(f"  - '{entity.text}' ({entity.entity_type}) [conf: {entity.confidence:.2f}]")
    
    print(f"\nLenient filtering ({len(lenient_entities)} entities):")
    for entity in lenient_entities:
        print(f"  - '{entity.text}' ({entity.entity_type}) [conf: {entity.confidence:.2f}]")
    
    print(f"\nFiltering impact: {len(lenient_entities) - len(strict_entities)} entities filtered out")
    
    return strict_entities, lenient_entities


async def main():
    """Run all examples."""
    print("Entity Extraction Service Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await basic_entity_extraction_example()
        await multilingual_extraction_example()
        await custom_configuration_example()
        await entity_ranking_example()
        await integration_with_text_segmentation_example()
        await entity_filtering_comparison_example()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())