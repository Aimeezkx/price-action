#!/usr/bin/env python3
"""
Test document parsing with real document files from the uploads directory.

This script tests the complete parsing pipeline with actual uploaded documents.
"""

import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_documents():
    """Test parsing with real documents from uploads directory."""
    print("🧪 Testing Real Document Parsing")
    print("=" * 50)
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ Uploads directory not found")
        return False
    
    # Find test documents
    test_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.docx"]:
        test_files.extend(uploads_dir.glob(pattern))
    
    if not test_files:
        print("⚠️  No test documents found in uploads directory")
        # Create a simple test document
        test_txt = uploads_dir / "parser_test.txt"
        test_content = """Document Learning Application Test

This is a test document created to verify the document parsing functionality.

Key Features:
- Document upload and processing
- Automatic flashcard generation
- Knowledge extraction
- Multi-format support (PDF, DOCX, TXT, MD)

Technical Details:
The system uses various parsers to extract content from different document formats.
Each parser is optimized for its specific format while maintaining a consistent interface.

Testing Scenarios:
1. Text extraction and segmentation
2. Metadata extraction
3. Error handling for corrupted files
4. Performance with large documents

This document should be parsed into multiple text blocks for processing."""
        
        test_txt.write_text(test_content, encoding='utf-8')
        test_files = [test_txt]
    
    print(f"Found {len(test_files)} test documents")
    
    # Test each document
    for file_path in test_files[:5]:  # Limit to first 5 files
        try:
            print(f"\n📄 Testing: {file_path.name}")
            
            # Get parser
            from app.parsers.factory import get_parser_for_file
            parser = get_parser_for_file(file_path)
            
            if not parser:
                print(f"❌ No parser available for {file_path.suffix}")
                continue
            
            print(f"✅ Using parser: {parser.name}")
            
            # Parse document
            start_time = asyncio.get_event_loop().time()
            parsed_content = await parser.parse(file_path)
            parse_time = asyncio.get_event_loop().time() - start_time
            
            print(f"✅ Parsed in {parse_time:.2f} seconds")
            print(f"   - Text blocks: {len(parsed_content.text_blocks)}")
            print(f"   - Images: {len(parsed_content.images)}")
            print(f"   - Metadata: {len(parsed_content.metadata)} fields")
            
            # Show sample content
            if parsed_content.text_blocks:
                first_block = parsed_content.text_blocks[0]
                print(f"   - First block: {first_block.text[:150]}...")
                print(f"   - Block dimensions: {first_block.bbox}")
            
            if parsed_content.images:
                first_image = parsed_content.images[0]
                print(f"   - First image: {first_image.image_path}")
                print(f"   - Image format: {first_image.format}")
            
            # Show interesting metadata
            metadata = parsed_content.metadata
            interesting_keys = ['format', 'page_count', 'word_count', 'character_count']
            for key in interesting_keys:
                if key in metadata:
                    print(f"   - {key}: {metadata[key]}")
            
        except Exception as e:
            print(f"❌ Failed to parse {file_path.name}: {e}")
            logger.exception(f"Error parsing {file_path}")
    
    print("\n" + "=" * 50)
    print("🎉 Real document parsing test completed!")

async def test_processing_pipeline_integration():
    """Test integration with the processing pipeline."""
    print("\n🔄 Testing Processing Pipeline Integration")
    print("=" * 50)
    
    try:
        from app.services.document_processing_pipeline import DocumentProcessingPipeline
        
        pipeline = DocumentProcessingPipeline()
        
        # Test parser selection logic
        test_extensions = ['.pdf', '.docx', '.txt', '.md', '.xyz']
        
        for ext in test_extensions:
            test_file = Path(f"test{ext}")
            
            from app.parsers.factory import get_parser_for_file
            parser = get_parser_for_file(test_file)
            
            if parser:
                print(f"✅ {ext}: {parser.name}")
            else:
                print(f"❌ {ext}: No parser available")
        
        # Test error handling in pipeline context
        print("\n🛡️  Testing Error Handling...")
        
        # Test with non-existent file
        try:
            from app.models.document import Document
            from uuid import uuid4
            
            # Create a mock document object
            class MockDocument:
                def __init__(self):
                    self.id = uuid4()
                    self.file_path = "nonexistent.txt"
                    self.file_type = "txt"
            
            mock_doc = MockDocument()
            
            # This should raise a ProcessingError
            try:
                await pipeline._parse_document(mock_doc)
                print("❌ Should have failed for non-existent file")
            except Exception as e:
                if "not found" in str(e).lower():
                    print("✅ Correctly handled non-existent file")
                else:
                    print(f"⚠️  Unexpected error: {e}")
                    
        except Exception as e:
            print(f"⚠️  Error handling test failed: {e}")
        
        print("✅ Processing pipeline integration test completed")
        
    except Exception as e:
        print(f"❌ Processing pipeline integration failed: {e}")
        logger.exception("Pipeline integration error")

if __name__ == "__main__":
    asyncio.run(test_real_documents())
    asyncio.run(test_processing_pipeline_integration())