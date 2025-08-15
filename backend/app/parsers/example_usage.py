"""Example usage of the document parser framework."""

import asyncio
from pathlib import Path

from .factory import get_parser_for_file, get_supported_extensions, is_file_supported


async def parse_document(file_path: Path) -> None:
    """
    Example function showing how to parse a document.
    
    Args:
        file_path: Path to the document to parse
    """
    print(f"Attempting to parse: {file_path}")
    
    # Check if file is supported
    if not is_file_supported(file_path):
        print(f"File type not supported: {file_path.suffix}")
        print(f"Supported extensions: {get_supported_extensions()}")
        return
    
    # Get appropriate parser
    parser = get_parser_for_file(file_path)
    if not parser:
        print("No parser available for this file")
        return
    
    print(f"Using parser: {parser.name}")
    
    try:
        # Parse the document
        result = await parser.parse(file_path)
        
        # Display results
        print(f"\nParsing Results:")
        print(f"- Text blocks: {len(result.text_blocks)}")
        print(f"- Images: {len(result.images)}")
        print(f"- Metadata: {result.metadata}")
        
        # Show first few text blocks
        print(f"\nFirst few text blocks:")
        for i, block in enumerate(result.text_blocks[:3]):
            print(f"Block {i+1} (page {block.page}):")
            print(f"  Text: {block.text[:100]}...")
            print(f"  Position: {block.bbox}")
            if block.font_info:
                print(f"  Font info: {block.font_info}")
        
        # Show images if any
        if result.images:
            print(f"\nImages found:")
            for i, image in enumerate(result.images):
                print(f"Image {i+1}:")
                print(f"  Path: {image.image_path}")
                print(f"  Page: {image.page}")
                print(f"  Format: {image.format}")
                print(f"  Position: {image.bbox}")
    
    except Exception as e:
        print(f"Error parsing document: {e}")


async def main():
    """Example main function."""
    print("Document Parser Framework Example")
    print("=" * 40)
    
    # Show supported extensions
    print(f"Supported file extensions: {get_supported_extensions()}")
    
    # Example usage with different file types
    example_files = [
        "sample.pdf",
        "document.docx", 
        "readme.md",
        "unsupported.txt",
    ]
    
    for filename in example_files:
        file_path = Path(filename)
        print(f"\n{'-' * 40}")
        await parse_document(file_path)


if __name__ == "__main__":
    asyncio.run(main())