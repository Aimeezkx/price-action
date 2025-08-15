"""Integration test for parser framework with sample files."""

import asyncio
import tempfile
from pathlib import Path

from app.parsers import get_parser_for_file, get_supported_extensions


async def test_markdown_parser():
    """Test markdown parser with sample content."""
    print("Testing Markdown Parser...")
    
    sample_markdown = """---
title: Sample Document
author: Test Author
---

# Introduction

This is a sample markdown document for testing the parser.

## Features

The parser should extract:

- Headers and structure
- Text content
- Images (if any)
- Metadata from front matter

### Code Example

```python
def hello_world():
    print("Hello, World!")
```

## Images

![Sample Image](sample.png)

## Conclusion

This concludes our test document.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_markdown)
        temp_path = Path(f.name)
    
    try:
        parser = get_parser_for_file(temp_path)
        if parser:
            print(f"Found parser: {parser.name}")
            
            result = await parser.parse(temp_path)
            
            print(f"Extracted {len(result.text_blocks)} text blocks")
            print(f"Extracted {len(result.images)} images")
            print(f"Metadata: {result.metadata}")
            
            # Print first few text blocks
            for i, block in enumerate(result.text_blocks[:3]):
                print(f"Block {i+1}: {block.text[:100]}...")
                print(f"  Type: {block.font_info.get('type', 'unknown')}")
                print(f"  Level: {block.font_info.get('level', 0)}")
        else:
            print("No parser found for markdown file")
    
    finally:
        temp_path.unlink()


async def test_parser_factory():
    """Test parser factory functionality."""
    print("\nTesting Parser Factory...")
    
    extensions = get_supported_extensions()
    print(f"Supported extensions: {extensions}")
    
    # Test file type detection
    test_files = [
        "document.pdf",
        "document.docx", 
        "document.md",
        "document.txt",  # Unsupported
    ]
    
    for filename in test_files:
        file_path = Path(filename)
        parser = get_parser_for_file(file_path)
        
        if parser:
            print(f"{filename}: {parser.name}")
        else:
            print(f"{filename}: No parser available")


async def main():
    """Run integration tests."""
    print("Parser Framework Integration Test")
    print("=" * 40)
    
    await test_markdown_parser()
    await test_parser_factory()
    
    print("\nIntegration test completed!")


if __name__ == "__main__":
    asyncio.run(main())