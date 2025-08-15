"""
Example usage of the text segmentation service.
"""

import asyncio
from pathlib import Path

from .text_segmentation_service import TextSegmentationService, SegmentationConfig
from ..parsers.base import TextBlock


async def example_text_segmentation():
    """Demonstrate text segmentation functionality."""
    
    print("=== Text Segmentation Service Example ===\n")
    
    # Create sample text blocks
    sample_blocks = [
        TextBlock(
            text="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            page=1,
            bbox={"x": 50, "y": 100, "width": 500, "height": 40}
        ),
        TextBlock(
            text="Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.",
            page=1,
            bbox={"x": 50, "y": 150, "width": 500, "height": 40}
        ),
        TextBlock(
            text="Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data.",
            page=2,
            bbox={"x": 50, "y": 100, "width": 500, "height": 40}
        )
    ]
    
    # Configure segmentation service
    config = SegmentationConfig(
        min_segment_length=150,
        max_segment_length=400,
        similarity_threshold=0.7,
        preserve_sentence_boundaries=True
    )
    
    service = TextSegmentationService(config)
    
    print("Input text blocks:")
    for i, block in enumerate(sample_blocks):
        print(f"  Block {i+1} (Page {block.page}): {block.text[:80]}...")
    
    print(f"\nSegmentation configuration:")
    print(f"  Min length: {config.min_segment_length} chars")
    print(f"  Max length: {config.max_segment_length} chars")
    print(f"  Similarity threshold: {config.similarity_threshold}")
    print(f"  Preserve sentences: {config.preserve_sentence_boundaries}")
    
    # Segment the text blocks
    segments = await service.segment_text_blocks(sample_blocks, "example_chapter")
    
    print(f"\nGenerated {len(segments)} segments:")
    print("=" * 60)
    
    for i, segment in enumerate(segments):
        print(f"\nSegment {i+1}:")
        print(f"  Length: {segment.character_count} chars, {segment.word_count} words")
        print(f"  Sentences: {segment.sentence_count}")
        print(f"  Page: {segment.anchors['page']}")
        print(f"  Chapter: {segment.anchors['chapter_id']}")
        print(f"  Original blocks: {segment.original_blocks}")
        
        # Calculate complexity
        complexity = service.calculate_text_complexity(segment.text)
        print(f"  Complexity: {complexity:.2f}")
        
        # Extract key terms
        key_terms = service.extract_key_terms(segment.text, max_terms=5)
        print(f"  Key terms: {[f'{term}({count})' for term, count in key_terms]}")
        
        print(f"  Text: {segment.text}")
    
    # Demonstrate text cleaning
    print(f"\n{'='*60}")
    print("Text Cleaning Examples:")
    
    dirty_texts = [
        "  This   has    excessive   whitespace.  ",
        'This text has "smart quotes" and \'apostrophes\'.',
        "Page 123\n\nThis text has page numbers.",
        "Text with...excessive...dots and---dashes."
    ]
    
    for dirty_text in dirty_texts:
        dirty_block = TextBlock(
            text=dirty_text,
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        cleaned_block = service._clean_text_block(dirty_block)
        print(f"  Original: '{dirty_text}'")
        print(f"  Cleaned:  '{cleaned_block.text}'")
        print()
    
    # Demonstrate text normalization
    print("Text Normalization Examples:")
    test_texts = [
        "This Is A Test With MIXED Case!",
        "Text with Special Characters: @#$%^&*()",
        "Multiple    Spaces    Between    Words"
    ]
    
    for text in test_texts:
        normalized = service.normalize_text(text)
        print(f"  Original:   '{text}'")
        print(f"  Normalized: '{normalized}'")
        print()
    
    # Demonstrate similarity calculation
    print("Text Similarity Examples:")
    text_pairs = [
        ("Machine learning is powerful", "Machine learning algorithms are effective"),
        ("Deep learning uses neural networks", "Cats and dogs are pets"),
        ("Natural language processing", "NLP processes human language")
    ]
    
    for text1, text2 in text_pairs:
        similarity = service._calculate_text_similarity(text1, text2)
        print(f"  Text 1: '{text1}'")
        print(f"  Text 2: '{text2}'")
        print(f"  Similarity: {similarity:.2f}")
        print()


if __name__ == "__main__":
    asyncio.run(example_text_segmentation())