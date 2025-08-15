"""Parser factory and registration system."""

from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseParser
from .docx_parser import DocxParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PDFParser


class ParserFactory:
    """Factory for creating and managing document parsers."""
    
    def __init__(self):
        """Initialize parser factory with default parsers."""
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._instances: Dict[str, BaseParser] = {}
        
        # Register default parsers
        self.register_parser("pdf", PDFParser)
        self.register_parser("docx", DocxParser)
        self.register_parser("markdown", MarkdownParser)
    
    def register_parser(self, name: str, parser_class: Type[BaseParser]) -> None:
        """
        Register a parser class with the factory.
        
        Args:
            name: Unique name for the parser
            parser_class: Parser class to register
            
        Raises:
            ValueError: If parser class is not a subclass of BaseParser
        """
        if not issubclass(parser_class, BaseParser):
            raise ValueError(f"Parser class must be a subclass of BaseParser")
        
        self._parsers[name] = parser_class
        # Clear cached instance if it exists
        if name in self._instances:
            del self._instances[name]
    
    def unregister_parser(self, name: str) -> None:
        """
        Unregister a parser from the factory.
        
        Args:
            name: Name of the parser to unregister
        """
        if name in self._parsers:
            del self._parsers[name]
        if name in self._instances:
            del self._instances[name]
    
    def get_parser(self, name: str) -> Optional[BaseParser]:
        """
        Get a parser instance by name.
        
        Args:
            name: Name of the parser
            
        Returns:
            Parser instance or None if not found
        """
        if name not in self._parsers:
            return None
        
        # Return cached instance or create new one
        if name not in self._instances:
            self._instances[name] = self._parsers[name]()
        
        return self._instances[name]
    
    def get_parser_for_file(self, file_path: Path) -> Optional[BaseParser]:
        """
        Get the appropriate parser for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance that supports the file, or None if no parser found
        """
        for parser_name, parser_class in self._parsers.items():
            parser = self.get_parser(parser_name)
            if parser and parser.supports_file(file_path):
                return parser
        
        return None
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported file extensions (including the dot)
        """
        extensions = []
        for parser_name in self._parsers:
            parser = self.get_parser(parser_name)
            if parser:
                extensions.extend(parser.supported_extensions)
        
        return sorted(list(set(extensions)))
    
    def list_parsers(self) -> List[str]:
        """
        Get list of registered parser names.
        
        Returns:
            List of parser names
        """
        return list(self._parsers.keys())
    
    def is_file_supported(self, file_path: Path) -> bool:
        """
        Check if a file is supported by any registered parser.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is supported, False otherwise
        """
        return self.get_parser_for_file(file_path) is not None


# Global parser factory instance
_parser_factory = ParserFactory()


def get_parser_factory() -> ParserFactory:
    """
    Get the global parser factory instance.
    
    Returns:
        Global ParserFactory instance
    """
    return _parser_factory


def get_parser(name: str) -> Optional[BaseParser]:
    """
    Get a parser instance by name using the global factory.
    
    Args:
        name: Name of the parser
        
    Returns:
        Parser instance or None if not found
    """
    return _parser_factory.get_parser(name)


def get_parser_for_file(file_path: Path) -> Optional[BaseParser]:
    """
    Get the appropriate parser for a file using the global factory.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Parser instance that supports the file, or None if no parser found
    """
    return _parser_factory.get_parser_for_file(file_path)


def is_file_supported(file_path: Path) -> bool:
    """
    Check if a file is supported by any registered parser.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is supported, False otherwise
    """
    return _parser_factory.is_file_supported(file_path)


def get_supported_extensions() -> List[str]:
    """
    Get list of all supported file extensions.
    
    Returns:
        List of supported file extensions (including the dot)
    """
    return _parser_factory.get_supported_extensions()