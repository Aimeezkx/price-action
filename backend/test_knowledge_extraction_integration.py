"""
Integration test for knowledge extraction service.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.knowledge_extraction_service import (
    KnowledgeExtractionService,
    KnowledgeExtractionConfig
)
from app.services.text_segmentation_service import TextSegment
from app.models.knowledge import KnowledgeType


async def test_knowledge_extraction_integration():
    """Test the complete knowledge extraction pipeline."""
    
    print("Testing Knowledge Extraction Service Integration...")
    
    # Initialize service
    config = KnowledgeExtractionConfig(
        use_llm=False,  # Use rule-based extraction for testing
        enable_fallback=True,
        min_confidence=0.4,  # Lower threshold for testing
        max_knowledge_points_per_segment=5
    )
    
    service = KnowledgeExtractionService(config)
    print("✓ Service initialized successfully")
    
    # Create test segments with different knowledge types
    test_segments = [
        # Definition
        TextSegment(
            text="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            character_count=250,
            word_count=40,
            sentence_count=2,
            anchors={
                "page": 1,
                "chapter_id": "test_chapter",
                "position": {"block_index": 0, "bbox": {"x": 0, "y": 0, "width": 100, "height": 20}}
            },
            original_blocks=[0]
        ),
        
        # Example
        TextSegment(
            text="For example, a recommendation system like Netflix uses machine learning algorithms to analyze viewing patterns and suggest movies that users might enjoy. Another example is email spam detection, which uses classification algorithms to identify unwanted messages.",
            character_count=280,
            word_count=42,
            sentence_count=2,
            anchors={
                "page": 1,
                "chapter_id": "test_chapter",
                "position": {"block_index": 1, "bbox": {"x": 0, "y": 25, "width": 100, "height": 20}}
            },
            original_blocks=[1]
        ),
        
        # Process
        TextSegment(
            text="The machine learning process involves several steps: Step 1: Data collection and preparation. Step 2: Feature selection and engineering. Step 3: Model selection and training. Step 4: Model evaluation and validation. Step 5: Deployment and monitoring.",
            character_count=270,
            word_count=40,
            sentence_count=6,
            anchors={
                "page": 2,
                "chapter_id": "test_chapter",
                "position": {"block_index": 2, "bbox": {"x": 0, "y": 50, "width": 100, "height": 20}}
            },
            original_blocks=[2]
        ),
        
        # Fact
        TextSegment(
            text="Research shows that deep learning models require large amounts of data to perform effectively. Studies indicate that neural networks with millions of parameters can achieve state-of-the-art performance on complex tasks like image recognition and natural language processing.",
            character_count=290,
            word_count=43,
            sentence_count=2,
            anchors={
                "page": 2,
                "chapter_id": "test_chapter",
                "position": {"block_index": 3, "bbox": {"x": 0, "y": 75, "width": 100, "height": 20}}
            },
            original_blocks=[3]
        ),
        
        # Theorem
        TextSegment(
            text="Theorem: Universal Approximation Theorem states that a feedforward network with a single hidden layer containing a finite number of neurons can approximate continuous functions on compact subsets of Rn, under mild assumptions on the activation function.",
            character_count=270,
            word_count=38,
            sentence_count=1,
            anchors={
                "page": 3,
                "chapter_id": "test_chapter",
                "position": {"block_index": 4, "bbox": {"x": 0, "y": 100, "width": 100, "height": 20}}
            },
            original_blocks=[4]
        )
    ]
    
    print(f"✓ Created {len(test_segments)} test segments")
    
    # Test knowledge extraction
    try:
        knowledge_points = await service.extract_knowledge_from_segments(
            test_segments, "test_chapter"
        )
        
        print(f"✓ Extracted {len(knowledge_points)} knowledge points")
        
        # Verify extraction results
        if not knowledge_points:
            print("✗ No knowledge points extracted")
            return False
        
        # Check that different types were extracted
        extracted_types = set(kp.kind for kp in knowledge_points)
        print(f"✓ Extracted knowledge types: {[t.value for t in extracted_types]}")
        
        # Verify each knowledge point
        for i, kp in enumerate(knowledge_points):
            print(f"\nKnowledge Point {i+1}:")
            print(f"  Type: {kp.kind.value}")
            print(f"  Text: {kp.text[:100]}...")
            print(f"  Entities: {kp.entities}")
            print(f"  Confidence: {kp.confidence:.3f}")
            print(f"  Anchors: {kp.anchors}")
            
            # Verify required fields
            assert kp.text, "Knowledge point text is empty"
            assert kp.kind in KnowledgeType, f"Invalid knowledge type: {kp.kind}"
            assert 0.0 <= kp.confidence <= 1.0, f"Invalid confidence: {kp.confidence}"
            assert kp.anchors, "Anchors are empty"
            assert "chapter_id" in kp.anchors, "Chapter ID missing from anchors"
            assert kp.anchors["chapter_id"] == "test_chapter", "Incorrect chapter ID"
        
        print("✓ All knowledge points have valid structure")
        
        # Test statistics
        stats = service.get_extraction_statistics(knowledge_points)
        print(f"\nExtraction Statistics:")
        print(f"  Total knowledge points: {stats['total_knowledge_points']}")
        print(f"  By type: {stats['by_type']}")
        print(f"  Average confidence: {stats['avg_confidence']}")
        print(f"  Extraction methods: {stats['extraction_methods']}")
        
        # Verify we extracted at least some of each expected type
        expected_types = {
            KnowledgeType.DEFINITION,
            KnowledgeType.EXAMPLE,
            KnowledgeType.PROCESS,
            KnowledgeType.FACT
        }
        
        found_types = set(kp.kind for kp in knowledge_points)
        missing_types = expected_types - found_types
        
        if missing_types:
            print(f"⚠ Missing expected types: {[t.value for t in missing_types]}")
        else:
            print("✓ All expected knowledge types found")
        
        # Test specific pattern matching
        print("\nTesting specific patterns:")
        
        # Check for definition
        definitions = [kp for kp in knowledge_points if kp.kind == KnowledgeType.DEFINITION]
        if definitions:
            print(f"✓ Found {len(definitions)} definition(s)")
            for defn in definitions:
                if "machine learning is" in defn.text.lower():
                    print("✓ Correctly identified machine learning definition")
                    break
        
        # Check for examples
        examples = [kp for kp in knowledge_points if kp.kind == KnowledgeType.EXAMPLE]
        if examples:
            print(f"✓ Found {len(examples)} example(s)")
            for ex in examples:
                if "for example" in ex.text.lower() or "another example" in ex.text.lower():
                    print("✓ Correctly identified examples with trigger phrases")
                    break
        
        # Check for processes
        processes = [kp for kp in knowledge_points if kp.kind == KnowledgeType.PROCESS]
        if processes:
            print(f"✓ Found {len(processes)} process(es)")
            for proc in processes:
                if "step" in proc.text.lower():
                    print("✓ Correctly identified process with steps")
                    break
        
        # Check for facts
        facts = [kp for kp in knowledge_points if kp.kind == KnowledgeType.FACT]
        if facts:
            print(f"✓ Found {len(facts)} fact(s)")
            for fact in facts:
                if "research shows" in fact.text.lower() or "studies indicate" in fact.text.lower():
                    print("✓ Correctly identified research-based facts")
                    break
        
        # Check for theorems
        theorems = [kp for kp in knowledge_points if kp.kind == KnowledgeType.THEOREM]
        if theorems:
            print(f"✓ Found {len(theorems)} theorem(s)")
            for thm in theorems:
                if "theorem" in thm.text.lower():
                    print("✓ Correctly identified theorem")
                    break
        
        print("\n✓ Knowledge extraction integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error during knowledge extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases and error handling."""
    
    print("\nTesting edge cases...")
    
    service = KnowledgeExtractionService()
    
    # Test empty segments
    empty_result = await service.extract_knowledge_from_segments([], "test_chapter")
    assert empty_result == [], "Empty segments should return empty list"
    print("✓ Empty segments handled correctly")
    
    # Test segment with no extractable knowledge
    no_knowledge_segment = TextSegment(
        text="The quick brown fox jumps over the lazy dog.",
        character_count=44,
        word_count=9,
        sentence_count=1,
        anchors={"page": 1, "chapter_id": "test"},
        original_blocks=[0]
    )
    
    no_knowledge_result = await service.extract_knowledge_from_segments(
        [no_knowledge_segment], "test_chapter"
    )
    print(f"✓ No-knowledge segment returned {len(no_knowledge_result)} points")
    
    # Test very short segment
    short_segment = TextSegment(
        text="AI is smart.",
        character_count=12,
        word_count=3,
        sentence_count=1,
        anchors={"page": 1, "chapter_id": "test"},
        original_blocks=[0]
    )
    
    short_result = await service.extract_knowledge_from_segments(
        [short_segment], "test_chapter"
    )
    print(f"✓ Short segment returned {len(short_result)} points")
    
    print("✓ Edge cases handled successfully")


async def main():
    """Run all integration tests."""
    
    print("=" * 60)
    print("KNOWLEDGE EXTRACTION SERVICE INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        # Test main functionality
        success = await test_knowledge_extraction_integration()
        
        if success:
            # Test edge cases
            await test_edge_cases()
            
            print("\n" + "=" * 60)
            print("ALL TESTS PASSED! ✓")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("TESTS FAILED! ✗")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n✗ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)