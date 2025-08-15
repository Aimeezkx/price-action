"""
Integration test for chapter extraction functionality.
"""

import asyncio
import tempfile
from pathlib import Path

from app.services.chapter_service import ChapterExtractor
from app.parsers.base import TextBlock, ParsedContent


async def test_chapter_extraction_integration():
    """Test the complete chapter extraction pipeline."""
    
    print("Testing Chapter Extraction Integration...")
    
    # Create sample text blocks that simulate a parsed document
    text_blocks = [
        # Chapter 1
        TextBlock(
            text="Chapter 1: Introduction to Machine Learning",
            page=1,
            bbox={"x": 50, "y": 100, "width": 400, "height": 24},
            font_info={"size": 18, "font": "Arial-Bold", "flags": 16}
        ),
        TextBlock(
            text="Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
            page=1,
            bbox={"x": 50, "y": 150, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial", "flags": 0}
        ),
        TextBlock(
            text="This chapter provides an overview of the fundamental concepts and techniques used in machine learning.",
            page=1,
            bbox={"x": 50, "y": 200, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial", "flags": 0}
        ),
        
        # Section 1.1
        TextBlock(
            text="1.1 Types of Machine Learning",
            page=2,
            bbox={"x": 50, "y": 100, "width": 300, "height": 18},
            font_info={"size": 14, "font": "Arial-Bold", "flags": 16}
        ),
        TextBlock(
            text="There are three main types of machine learning: supervised, unsupervised, and reinforcement learning.",
            page=2,
            bbox={"x": 50, "y": 130, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial", "flags": 0}
        ),
        
        # Chapter 2
        TextBlock(
            text="Chapter 2: Supervised Learning",
            page=3,
            bbox={"x": 50, "y": 100, "width": 350, "height": 24},
            font_info={"size": 18, "font": "Arial-Bold", "flags": 16}
        ),
        TextBlock(
            text="Supervised learning involves training algorithms on labeled data to make predictions on new, unseen data.",
            page=3,
            bbox={"x": 50, "y": 150, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial", "flags": 0}
        ),
        
        # Section 2.1
        TextBlock(
            text="2.1 Linear Regression",
            page=4,
            bbox={"x": 50, "y": 100, "width": 200, "height": 18},
            font_info={"size": 14, "font": "Arial-Bold", "flags": 16}
        ),
        TextBlock(
            text="Linear regression is one of the simplest supervised learning algorithms.",
            page=4,
            bbox={"x": 50, "y": 130, "width": 400, "height": 20},
            font_info={"size": 12, "font": "Arial", "flags": 0}
        ),
    ]
    
    # Create parsed content
    parsed_content = ParsedContent(
        text_blocks=text_blocks,
        images=[],
        metadata={"title": "Machine Learning Textbook", "page_count": 4}
    )
    
    # Test chapter extraction
    extractor = ChapterExtractor()
    
    # Create a temporary file path for testing
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    
    try:
        # Extract chapters
        chapters = await extractor.extract_chapters(temp_path, parsed_content)
        
        print(f"✅ Extracted {len(chapters)} chapters")
        
        # Verify chapter structure
        assert len(chapters) >= 2, f"Expected at least 2 chapters, got {len(chapters)}"
        
        # Check first chapter
        chapter1 = chapters[0]
        assert "Introduction" in chapter1.title or "Chapter 1" in chapter1.title
        assert chapter1.level == 1
        assert chapter1.page_start == 1
        assert len(chapter1.content_blocks) > 0
        
        print(f"✅ Chapter 1: '{chapter1.title}' (Level {chapter1.level}, Pages {chapter1.page_start}-{chapter1.page_end})")
        print(f"   Content blocks: {len(chapter1.content_blocks)}")
        
        # Check second chapter
        chapter2 = chapters[1]
        assert "Supervised" in chapter2.title or "Chapter 2" in chapter2.title
        assert chapter2.level == 1
        assert chapter2.page_start >= 3
        assert len(chapter2.content_blocks) > 0
        
        print(f"✅ Chapter 2: '{chapter2.title}' (Level {chapter2.level}, Pages {chapter2.page_start}-{chapter2.page_end})")
        print(f"   Content blocks: {len(chapter2.content_blocks)}")
        
        # Verify content assignment (accounting for chapter titles being excluded)
        total_content_blocks = sum(len(ch.content_blocks) for ch in chapters)
        # Chapter titles are excluded from content blocks, so we expect fewer blocks
        expected_content_blocks = len(text_blocks) - len(chapters)  # Subtract chapter titles
        assert total_content_blocks >= expected_content_blocks - 1, f"Content blocks not properly assigned: {total_content_blocks} < {expected_content_blocks}"
        
        print("✅ All content blocks properly assigned to chapters")
        
        # Test hierarchical structure
        has_subsections = any(ch.level > 1 for ch in chapters)
        if has_subsections:
            print("✅ Hierarchical structure detected (subsections found)")
        else:
            print("ℹ️  No subsections detected (flat structure)")
        
        print("\n📊 Chapter Summary:")
        for i, chapter in enumerate(chapters):
            content_preview = ""
            if chapter.content_blocks:
                content_preview = chapter.content_blocks[0].text[:50] + "..."
            
            print(f"  {i+1}. {chapter.title}")
            print(f"     Level: {chapter.level}, Pages: {chapter.page_start}-{chapter.page_end}")
            print(f"     Content blocks: {len(chapter.content_blocks)}")
            print(f"     Preview: {content_preview}")
            print()
        
        return True
        
    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()


async def test_markdown_chapter_extraction():
    """Test chapter extraction from Markdown-style content."""
    
    print("Testing Markdown Chapter Extraction...")
    
    # Create Markdown-style text blocks
    text_blocks = [
        TextBlock(
            text="# Introduction",
            page=1,
            bbox={"x": 0, "y": 0, "width": 200, "height": 20},
            font_info={"size": 16, "font": "Arial-Bold"}
        ),
        TextBlock(
            text="This is the introduction content.",
            page=1,
            bbox={"x": 0, "y": 30, "width": 400, "height": 20},
            font_info={"size": 12, "font": "Arial"}
        ),
        TextBlock(
            text="## Getting Started",
            page=1,
            bbox={"x": 0, "y": 60, "width": 200, "height": 18},
            font_info={"size": 14, "font": "Arial-Bold"}
        ),
        TextBlock(
            text="Here's how to get started.",
            page=1,
            bbox={"x": 0, "y": 90, "width": 300, "height": 20},
            font_info={"size": 12, "font": "Arial"}
        ),
        TextBlock(
            text="# Methods",
            page=2,
            bbox={"x": 0, "y": 0, "width": 150, "height": 20},
            font_info={"size": 16, "font": "Arial-Bold"}
        ),
        TextBlock(
            text="This section describes the methods used.",
            page=2,
            bbox={"x": 0, "y": 30, "width": 400, "height": 20},
            font_info={"size": 12, "font": "Arial"}
        ),
    ]
    
    parsed_content = ParsedContent(text_blocks, [], {})
    
    extractor = ChapterExtractor()
    
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    
    try:
        chapters = await extractor.extract_chapters(temp_path, parsed_content)
        
        print(f"✅ Extracted {len(chapters)} chapters from Markdown content")
        
        # Should detect main headers as chapters
        assert len(chapters) >= 2
        
        # Check for proper level detection
        intro_chapter = next((ch for ch in chapters if "Introduction" in ch.title), None)
        assert intro_chapter is not None
        assert intro_chapter.level == 1
        
        methods_chapter = next((ch for ch in chapters if "Methods" in ch.title), None)
        assert methods_chapter is not None
        assert methods_chapter.level == 1
        
        # Check for subsection detection
        subsection = next((ch for ch in chapters if "Getting Started" in ch.title), None)
        if subsection:
            assert subsection.level == 2
            print("✅ Subsection properly detected with level 2")
        
        print("✅ Markdown chapter extraction successful")
        return True
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


async def test_fallback_single_chapter():
    """Test fallback to single chapter when no structure is detected."""
    
    print("Testing Fallback Single Chapter...")
    
    # Create text blocks with no clear headings
    text_blocks = [
        TextBlock(
            text="This is just regular paragraph text without any clear heading structure.",
            page=1,
            bbox={"x": 0, "y": 0, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial"}
        ),
        TextBlock(
            text="More regular content that doesn't look like a heading at all.",
            page=1,
            bbox={"x": 0, "y": 50, "width": 500, "height": 40},
            font_info={"size": 12, "font": "Arial"}
        ),
        TextBlock(
            text="Even more content on the second page.",
            page=2,
            bbox={"x": 0, "y": 0, "width": 400, "height": 20},
            font_info={"size": 12, "font": "Arial"}
        ),
    ]
    
    parsed_content = ParsedContent(text_blocks, [], {})
    
    extractor = ChapterExtractor()
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    
    try:
        chapters = await extractor.extract_chapters(temp_path, parsed_content)
        
        print(f"✅ Fallback created {len(chapters)} chapter(s)")
        
        # Should create exactly one chapter
        assert len(chapters) == 1
        
        chapter = chapters[0]
        assert chapter.title == "Document Content"
        assert chapter.level == 1
        assert chapter.page_start == 1
        assert chapter.page_end == 2
        assert len(chapter.content_blocks) == 3
        
        print("✅ Single chapter fallback working correctly")
        return True
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


async def main():
    """Run all integration tests."""
    print("🧪 Running Chapter Extraction Integration Tests\n")
    
    try:
        # Test 1: Standard chapter extraction
        await test_chapter_extraction_integration()
        print("=" * 60)
        
        # Test 2: Markdown chapter extraction
        await test_markdown_chapter_extraction()
        print("=" * 60)
        
        # Test 3: Fallback single chapter
        await test_fallback_single_chapter()
        print("=" * 60)
        
        print("🎉 All chapter extraction integration tests passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())