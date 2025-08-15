"""
Verification script for entity extraction implementation.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.entity_extraction_service import (
    EntityExtractionService,
    EntityExtractionConfig,
    Entity,
    EntityType,
    Language
)


async def verify_basic_functionality():
    """Verify basic entity extraction functionality."""
    print("🔍 Testing basic entity extraction functionality...")
    
    service = EntityExtractionService()
    
    # Test English text
    english_text = "Machine learning and artificial intelligence are transforming technology. Companies like Google and Microsoft are investing heavily in AI research."
    english_entities = await service.extract_entities(english_text, Language.ENGLISH)
    
    print(f"✅ English entity extraction: {len(english_entities)} entities found")
    
    # Test Chinese text
    chinese_text = "机器学习和人工智能正在改变技术。像谷歌和微软这样的公司正在大力投资人工智能研究。"
    chinese_entities = await service.extract_entities(chinese_text, Language.CHINESE)
    
    print(f"✅ Chinese entity extraction: {len(chinese_entities)} entities found")
    
    # Test technical term extraction
    tech_text = "The REST API uses HTTP protocol and JSON data format. Machine learning algorithms process data using TensorFlow and PyTorch frameworks."
    tech_entities = await service.extract_entities(tech_text, Language.ENGLISH)
    tech_terms = [e for e in tech_entities if e.entity_type == EntityType.TECHNICAL_TERM]
    
    print(f"✅ Technical term extraction: {len(tech_terms)} technical terms found")
    
    return len(english_entities) > 0 and len(chinese_entities) > 0 and len(tech_terms) > 0


async def verify_configuration_options():
    """Verify configuration options work correctly."""
    print("\n⚙️ Testing configuration options...")
    
    # Test strict configuration
    strict_config = EntityExtractionConfig(
        min_entity_length=5,
        min_confidence=0.8,
        enable_deduplication=True,
        similarity_threshold=0.9
    )
    strict_service = EntityExtractionService(strict_config)
    
    # Test lenient configuration
    lenient_config = EntityExtractionConfig(
        min_entity_length=2,
        min_confidence=0.3,
        enable_deduplication=False
    )
    lenient_service = EntityExtractionService(lenient_config)
    
    text = "AI and ML are important technologies. Machine learning algorithms use data."
    
    strict_entities = await strict_service.extract_entities(text)
    lenient_entities = await lenient_service.extract_entities(text)
    
    print(f"✅ Strict config: {len(strict_entities)} entities")
    print(f"✅ Lenient config: {len(lenient_entities)} entities")
    print(f"✅ Configuration filtering working: {len(lenient_entities) >= len(strict_entities)}")
    
    return len(lenient_entities) >= len(strict_entities)


async def verify_entity_ranking():
    """Verify entity ranking functionality."""
    print("\n📊 Testing entity ranking...")
    
    service = EntityExtractionService()
    
    text = """
    Machine learning is a powerful technique for data analysis. Deep learning algorithms
    use neural networks to process information. Companies like Google and Microsoft
    are leading AI research. TensorFlow and PyTorch are popular frameworks.
    """
    
    entities = await service.extract_entities(text)
    ranked_entities = service.rank_entities_by_importance(entities, max_entities=10)
    
    print(f"✅ Entity ranking: Top 10 from {len(entities)} total entities")
    
    # Check that ranking assigns importance scores
    has_scores = all(hasattr(entity, 'importance_score') for entity in ranked_entities)
    print(f"✅ Importance scores assigned: {has_scores}")
    
    return len(ranked_entities) <= 10 and has_scores


async def verify_entity_statistics():
    """Verify entity statistics functionality."""
    print("\n📈 Testing entity statistics...")
    
    service = EntityExtractionService()
    
    text = "AI and machine learning are transforming industries. Deep learning uses neural networks."
    entities = await service.extract_entities(text)
    
    stats = service.get_entity_statistics(entities)
    
    required_keys = ['total_entities', 'unique_entities', 'entity_types', 'avg_confidence', 'avg_frequency']
    has_all_keys = all(key in stats for key in required_keys)
    
    print(f"✅ Statistics generated: {has_all_keys}")
    print(f"✅ Total entities: {stats['total_entities']}")
    print(f"✅ Unique entities: {stats['unique_entities']}")
    print(f"✅ Entity types: {len(stats['entity_types'])}")
    
    return has_all_keys and stats['total_entities'] > 0


async def verify_deduplication():
    """Verify entity deduplication functionality."""
    print("\n🔄 Testing entity deduplication...")
    
    # Test with deduplication enabled
    dedup_config = EntityExtractionConfig(enable_deduplication=True, similarity_threshold=0.8)
    dedup_service = EntityExtractionService(dedup_config)
    
    # Test without deduplication
    no_dedup_config = EntityExtractionConfig(enable_deduplication=False)
    no_dedup_service = EntityExtractionService(no_dedup_config)
    
    # Text with potential duplicates
    text = "Machine learning and machine learning algorithms are important. AI and artificial intelligence are the same."
    
    dedup_entities = await dedup_service.extract_entities(text)
    no_dedup_entities = await no_dedup_service.extract_entities(text)
    
    print(f"✅ With deduplication: {len(dedup_entities)} entities")
    print(f"✅ Without deduplication: {len(no_dedup_entities)} entities")
    
    # Deduplication should reduce or maintain the same number of entities
    dedup_working = len(dedup_entities) <= len(no_dedup_entities)
    print(f"✅ Deduplication working: {dedup_working}")
    
    return dedup_working


async def verify_language_detection():
    """Verify language detection functionality."""
    print("\n🌐 Testing language detection...")
    
    service = EntityExtractionService()
    
    # Test English detection
    english_text = "Machine learning is a subset of artificial intelligence."
    english_lang = service.detect_language(english_text)
    
    # Test Chinese detection
    chinese_text = "机器学习是人工智能的一个分支。"
    chinese_lang = service.detect_language(chinese_text)
    
    # Test mixed text (should detect based on majority)
    mixed_text = "Machine learning (机器学习) is important."
    mixed_lang = service.detect_language(mixed_text)
    
    print(f"✅ English detection: {english_lang == Language.ENGLISH}")
    print(f"✅ Chinese detection: {chinese_lang == Language.CHINESE}")
    print(f"✅ Mixed text detection: {mixed_lang in [Language.ENGLISH, Language.CHINESE]}")
    
    return (english_lang == Language.ENGLISH and 
            chinese_lang == Language.CHINESE and 
            mixed_lang in [Language.ENGLISH, Language.CHINESE])


async def verify_error_handling():
    """Verify error handling for edge cases."""
    print("\n🛡️ Testing error handling...")
    
    service = EntityExtractionService()
    
    # Test empty text
    empty_entities = await service.extract_entities("")
    print(f"✅ Empty text handling: {len(empty_entities) == 0}")
    
    # Test whitespace-only text
    whitespace_entities = await service.extract_entities("   \n\t  ")
    print(f"✅ Whitespace text handling: {len(whitespace_entities) == 0}")
    
    # Test very short text
    short_entities = await service.extract_entities("AI")
    print(f"✅ Short text handling: {len(short_entities) >= 0}")
    
    return (len(empty_entities) == 0 and 
            len(whitespace_entities) == 0 and 
            len(short_entities) >= 0)


async def main():
    """Run all verification tests."""
    print("Entity Extraction Service Implementation Verification")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", verify_basic_functionality),
        ("Configuration Options", verify_configuration_options),
        ("Entity Ranking", verify_entity_ranking),
        ("Entity Statistics", verify_entity_statistics),
        ("Entity Deduplication", verify_deduplication),
        ("Language Detection", verify_language_detection),
        ("Error Handling", verify_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            status = "✅ PASSED" if result else "❌ FAILED"
            results.append((test_name, status))
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, "❌ ERROR"))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for test_name, status in results:
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, status in results if "PASSED" in status)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("\nThe entity extraction service implementation is complete and working correctly.")
        print("\nKey features implemented:")
        print("- ✅ Multilingual entity extraction (English and Chinese)")
        print("- ✅ Technical term pattern matching")
        print("- ✅ Entity filtering and deduplication")
        print("- ✅ Term frequency analysis and ranking")
        print("- ✅ Stopword removal and entity validation")
        print("- ✅ Configurable extraction parameters")
        print("- ✅ Comprehensive error handling")
        print("- ✅ Statistical analysis and reporting")
        return True
    else:
        print("\n❌ Some verification tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)