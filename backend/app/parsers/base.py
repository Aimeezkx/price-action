"""Base parser interface and data structures for document parsing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TextBlock:
    """Represents a block of text with position and formatting information."""
    
    text: str
    page: int
    bbox: Dict[str, float]  # {x, y, width, height}
    font_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate bbox structure."""
        required_keys = {"x", "y", "width", "height"}
        if not all(key in self.bbox for key in required_keys):
            raise ValueError(f"bbox must contain keys: {required_keys}")


@dataclass
class ImageData:
    """Represents an extracted image with metadata."""
    
    image_path: str
    page: int
    bbox: Dict[str, float]  # {x, y, width, height}
    format: str
    original_size: Optional[Dict[str, int]] = None  # {width, height}
    
    def __post_init__(self):
        """Validate bbox structure."""
        required_keys = {"x", "y", "width", "height"}
        if not all(key in self.bbox for key in required_keys):
            raise ValueError(f"bbox must contain keys: {required_keys}")


@dataclass
class ParsedContent:
    """Container for all content extracted from a document."""
    
    text_blocks: List[TextBlock]
    images: List[ImageData]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Initialize empty lists if None provided."""
        if self.text_blocks is None:
            self.text_blocks = []
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    def __init__(self):
        """Initialize parser with default settings."""
        self.supported_extensions: List[str] = []
        self.name: str = self.__class__.__name__
    
    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse a document and extract content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ParsedContent containing extracted text blocks, images, and metadata
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
            Exception: For parsing errors
        """
        pass
    
    def supports_file(self, file_path: Path) -> bool:
        """
        Check if this parser supports the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is supported, False otherwise
        """
        return file_path.suffix.lower() in self.supported_extensions
    
    def validate_file(self, file_path: Path) -> None:
        """
        Validate that the file exists and is supported.
        
        Args:
            file_path: Path to the file to validate
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.supports_file(file_path):
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. "
                f"Supported formats: {self.supported_extensions}"
            )
    
    def _extract_text_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract basic metadata from text content.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary containing text metadata
        """
        return {
            "character_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.splitlines()),
        }