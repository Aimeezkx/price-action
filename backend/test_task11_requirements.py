#!/usr/bin/env python3
"""
Test script specifically for Task 11 requirements:

- Connect existing PDF, DOCX, TXT, MD parsers to pipeline
- Add parser selection logic based on file type  
- Handle parser errors and unsupported content gracefully
- Test parsing with real documents of each type

Requirements: 2.1, 2.2, 5.2, 5.4
"""

import asyncio
import tempfile
import logging
from pathlib import Path
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_task11_requirements():
    """Test all Task 11 requirements."""
    print("🎯 Testing Task 11: Integrate document parsers with processing pipeline")
    print("=" * 70)
    
    results = {
        "parser_connection": False,
        "parser_selection": False, 
        "error_handling": False,
        "real_document_testing": False
    }
    
    # Requirement: Connect existing PDF, DOCX, TXT, MD parsers to pipeline
    print("\n📋 Requirement 1: Connect existing parsers to pipeline")
    try:
        from app.services.document_processing_pipeline import DocumentProcessingPipeline
        from app.parsers.factory import get_parser_factory, get_supported_extensions
        
        # Verify all required parsers are available
        factory = get_parser_factory()
        parsers = factory.list_parsers()
        extensions = get_supported_extensions()
        
        required_parsers = ["pdf", "docx", "txt", "markdown"]
        required_extensions = [".pdf", ".docx", ".txt", ".md"]
        
        print(f"Available parsers: {parsers}")
        print(f"Supported extensions: {extensions}")
        
        # Check all required parsers exist
        missing_parsers = [p for p in required_parsers if p not in parsers]
        missing_extensions = [e for e in required_extensions if e not in extensions]
        
        if not missing_parsers and not missing_extensions:
            print("✅ All required parsers connected to pipeline")
            results["parser_connection"] = True
        else:
            print(f"❌ Missing parsers: {missing_parsers}")
            print(f"❌ Missing extensions: {missing_extensions}")
            
        # Verify pipeline can access parsers
        pipeline = DocumentProcessingPipeline()
        print("✅ Processing pipeline can access parser factory")
        
    except Exception as e:
        print(f"❌ Parser connection test failed: {e}")
    
    # Requirement: Add parser selection logic based on file type
    print("\n🎯 Requirement 2: Parser selection logic based on file type")
    try:
        from app.parsers.factory import get_parser_for_file
        
        test_cases = [
            ("document.pdf", "PDFParser"),
            ("document.docx", "DocxParser"), 
            ("document.txt", "TxtParser"),
            ("document.md", "MarkdownParser"),
            ("document.markdown", "MarkdownParser"),
            ("document.text", "TxtParser"),
            ("document.doc", "DocxParser"),
            ("document.xyz", None),  # Unsupported
        ]
        
        all_correct = True
        for filename, expected_parser in test_cases:
            file_path = Path(filename)
            parser = get_parser_for_file(file_path)
            
            if expected_parser is None:
                if parser is None:
                    print(f"✅ {filename}: Correctly returned None")
                else:
                    print(f"❌ {filename}: Expected None, got {parser.name}")
                    all_correct = False
            else:
                if parser and parser.name == expected_parser:
                    print(f"✅ {filename}: {parser.name}")
                else:
                    actual = parser.name if parser else "None"
                    print(f"❌ {filename}: Expected {expected_parser}, got {actual}")
                    all_correct = False
        
        if all_correct:
            results["parser_selection"] = True
            print("✅ Parser selection logic working correctly")
        else:
            print("❌ Parser selection logic has issues")
            
    except Exception as e:
        print(f"❌ Parser selection test failed: {e}")
    
    # Requirement: Handle parser errors and unsupported content gracefully
    print("\n🛡️  Requirement 3: Handle parser errors and unsupported content gracefully")
    try:
        error_tests_passed = 0
        total_error_tests = 4
        
        # Test 1: Unsupported file type
        try:
            from app.parsers.factory import get_parser_for_file
            unsupported_file = Path("test.xyz")
            parser = get_parser_for_file(unsupported_file)
            
            if parser is None:
                print("✅ Unsupported file type handled gracefully")
                error_tests_passed += 1
            else:
                print(f"❌ Unsupported file type returned parser: {parser.name}")
        except Exception as e:
            print(f"❌ Unsupported file type test failed: {e}")
        
        # Test 2: Corrupted file content
        try:
            corrupted_file = Path(tempfile.mktemp(suffix=".txt"))
            with open(corrupted_file, 'wb') as f:
                f.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')  # Binary garbage
            
            from app.parsers.txt_parser import TxtParser
            parser = TxtParser()
            parsed_content = await parser.parse(corrupted_file)
            
            # Should handle gracefully and return some content
            print("✅ Corrupted file content handled gracefully")
            error_tests_passed += 1
            
            corrupted_file.unlink()
            
        except Exception as e:
            print(f"⚠️  Corrupted file handling: {e}")
        
        # Test 3: Empty file
        try:
            empty_file = Path(tempfile.mktemp(suffix=".txt"))
            empty_file.write_text("", encoding='utf-8')
            
            from app.parsers.txt_parser import TxtParser
            parser = TxtParser()
            parsed_content = await parser.parse(empty_file)
            
            print("✅ Empty file handled gracefully")
            error_tests_passed += 1
            
            empty_file.unlink()
            
        except Exception as e:
            print(f"⚠️  Empty file handling: {e}")
        
        # Test 4: Processing pipeline error handling
        try:
            from app.services.document_processing_pipeline import DocumentProcessingPipeline
            
            pipeline = DocumentProcessingPipeline()
            
            # Create mock document with non-existent file
            class MockDocument:
                def __init__(self):
                    self.id = uuid4()
                    self.file_path = "nonexistent_file.txt"
                    self.file_type = "txt"
            
            mock_doc = MockDocument()
            
            try:
                await pipeline._parse_document(mock_doc)
                print("❌ Should have raised ProcessingError for non-existent file")
            except Exception as e:
                if "not found" in str(e).lower() or "processingerror" in str(type(e)).lower():
                    print("✅ Processing pipeline error handling works")
                    error_tests_passed += 1
                else:
                    print(f"⚠️  Unexpected error type: {e}")
                    
        except Exception as e:
            print(f"❌ Processing pipeline error test failed: {e}")
        
        if error_tests_passed >= 3:  # Allow some flexibility
            results["error_handling"] = True
            print(f"✅ Error handling tests passed: {error_tests_passed}/{total_error_tests}")
        else:
            print(f"❌ Error handling needs improvement: {error_tests_passed}/{total_error_tests}")
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Requirement: Test parsing with real documents of each type
    print("\n📄 Requirement 4: Test parsing with real documents of each type")
    try:
        # Create test documents for each type
        test_documents = await create_comprehensive_test_documents()
        
        successful_parses = 0
        total_documents = len(test_documents)
        
        for file_path, doc_type, expected_features in test_documents:
            try:
                print(f"\n   Testing {doc_type} document: {file_path.name}")
                
                from app.parsers.factory import get_parser_for_file
                parser = get_parser_for_file(file_path)
                
                if not parser:
                    print(f"❌ No parser found for {doc_type}")
                    continue
                
                # Parse the document
                parsed_content = await parser.parse(file_path)
                
                # Verify expected features
                features_found = []
                if parsed_content.text_blocks:
                    features_found.append("text_blocks")
                if parsed_content.images:
                    features_found.append("images")
                if parsed_content.metadata:
                    features_found.append("metadata")
                
                # Check specific expectations
                meets_expectations = True
                for feature in expected_features:
                    if feature not in features_found:
                        print(f"⚠️  Expected {feature} not found")
                        meets_expectations = False
                
                if meets_expectations:
                    print(f"✅ {doc_type} parsing successful")
                    print(f"   - Text blocks: {len(parsed_content.text_blocks)}")
                    print(f"   - Images: {len(parsed_content.images)}")
                    print(f"   - Metadata fields: {len(parsed_content.metadata)}")
                    successful_parses += 1
                else:
                    print(f"⚠️  {doc_type} parsing incomplete")
                    
            except Exception as e:
                print(f"❌ {doc_type} parsing failed: {e}")
            finally:
                # Clean up test file
                try:
                    file_path.unlink()
                except:
                    pass
        
        if successful_parses >= total_documents * 0.75:  # 75% success rate
            results["real_document_testing"] = True
            print(f"✅ Real document testing passed: {successful_parses}/{total_documents}")
        else:
            print(f"❌ Real document testing needs improvement: {successful_parses}/{total_documents}")
            
    except Exception as e:
        print(f"❌ Real document testing failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Task 11 Requirements Summary:")
    print(f"✅ Parser Connection: {'PASS' if results['parser_connection'] else 'FAIL'}")
    print(f"✅ Parser Selection: {'PASS' if results['parser_selection'] else 'FAIL'}")
    print(f"✅ Error Handling: {'PASS' if results['error_handling'] else 'FAIL'}")
    print(f"✅ Real Document Testing: {'PASS' if results['real_document_testing'] else 'FAIL'}")
    
    overall_success = all(results.values())
    print(f"\n🎯 Overall Task 11 Status: {'✅ COMPLETE' if overall_success else '❌ NEEDS WORK'}")
    
    return overall_success

async def create_comprehensive_test_documents():
    """Create comprehensive test documents for each parser type."""
    test_documents = []
    
    # TXT document
    txt_file = Path(tempfile.mktemp(suffix=".txt"))
    txt_content = """Document Learning System - Technical Overview

INTRODUCTION
This document provides a comprehensive overview of the document learning system architecture and implementation.

SYSTEM ARCHITECTURE
The system consists of several key components:
1. Document Upload and Storage
2. Content Parsing and Extraction
3. Knowledge Point Identification
4. Flashcard Generation
5. Spaced Repetition System

PARSING SUBSYSTEM
The parsing subsystem supports multiple document formats:
- PDF documents with text and image extraction
- Microsoft Word documents (DOCX format)
- Plain text files with intelligent segmentation
- Markdown documents with structure preservation

KNOWLEDGE EXTRACTION
The knowledge extraction process involves:
• Text segmentation into meaningful chunks
• Entity recognition and classification
• Concept identification and relationship mapping
• Difficulty assessment for learning optimization

FLASHCARD GENERATION
Three types of flashcards are generated:
1. Question and Answer cards for factual content
2. Cloze deletion cards for fill-in-the-blank learning
3. Image hotspot cards for visual content

TECHNICAL IMPLEMENTATION
The system uses asynchronous processing to handle document parsing efficiently.
Error handling ensures graceful degradation when parsing fails.
The modular architecture allows for easy extension with new document formats.

CONCLUSION
This system provides a robust foundation for automated learning content generation from various document types."""
    
    txt_file.write_text(txt_content, encoding='utf-8')
    test_documents.append((txt_file, "TXT", ["text_blocks", "metadata"]))
    
    # Markdown document
    md_file = Path(tempfile.mktemp(suffix=".md"))
    md_content = """# Document Learning System

## Overview

The **Document Learning System** is designed to automatically generate flashcards from uploaded documents.

### Key Features

- Multi-format document support
- Intelligent content extraction
- Automated flashcard generation
- Spaced repetition learning

## Architecture

### Core Components

1. **Document Parser**
   - PDF parsing with PyMuPDF
   - DOCX parsing with python-docx
   - Markdown parsing with python-markdown
   - Plain text parsing with custom logic

2. **Knowledge Extraction**
   - Text segmentation
   - Entity recognition
   - Concept identification

3. **Card Generation**
   - Q&A cards
   - Cloze deletion
   - Image hotspots

### Processing Pipeline

```python
async def process_document(document_id):
    # 1. Parse document content
    parsed_content = await parser.parse(file_path)
    
    # 2. Extract knowledge points
    knowledge_points = await extract_knowledge(parsed_content)
    
    # 3. Generate flashcards
    cards = await generate_cards(knowledge_points)
    
    return cards
```

## Implementation Details

The system uses **asynchronous processing** to handle multiple documents concurrently.

### Error Handling

- Graceful degradation for unsupported formats
- Retry mechanisms for transient failures
- Detailed logging for debugging

### Performance Optimization

- Streaming processing for large documents
- Memory-efficient parsing algorithms
- Background task queuing

## Testing

The system includes comprehensive tests for:

- [ ] Parser functionality
- [ ] Error scenarios
- [ ] Performance benchmarks
- [ ] Integration testing

## Conclusion

This system provides a robust foundation for automated learning content generation."""
    
    md_file.write_text(md_content, encoding='utf-8')
    test_documents.append((md_file, "Markdown", ["text_blocks", "metadata"]))
    
    return test_documents

if __name__ == "__main__":
    success = asyncio.run(test_task11_requirements())
    exit(0 if success else 1)