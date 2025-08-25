"""Plain text parser implementation."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseParser, ImageData, ParsedContent, TextBlock


class TxtParser(BaseParser):
    """Parser for plain text documents."""
    
    def __init__(self):
        """Initialize TXT parser."""
        super().__init__()
        self.supported_extensions = [".txt", ".text"]
        self.name = "TxtParser"
    
    async def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse a plain text document and extract content.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            ParsedContent containing extracted text blocks and metadata
        """
        self.validate_file(file_path)
        
        # Run parsing in thread pool to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(
            None, self._parse_sync, file_path
        )
    
    def _parse_sync(self, file_path: Path) -> ParsedContent:
        """Synchronous text parsing implementation."""
        text_blocks: List[TextBlock] = []
        images: List[ImageData] = []  # Plain text has no images
        metadata: Dict[str, Any] = {}
        
        try:
            # Read text content with encoding detection
            content = self._read_text_file(file_path)
            
            # Split content into logical blocks (paragraphs)
            paragraphs = self._split_into_paragraphs(content)
            
            # Create text blocks from paragraphs
            y_position = 0
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():  # Skip empty paragraphs
                    text_block = self._create_text_block(paragraph, i + 1, y_position)
                    text_blocks.append(text_block)
                    y_position += text_block.bbox["height"] + 10
            
            # Extract document metadata
            metadata = self._extract_document_metadata(content, file_path)
            
        except Exception as e:
            raise Exception(f"Failed to parse text file {file_path}: {str(e)}") from e
        
        return ParsedContent(
            text_blocks=text_blocks,
            images=images,
            metadata=metadata
        )
    
    def _read_text_file(self, file_path: Path) -> str:
        """Read text file with encoding detection."""
        # Try common encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, read as binary and decode with errors='replace'
        with open(file_path, 'rb') as f:
            content = f.read()
            return content.decode('utf-8', errors='replace')
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split text content into logical paragraphs."""
        # Split by double newlines (paragraph breaks)
        paragraphs = content.split('\n\n')
        
        # If no paragraph breaks found, split by single newlines
        if len(paragraphs) == 1:
            paragraphs = content.split('\n')
        
        # Filter out very short paragraphs and clean up
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            cleaned = paragraph.strip()
            if len(cleaned) > 10:  # Only keep paragraphs with substantial content
                cleaned_paragraphs.append(cleaned)
        
        # If we have too few paragraphs, try to split long ones
        if len(cleaned_paragraphs) < 3:
            final_paragraphs = []
            for paragraph in cleaned_paragraphs:
                if len(paragraph) > 500:  # Split very long paragraphs
                    # Split by sentences (rough approximation)
                    sentences = paragraph.replace('. ', '.\n').split('\n')
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk + sentence) > 300:
                            if current_chunk:
                                final_paragraphs.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            current_chunk += " " + sentence if current_chunk else sentence
                    if current_chunk:
                        final_paragraphs.append(current_chunk.strip())
                else:
                    final_paragraphs.append(paragraph)
            return final_paragraphs
        
        return cleaned_paragraphs
    
    def _create_text_block(self, text: str, block_number: int, y_position: float) -> TextBlock:
        """Create a text block from a paragraph."""
        # Estimate dimensions based on content
        lines = text.split('\n')
        line_count = max(len(lines), 1)
        max_line_length = max(len(line) for line in lines) if lines else len(text)
        
        # Estimate width and height (rough approximation)
        estimated_width = min(max_line_length * 8, 600)  # ~8 pixels per character
        estimated_height = line_count * 20  # ~20 pixels per line
        
        # Minimum dimensions
        estimated_width = max(estimated_width, 100)
        estimated_height = max(estimated_height, 20)
        
        font_info = {
            "type": "paragraph",
            "size": 12,
            "font": "monospace",  # Plain text is typically monospace
            "block_number": block_number,
        }
        
        return TextBlock(
            text=text,
            page=1,  # Plain text is treated as single page
            bbox={
                "x": 0,
                "y": y_position,
                "width": estimated_width,
                "height": estimated_height,
            },
            font_info=font_info,
        )
    
    def _extract_document_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from text content."""
        lines = content.split('\n')
        
        # Basic text statistics
        metadata = {
            "format": "Plain Text",
            "page_count": 1,
            "line_count": len(lines),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "encoding": "UTF-8",  # Simplified - we normalized to UTF-8
            **self._extract_text_metadata(content),
        }
        
        # Try to detect if this might be a structured text file
        if any(line.strip().startswith('#') for line in lines[:10]):
            metadata["possible_format"] = "Markdown-like"
        elif any(line.strip().startswith('*') or line.strip().startswith('-') for line in lines[:10]):
            metadata["possible_format"] = "List-like"
        elif content.count('\t') > len(lines) * 0.5:
            metadata["possible_format"] = "Tab-separated"
        
        return metadata