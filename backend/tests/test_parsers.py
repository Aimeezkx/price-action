"""Tests for document parser framework."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.parsers import (
    BaseParser,
    DocxParser,
    ImageData,
    MarkdownParser,
    PDFParser,
    ParsedContent,
    ParserFactory,
    TextBlock,
    get_parser,
    get_parser_for_file,
    get_supported_extensions,
    is_file_supported,
)


class TestBaseParser:
    """Test BaseParser abstract class."""
    
    def test_text_block_creation(self):
        """Test TextBlock creation and validation."""
        text_block = TextBlock(
            text="Sample text",
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20},
        )
        
        assert text_block.text == "Sample text"
        assert text_block.page == 1
        assert text_block.bbox["width"] == 100
    
    def test_text_block_invalid_bbox(self):
        """Test TextBlock with invalid bbox."""
        with pytest.raises(ValueError, match="bbox must contain keys"):
            TextBlock(
                text="Sample text",
                page=1,
                bbox={"x": 0, "y": 0},  # Missing width and height
            )
    
    def test_image_data_creation(self):
        """Test ImageData creation and validation."""
        image_data = ImageData(
            image_path="/path/to/image.png",
            page=1,
            bbox={"x": 0, "y": 0, "width": 200, "height": 150},
            format="PNG",
        )
        
        assert image_data.image_path == "/path/to/image.png"
        assert image_data.format == "PNG"
    
    def test_parsed_content_creation(self):
        """Test ParsedContent creation."""
        text_block = TextBlock(
            text="Sample text",
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20},
        )
        
        content = ParsedContent(
            text_blocks=[text_block],
            images=[],
            metadata={"format": "test"},
        )
        
        assert len(content.text_blocks) == 1
        assert len(content.images) == 0
        assert content.metadata["format"] == "test"


class MockParser(BaseParser):
    """Mock parser for testing."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = [".mock"]
        self.name = "MockParser"
    
    async def parse(self, file_path: Path) -> ParsedContent:
        """Mock parse implementation."""
        return ParsedContent(
            text_blocks=[
                TextBlock(
                    text="Mock content",
                    page=1,
                    bbox={"x": 0, "y": 0, "width": 100, "height": 20},
                )
            ],
            images=[],
            metadata={"format": "mock"},
        )


class TestParserFactory:
    """Test ParserFactory functionality."""
    
    def test_factory_initialization(self):
        """Test factory initializes with default parsers."""
        factory = ParserFactory()
        
        parsers = factory.list_parsers()
        assert "pdf" in parsers
        assert "docx" in parsers
        assert "markdown" in parsers
    
    def test_register_custom_parser(self):
        """Test registering a custom parser."""
        factory = ParserFactory()
        factory.register_parser("mock", MockParser)
        
        parser = factory.get_parser("mock")
        assert parser is not None
        assert isinstance(parser, MockParser)
    
    def test_register_invalid_parser(self):
        """Test registering invalid parser class."""
        factory = ParserFactory()
        
        with pytest.raises(ValueError, match="must be a subclass of BaseParser"):
            factory.register_parser("invalid", str)
    
    def test_unregister_parser(self):
        """Test unregistering a parser."""
        factory = ParserFactory()
        factory.register_parser("mock", MockParser)
        
        assert factory.get_parser("mock") is not None
        
        factory.unregister_parser("mock")
        assert factory.get_parser("mock") is None
    
    def test_get_parser_for_file(self):
        """Test getting parser for specific file."""
        factory = ParserFactory()
        
        pdf_file = Path("test.pdf")
        parser = factory.get_parser_for_file(pdf_file)
        assert isinstance(parser, PDFParser)
        
        docx_file = Path("test.docx")
        parser = factory.get_parser_for_file(docx_file)
        assert isinstance(parser, DocxParser)
        
        md_file = Path("test.md")
        parser = factory.get_parser_for_file(md_file)
        assert isinstance(parser, MarkdownParser)
        
        unsupported_file = Path("test.xyz")
        parser = factory.get_parser_for_file(unsupported_file)
        assert parser is None
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        factory = ParserFactory()
        extensions = factory.get_supported_extensions()
        
        assert ".pdf" in extensions
        assert ".docx" in extensions
        assert ".md" in extensions
        assert ".markdown" in extensions
    
    def test_is_file_supported(self):
        """Test checking if file is supported."""
        factory = ParserFactory()
        
        assert factory.is_file_supported(Path("test.pdf"))
        assert factory.is_file_supported(Path("test.docx"))
        assert factory.is_file_supported(Path("test.md"))
        assert not factory.is_file_supported(Path("test.xyz"))


class TestGlobalFunctions:
    """Test global parser functions."""
    
    def test_get_parser(self):
        """Test global get_parser function."""
        parser = get_parser("pdf")
        assert isinstance(parser, PDFParser)
        
        parser = get_parser("nonexistent")
        assert parser is None
    
    def test_get_parser_for_file(self):
        """Test global get_parser_for_file function."""
        parser = get_parser_for_file(Path("test.pdf"))
        assert isinstance(parser, PDFParser)
    
    def test_is_file_supported(self):
        """Test global is_file_supported function."""
        assert is_file_supported(Path("test.pdf"))
        assert not is_file_supported(Path("test.xyz"))
    
    def test_get_supported_extensions(self):
        """Test global get_supported_extensions function."""
        extensions = get_supported_extensions()
        assert ".pdf" in extensions


class TestPDFParser:
    """Test PDFParser functionality."""
    
    def test_pdf_parser_initialization(self):
        """Test PDF parser initialization."""
        parser = PDFParser()
        assert parser.name == "PDFParser"
        assert ".pdf" in parser.supported_extensions
    
    def test_supports_file(self):
        """Test PDF parser file support."""
        parser = PDFParser()
        assert parser.supports_file(Path("test.pdf"))
        assert not parser.supports_file(Path("test.docx"))
    
    def test_validate_file_not_found(self):
        """Test validation with non-existent file."""
        parser = PDFParser()
        
        with pytest.raises(FileNotFoundError):
            parser.validate_file(Path("nonexistent.pdf"))
    
    def test_validate_unsupported_file(self):
        """Test validation with unsupported file."""
        parser = PDFParser()
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
            with pytest.raises(ValueError, match="Unsupported file format"):
                parser.validate_file(Path(temp_file.name))


class TestDocxParser:
    """Test DocxParser functionality."""
    
    def test_docx_parser_initialization(self):
        """Test DOCX parser initialization."""
        parser = DocxParser()
        assert parser.name == "DocxParser"
        assert ".docx" in parser.supported_extensions
        assert ".doc" in parser.supported_extensions
    
    def test_supports_file(self):
        """Test DOCX parser file support."""
        parser = DocxParser()
        assert parser.supports_file(Path("test.docx"))
        assert parser.supports_file(Path("test.doc"))
        assert not parser.supports_file(Path("test.pdf"))


class TestMarkdownParser:
    """Test MarkdownParser functionality."""
    
    def test_markdown_parser_initialization(self):
        """Test Markdown parser initialization."""
        parser = MarkdownParser()
        assert parser.name == "MarkdownParser"
        assert ".md" in parser.supported_extensions
        assert ".markdown" in parser.supported_extensions
    
    def test_supports_file(self):
        """Test Markdown parser file support."""
        parser = MarkdownParser()
        assert parser.supports_file(Path("test.md"))
        assert parser.supports_file(Path("test.markdown"))
        assert not parser.supports_file(Path("test.pdf"))
    
    def test_extract_front_matter(self):
        """Test front matter extraction."""
        parser = MarkdownParser()
        
        content_with_front_matter = """---
title: Test Document
author: Test Author
---

# Main Content

This is the main content."""
        
        content, front_matter = parser._extract_front_matter(content_with_front_matter)
        
        assert "title" in front_matter
        assert front_matter["title"] == "Test Document"
        assert content.startswith("# Main Content")
    
    def test_parse_sections(self):
        """Test markdown section parsing."""
        parser = MarkdownParser()
        
        content = """# Header 1

Some text content.

## Header 2

More content with a list:

- Item 1
- Item 2

```python
code block
```

Final paragraph."""
        
        sections = parser._parse_sections(content)
        
        # Should have headers, text, list, and code sections
        assert len(sections) > 0
        
        # Check for different section types
        section_types = [s["type"] for s in sections]
        assert "header" in section_types
        assert "text" in section_types


@pytest.mark.asyncio
class TestAsyncParsing:
    """Test asynchronous parsing functionality."""
    
    async def test_mock_parser_async(self):
        """Test async parsing with mock parser."""
        parser = MockParser()
        
        with tempfile.NamedTemporaryFile(suffix=".mock") as temp_file:
            temp_path = Path(temp_file.name)
            
            # Mock the file existence check
            with patch.object(Path, "exists", return_value=True):
                result = await parser.parse(temp_path)
                
                assert isinstance(result, ParsedContent)
                assert len(result.text_blocks) == 1
                assert result.text_blocks[0].text == "Mock content"