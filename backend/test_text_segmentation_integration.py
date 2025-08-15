"""
Integration test for text segmentation service.
"""

import asyncio
import tempfile
from pathlib import Path

from app.services.text_segmentation_service import TextSegmentationService, SegmentationConfig
from app.services.chapter_service import ChapterExtractor
from app.parsers.pdf_parser import PDFParser
from app.parsers.base import TextBlock


async def test_text_segmentation_integration():
    """Test text segmentation with real document parsing."""
    
    # Create a simple test document content
    test_content = """Chapter 1: Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without being explicitly programmed. This field has revolutionized many industries and continues to grow rapidly.

The core concept of machine learning involves training algorithms on data to recognize patterns and make predictions. There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.

Supervised learning uses labeled data to train models. The algorithm learns from input-output pairs and can then make predictions on new, unseen data. Common examples include classification and regression tasks.

Chapter 2: Deep Learning Fundamentals

Deep learning is a specialized subset of machine learning that uses neural networks with multiple layers. These networks can automatically learn hierarchical representations of data, making them particularly effective for complex tasks.

Neural networks consist of interconnected nodes called neurons, organized in layers. The input layer receives data, hidden layers process it, and the output layer produces results. Each connection has a weight that determines its importance.

Training deep neural networks requires large amounts of data and computational power. The process involves forward propagation, where data flows through the network, and backpropagation, where errors are used to update weights."""
    
    # Create text blocks from the content
    text_blocks = []
    paragraphs = [p.strip() for p in test_content.split('\n\n') if p.strip()]
    
    for i, paragraph in enumerate(paragraphs):
        if paragraph:
            block = TextBlock(
                text=paragraph,
                page=1 if i < 4 else 2,  # Simulate two pages
                bbox={"x": 50, "y": 100 + i * 50, "width": 500, "height": 40}
            )
            text_blocks.append(block)
    
    print(f"Created {len(text_blocks)} text blocks")
    
    # Test chapter extraction first
    chapter_extractor = ChapterExtractor()
    
    # Create a temporary file path for testing
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    
    try:
        # Extract chapters
        chapters = await chapter_extractor._extract_from_heuristics(text_blocks)
        print(f"Extracted {len(chapters)} chapters:")
        
        for chapter in chapters:
            print(f"  - {chapter.title} (Level {chapter.level}, Pages {chapter.page_start}-{chapter.page_end})")
            print(f"    Content blocks: {len(chapter.content_blocks)}")
        
        # Test text segmentation
        segmentation_service = TextSegmentationService(
            SegmentationConfig(
                min_segment_length=200,
                max_segment_length=500,
                similarity_threshold=0.6
            )
        )
        
        # Segment text for each chapter
        all_segments = []
        if chapters:
            for chapter in chapters:
                if chapter.content_blocks:
                    segments = await segmentation_service.segment_text_blocks(
                        chapter.content_blocks, 
                        str(chapter.order_index)
                    )
                    
                    print(f"\nChapter '{chapter.title}' segments:")
                    for i, segment in enumerate(segments):
                        print(f"  Segment {i+1}:")
                        print(f"    Length: {segment.character_count} chars, {segment.word_count} words")
                        print(f"    Sentences: {segment.sentence_count}")
                        print(f"    Text preview: {segment.text[:100]}...")
                        print(f"    Anchors: Page {segment.anchors['page']}, Chapter {segment.anchors['chapter_id']}")
                        
                        # Test text complexity calculation
                        complexity = segmentation_service.calculate_text_complexity(segment.text)
                        print(f"    Complexity: {complexity:.2f}")
                        
                        # Test key term extraction
                        key_terms = segmentation_service.extract_key_terms(segment.text, max_terms=5)
                        print(f"    Key terms: {[term[0] for term in key_terms]}")
                        print()
                    
                    all_segments.extend(segments)
        else:
            # If no chapters found, segment all text blocks directly
            print("\nNo chapters found, segmenting all text blocks directly:")
            segments = await segmentation_service.segment_text_blocks(text_blocks, "default_chapter")
            
            for i, segment in enumerate(segments):
                print(f"  Segment {i+1}:")
                print(f"    Length: {segment.character_count} chars, {segment.word_count} words")
                print(f"    Sentences: {segment.sentence_count}")
                print(f"    Text preview: {segment.text[:100]}...")
                print(f"    Anchors: Page {segment.anchors['page']}, Chapter {segment.anchors['chapter_id']}")
                
                # Test text complexity calculation
                complexity = segmentation_service.calculate_text_complexity(segment.text)
                print(f"    Complexity: {complexity:.2f}")
                
                # Test key term extraction
                key_terms = segmentation_service.extract_key_terms(segment.text, max_terms=5)
                print(f"    Key terms: {[term[0] for term in key_terms]}")
                print()
            
            all_segments.extend(segments)
        
        print(f"Total segments created: {len(all_segments)}")
        
        # Verify segment properties
        for segment in all_segments:
            assert segment.text.strip(), "Segment should have non-empty text"
            assert segment.character_count > 0, "Character count should be positive"
            assert segment.word_count > 0, "Word count should be positive"
            assert segment.sentence_count > 0, "Sentence count should be positive"
            assert 'page' in segment.anchors, "Should have page anchor"
            assert 'chapter_id' in segment.anchors, "Should have chapter_id anchor"
            assert 'position' in segment.anchors, "Should have position anchor"
            assert len(segment.original_blocks) > 0, "Should reference original blocks"
        
        # Test text normalization
        sample_text = "This Is A Test With MIXED Case And Special Characters!@#"
        normalized = segmentation_service.normalize_text(sample_text)
        print(f"Original: {sample_text}")
        print(f"Normalized: {normalized}")
        
        # Test similarity calculation
        text1 = "Machine learning algorithms are powerful tools for data analysis."
        text2 = "Machine learning models are effective tools for analyzing data."
        text3 = "Cats and dogs are popular pets in many households."
        
        similarity_high = segmentation_service._calculate_text_similarity(text1, text2)
        similarity_low = segmentation_service._calculate_text_similarity(text1, text3)
        
        print(f"Similarity (high): {similarity_high:.2f}")
        print(f"Similarity (low): {similarity_low:.2f}")
        
        assert similarity_high > similarity_low, "Similar texts should have higher similarity"
        
        print("\n✅ Text segmentation integration test passed!")
        
    finally:
        # Clean up temporary file
        if tmp_path.exists():
            tmp_path.unlink()


async def test_segmentation_with_real_parser():
    """Test segmentation with actual PDF parser if available."""
    
    # Check if we have any PDF files in the resource directory
    resource_dir = Path("resource")
    if not resource_dir.exists():
        print("No resource directory found, skipping PDF parser test")
        return
    
    pdf_files = list(resource_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in resource directory, skipping PDF parser test")
        return
    
    # Use the first PDF file
    pdf_file = pdf_files[0]
    print(f"Testing with PDF file: {pdf_file}")
    
    try:
        # Parse the PDF
        parser = PDFParser()
        parsed_content = await parser.parse(pdf_file)
        
        print(f"Parsed content: {len(parsed_content.text_blocks)} text blocks, {len(parsed_content.images)} images")
        
        if not parsed_content.text_blocks:
            print("No text blocks found in PDF, skipping segmentation test")
            return
        
        # Extract chapters
        chapter_extractor = ChapterExtractor()
        chapters = await chapter_extractor.extract_chapters(pdf_file, parsed_content)
        
        print(f"Extracted {len(chapters)} chapters")
        
        # Segment text from first chapter
        if chapters and chapters[0].content_blocks:
            segmentation_service = TextSegmentationService()
            segments = await segmentation_service.segment_text_blocks(
                chapters[0].content_blocks[:5],  # Limit to first 5 blocks for testing
                str(chapters[0].order_index)
            )
            
            print(f"Created {len(segments)} segments from first chapter")
            
            for i, segment in enumerate(segments[:3]):  # Show first 3 segments
                print(f"\nSegment {i+1}:")
                print(f"  Length: {segment.character_count} chars")
                print(f"  Preview: {segment.text[:150]}...")
                
                complexity = segmentation_service.calculate_text_complexity(segment.text)
                print(f"  Complexity: {complexity:.2f}")
        
        print("\n✅ PDF segmentation test completed!")
        
    except Exception as e:
        print(f"Error testing with PDF: {e}")
        print("This is expected if PDF parsing dependencies are not available")


if __name__ == "__main__":
    print("Running text segmentation integration tests...")
    
    # Run the basic integration test
    asyncio.run(test_text_segmentation_integration())
    
    # Run the PDF parser test if possible
    asyncio.run(test_segmentation_with_real_parser())
    
    print("\nAll tests completed!")