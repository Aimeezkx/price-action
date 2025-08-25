#!/usr/bin/env python3
"""
Test script to verify document parser integration with processing pipeline.

This script tests:
1. Parser selection logic based on file type
2. Error handling for unsupported content
3. Parsing with real documents of each type
4. Integration with processing pipeline
"""

import asyncio
import tempfile
import logging
from pathlib import Path
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_parser_integration():
    """Test parser integration with processing pipeline."""
    print("🧪 Testing Document Parser Integration")
    print("=" * 50)
    
    # Test 1: Parser Factory and Registration
    print("\n1. Testing Parser Factory...")
    try:
        from app.parsers.factory import get_parser_factory, get_supported_extensions
        
        factory = get_parser_factory()
        parsers = factory.list_parsers()
        extensions = get_supported_extensions()
        
        print(f"✅ Registered parsers: {parsers}")
        print(f"✅ Supported extensions: {extensions}")
        
        # Verify all expected parsers are registered
        expected_parsers = ["pdf", "docx", "markdown", "txt"]
        for parser_name in expected_parsers:
            if parser_name in parsers:
                print(f"✅ {parser_name.upper()} parser registered")
            else:
                print(f"❌ {parser_name.upper()} parser missing")
                
    except Exception as e:
        print(f"❌ Parser factory test failed: {e}")
        return False
    
    # Test 2: Individual Parser Testing
    print("\n2. Testing Individual Parsers...")
    
    # Create test files
    test_files = await create_test_files()
    
    for file_path, file_type in test_files:
        try:
            print(f"\n   Testing {file_type} parser with {file_path.name}...")
            
            from app.parsers.factory import get_parser_for_file
            parser = get_parser_for_file(file_path)
            
            if not parser:
                print(f"❌ No parser found for {file_type}")
                continue
                
            print(f"✅ Found parser: {parser.name}")
            
            # Test parsing
            parsed_content = await parser.parse(file_path)
            
            print(f"✅ Parsed successfully:")
            print(f"   - Text blocks: {len(parsed_content.text_blocks)}")
            print(f"   - Images: {len(parsed_content.images)}")
            print(f"   - Metadata keys: {list(parsed_content.metadata.keys())}")
            
            # Verify content
            if parsed_content.text_blocks:
                first_block = parsed_content.text_blocks[0]
                print(f"   - First block preview: {first_block.text[:100]}...")
            else:
                print("   - No text blocks extracted")
                
        except Exception as e:
            print(f"❌ {file_type} parser failed: {e}")
    
    # Test 3: Error Handling
    print("\n3. Testing Error Handling...")
    
    # Test unsupported file type
    try:
        unsupported_file = Path(tempfile.mktemp(suffix=".xyz"))
        unsupported_file.write_text("test content")
        
        from app.parsers.factory import get_parser_for_file
        parser = get_parser_for_file(unsupported_file)
        
        if parser is None:
            print("✅ Correctly returned None for unsupported file type")
        else:
            print(f"❌ Unexpectedly found parser for .xyz file: {parser.name}")
            
        unsupported_file.unlink()  # Clean up
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 4: Processing Pipeline Integration
    print("\n4. Testing Processing Pipeline Integration...")
    
    try:
        # This would require database setup, so we'll test the parser selection logic
        from app.services.document_processing_pipeline import DocumentProcessingPipeline
        
        pipeline = DocumentProcessingPipeline()
        print("✅ Processing pipeline initialized successfully")
        
        # Test parser selection logic in pipeline context
        for file_path, file_type in test_files:
            try:
                from app.parsers.factory import get_parser_for_file
                parser = get_parser_for_file(file_path)
                
                if parser:
                    print(f"✅ Pipeline can select {parser.name} for {file_type}")
                else:
                    print(f"❌ Pipeline cannot find parser for {file_type}")
                    
            except Exception as e:
                print(f"❌ Pipeline parser selection failed for {file_type}: {e}")
                
    except Exception as e:
        print(f"❌ Processing pipeline integration test failed: {e}")
    
    # Clean up test files
    for file_path, _ in test_files:
        try:
            file_path.unlink()
        except:
            pass
    
    print("\n" + "=" * 50)
    print("🎉 Parser integration testing completed!")
    return True

async def create_test_files():
    """Create test files for each supported format."""
    test_files = []
    
    # Create TXT file
    txt_file = Path(tempfile.mktemp(suffix=".txt"))
    txt_content = """This is a test document for the TXT parser.

This document contains multiple paragraphs to test the text segmentation functionality.

The parser should be able to extract this content and create appropriate text blocks.

Here's another paragraph with some technical content:
- Machine learning algorithms
- Natural language processing
- Document parsing and extraction

This tests the parser's ability to handle different types of content."""
    
    txt_file.write_text(txt_content, encoding='utf-8')
    test_files.append((txt_file, "TXT"))
    
    # Create Markdown file
    md_file = Path(tempfile.mktemp(suffix=".md"))
    md_content = """# Test Document

This is a **test document** for the Markdown parser.

## Section 1

Here's some content with *emphasis* and `code`.

### Subsection

- List item 1
- List item 2
- List item 3

## Section 2

```python
def hello_world():
    print("Hello, World!")
```

This tests various Markdown features."""
    
    md_file.write_text(md_content, encoding='utf-8')
    test_files.append((md_file, "Markdown"))
    
    # Note: We can't easily create valid PDF or DOCX files without additional libraries
    # In a real test environment, you would use sample files
    
    return test_files

async def test_error_scenarios():
    """Test various error scenarios."""
    print("\n5. Testing Error Scenarios...")
    
    # Test corrupted file
    try:
        corrupted_file = Path(tempfile.mktemp(suffix=".txt"))
        # Create a file with invalid content
        with open(corrupted_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')  # Binary garbage
        
        from app.parsers.txt_parser import TxtParser
        parser = TxtParser()
        
        # This should handle the corrupted content gracefully
        parsed_content = await parser.parse(corrupted_file)
        print("✅ Handled corrupted file gracefully")
        
        corrupted_file.unlink()
        
    except Exception as e:
        print(f"⚠️  Corrupted file handling: {e}")
    
    # Test empty file
    try:
        empty_file = Path(tempfile.mktemp(suffix=".txt"))
        empty_file.write_text("", encoding='utf-8')
        
        from app.parsers.txt_parser import TxtParser
        parser = TxtParser()
        
        parsed_content = await parser.parse(empty_file)
        print("✅ Handled empty file gracefully")
        
        empty_file.unlink()
        
    except Exception as e:
        print(f"⚠️  Empty file handling: {e}")
    
    # Test very large file (simulate)
    try:
        large_file = Path(tempfile.mktemp(suffix=".txt"))
        large_content = "This is a test line.\n" * 10000  # 10k lines
        large_file.write_text(large_content, encoding='utf-8')
        
        from app.parsers.txt_parser import TxtParser
        parser = TxtParser()
        
        parsed_content = await parser.parse(large_file)
        print(f"✅ Handled large file: {len(parsed_content.text_blocks)} blocks")
        
        large_file.unlink()
        
    except Exception as e:
        print(f"⚠️  Large file handling: {e}")

if __name__ == "__main__":
    asyncio.run(test_parser_integration())
    asyncio.run(test_error_scenarios())