"""Document parser framework for extracting content from various document formats."""

from .base import BaseParser, ParsedContent, TextBlock, ImageData
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .markdown_parser import MarkdownParser
from .factory import (
    ParserFactory, 
    get_parser, 
    get_parser_for_file, 
    is_file_supported, 
    get_supported_extensions
)

__all__ = [
    "BaseParser",
    "ParsedContent", 
    "TextBlock",
    "ImageData",
    "PDFParser",
    "DocxParser", 
    "MarkdownParser",
    "ParserFactory",
    "get_parser",
    "get_parser_for_file",
    "is_file_supported", 
    "get_supported_extensions",
]