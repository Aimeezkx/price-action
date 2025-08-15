"""
Integration tests for entity extraction service.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.entity_extraction_service import (
    EntityExtractionService,
    EntityExtractionConfig,
    EntityType,
    Language
)


async def test_english_entity_extraction():
    """Test entity extraction from English text."""
    print("Testing English entity extraction...")
    
    service = EntityExtractionService()
    
    text = """
    Machine learning is a method of data analysis that automates analytical model building.
    It is a branch of artificial intelligence (AI) based on the idea that systems can learn
    from data, identify patterns and make decisions with minimal human intervention.
    
    Companies like Google, Microsoft, Amazon, and Facebook are heavily investing in AI research.
    Popular algorithms include neural networks, decision trees, support vector machines (SVM),
    and random forests. The GPT-3 model by OpenAI has 175 billion parameters and demonstrates
    remarkable natural language processing capabilities.
    
    Deep learning, a subset of machine learning, uses artificial neural networks with multiple
    layers to model and understand complex patterns. TensorFlow and PyTorch are popular
    frameworks for implementing deep learning models.
    """
    
    entities = await service.extract_entities(text, Language.ENGLISH)
    
    print(f"Extracted {len(entities)} entities:")
    for entity in entities[:15]:  # Show first 15 entities
        print(f"  - {entity.text} ({entity.entity_type}) [confidence: {entity.confidence:.2f}, freq: {entity.frequency}]")
    
    # Rank entities by importance
    ranked_entities = service.rank_entities_by_importance(entities, max_entities=10)
    print(f"\nTop 10 most important entities:")
    for i, entity in enumerate(ranked_entities, 1):
        print(f"  {i}. {entity.text} ({entity.entity_type}) [score: {entity.importance_score:.3f}]")
    
    # Get statistics
    stats = service.get_entity_statistics(entities)
    print(f"\nEntity Statistics:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Unique entities: {stats['unique_entities']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"  Average frequency: {stats['avg_frequency']}")
    print(f"  Entity types: {stats['entity_types']}")
    
    return len(entities) > 0


async def test_chinese_entity_extraction():
    """Test entity extraction from Chinese text."""
    print("\n" + "="*60)
    print("Testing Chinese entity extraction...")
    
    service = EntityExtractionService()
    
    text = """
    机器学习是数据分析的一种方法，它自动化分析模型的构建过程。它是人工智能（AI）的一个分支，
    基于系统可以从数据中学习、识别模式并在最少人工干预下做出决策的理念。
    
    像谷歌、微软、亚马逊和脸书这样的公司正在大力投资人工智能研究。流行的算法包括神经网络、
    决策树、支持向量机（SVM）和随机森林。OpenAI的GPT-3模型拥有1750亿参数，展现了
    卓越的自然语言处理能力。
    
    深度学习是机器学习的一个子集，使用具有多层的人工神经网络来建模和理解复杂模式。
    TensorFlow和PyTorch是实现深度学习模型的流行框架。
    """
    
    entities = await service.extract_entities(text, Language.CHINESE)
    
    print(f"Extracted {len(entities)} entities:")
    for entity in entities[:15]:  # Show first 15 entities
        print(f"  - {entity.text} ({entity.entity_type}) [confidence: {entity.confidence:.2f}, freq: {entity.frequency}]")
    
    # Rank entities by importance
    ranked_entities = service.rank_entities_by_importance(entities, max_entities=10)
    print(f"\nTop 10 most important entities:")
    for i, entity in enumerate(ranked_entities, 1):
        print(f"  {i}. {entity.text} ({entity.entity_type}) [score: {entity.importance_score:.3f}]")
    
    # Get statistics
    stats = service.get_entity_statistics(entities)
    print(f"\nEntity Statistics:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Unique entities: {stats['unique_entities']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"  Average frequency: {stats['avg_frequency']}")
    print(f"  Entity types: {stats['entity_types']}")
    
    return len(entities) > 0


async def test_technical_term_extraction():
    """Test technical term extraction."""
    print("\n" + "="*60)
    print("Testing technical term extraction...")
    
    service = EntityExtractionService()
    
    text = """
    The REST API uses HTTP protocol to communicate with the SQL database.
    The machine-learning algorithm processes JSON data and returns XML responses.
    Popular frameworks include TensorFlow, PyTorch, scikit-learn, and Keras.
    The system uses OAuth2 for authentication and JWT tokens for authorization.
    Data is stored in PostgreSQL and cached using Redis. The frontend is built
    with React.js and TypeScript, while the backend uses FastAPI and Python.
    """
    
    entities = await service.extract_entities(text, Language.ENGLISH)
    
    # Filter technical terms
    technical_entities = [e for e in entities if e.entity_type == EntityType.TECHNICAL_TERM]
    
    print(f"Extracted {len(technical_entities)} technical terms:")
    for entity in technical_entities:
        print(f"  - {entity.text} [confidence: {entity.confidence:.2f}, freq: {entity.frequency}]")
    
    return len(technical_entities) > 0


async def test_mixed_language_extraction():
    """Test entity extraction from mixed language text."""
    print("\n" + "="*60)
    print("Testing mixed language entity extraction...")
    
    service = EntityExtractionService()
    
    text = """
    Machine Learning (机器学习) is a subset of Artificial Intelligence (人工智能).
    Companies like Google (谷歌), Microsoft (微软), and OpenAI are leading the research.
    The neural network (神经网络) model achieved 95% accuracy on the dataset.
    Natural Language Processing (自然语言处理) is an important branch of AI.
    Deep learning algorithms (深度学习算法) can process large amounts of data.
    """
    
    entities = await service.extract_entities(text)
    
    print(f"Extracted {len(entities)} entities from mixed language text:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.entity_type}) [confidence: {entity.confidence:.2f}]")
    
    # Separate English and Chinese entities
    english_entities = [e for e in entities if any('a' <= c.lower() <= 'z' for c in e.text)]
    chinese_entities = [e for e in entities if any('\u4e00' <= c <= '\u9fff' for c in e.text)]
    
    print(f"\nEnglish entities: {len(english_entities)}")
    print(f"Chinese entities: {len(chinese_entities)}")
    
    return len(entities) > 0


async def test_entity_deduplication():
    """Test entity deduplication functionality."""
    print("\n" + "="*60)
    print("Testing entity deduplication...")
    
    config = EntityExtractionConfig(enable_deduplication=True, similarity_threshold=0.8)
    service = EntityExtractionService(config)
    
    text = """
    Machine learning and machine learning algorithms are important.
    AI and artificial intelligence are the same thing.
    Neural networks and neural network models are used in deep learning.
    Google and Google Inc. are the same company.
    """
    
    entities = await service.extract_entities(text, Language.ENGLISH)
    
    print(f"Extracted {len(entities)} entities after deduplication:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.entity_type}) [confidence: {entity.confidence:.2f}, freq: {entity.frequency}]")
    
    # Test without deduplication
    config_no_dedup = EntityExtractionConfig(enable_deduplication=False)
    service_no_dedup = EntityExtractionService(config_no_dedup)
    
    entities_no_dedup = await service_no_dedup.extract_entities(text, Language.ENGLISH)
    
    print(f"\nWithout deduplication: {len(entities_no_dedup)} entities")
    print(f"With deduplication: {len(entities)} entities")
    print(f"Reduction: {len(entities_no_dedup) - len(entities)} entities removed")
    
    return len(entities) < len(entities_no_dedup)


async def test_entity_filtering():
    """Test entity filtering functionality."""
    print("\n" + "="*60)
    print("Testing entity filtering...")
    
    # Test with strict filtering
    strict_config = EntityExtractionConfig(
        min_entity_length=3,
        min_confidence=0.7,
        filter_punctuation=True,
        filter_numbers_only=True
    )
    strict_service = EntityExtractionService(strict_config)
    
    # Test with lenient filtering
    lenient_config = EntityExtractionConfig(
        min_entity_length=1,
        min_confidence=0.1,
        filter_punctuation=False,
        filter_numbers_only=False
    )
    lenient_service = EntityExtractionService(lenient_config)
    
    text = """
    AI, ML, and NLP are important technologies. The year 2023 saw major advances.
    Companies invested $1.5 billion in research. The accuracy was 95.7%.
    """
    
    strict_entities = await strict_service.extract_entities(text, Language.ENGLISH)
    lenient_entities = await lenient_service.extract_entities(text, Language.ENGLISH)
    
    print(f"Strict filtering: {len(strict_entities)} entities")
    for entity in strict_entities:
        print(f"  - {entity.text} ({entity.entity_type})")
    
    print(f"\nLenient filtering: {len(lenient_entities)} entities")
    for entity in lenient_entities:
        print(f"  - {entity.text} ({entity.entity_type})")
    
    return len(strict_entities) <= len(lenient_entities)


async def main():
    """Run all integration tests."""
    print("Entity Extraction Service Integration Tests")
    print("=" * 60)
    
    tests = [
        ("English Entity Extraction", test_english_entity_extraction),
        ("Chinese Entity Extraction", test_chinese_entity_extraction),
        ("Technical Term Extraction", test_technical_term_extraction),
        ("Mixed Language Extraction", test_mixed_language_extraction),
        ("Entity Deduplication", test_entity_deduplication),
        ("Entity Filtering", test_entity_filtering),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"Error in {test_name}: {e}")
            results.append((test_name, "ERROR"))
    
    print("\n" + "="*60)
    print("Test Results Summary:")
    print("="*60)
    
    for test_name, status in results:
        status_symbol = "✓" if status == "PASSED" else "✗" if status == "FAILED" else "!"
        print(f"{status_symbol} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)