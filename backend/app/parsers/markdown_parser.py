"""Markdown parser implementation using python-markdown."""

import asyncio
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import markdown
from markdown.extensions import codehilite, tables, toc

from .base import BaseParser, ImageData, ParsedContent, TextBlock


class MarkdownParser(BaseParser):
    """Parser for Markdown documents."""
    
    def __init__(self):
        """Initialize Markdown parser."""
        super().__init__()
        self.supported_extensions = [".md", ".markdown", ".mdown", ".mkd"]
        self.name = "MarkdownParser"
        
        # Initialize markdown processor with extensions
        self.md = markdown.Markdown(
            extensions=[
                "toc",
                "tables", 
                "codehilite",
                "fenced_code",
                "attr_list",
            ]
        )
    
    async def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse a Markdown document and extract content.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            ParsedContent containing extracted text blocks, images, and metadata
        """
        self.validate_file(file_path)
        
        # Run parsing in thread pool to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(
            None, self._parse_sync, file_path
        )
    
    def _parse_sync(self, file_path: Path) -> ParsedContent:
        """Synchronous Markdown parsing implementation."""
        text_blocks: List[TextBlock] = []
        images: List[ImageData] = []
        metadata: Dict[str, Any] = {}
        
        try:
            # Read markdown content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract metadata from front matter if present
            content, front_matter = self._extract_front_matter(content)
            metadata.update(front_matter)
            
            # Parse markdown structure
            sections = self._parse_sections(content)
            
            # Extract text blocks from sections
            y_position = 0
            for section in sections:
                text_block = self._create_text_block(section, y_position)
                text_blocks.append(text_block)
                y_position += text_block.bbox["height"] + 10
            
            # Extract images
            images = self._extract_images(content, file_path)
            
            # Add document metadata
            metadata.update(self._extract_document_metadata(content, file_path))
            
        except Exception as e:
            raise Exception(f"Failed to parse Markdown {file_path}: {str(e)}") from e
        
        return ParsedContent(
            text_blocks=text_blocks,
            images=images,
            metadata=metadata
        )
    
    def _extract_front_matter(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """Extract YAML front matter from markdown content."""
        front_matter = {}
        
        # Check for YAML front matter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    front_matter = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                except ImportError:
                    # If PyYAML not available, parse basic key-value pairs
                    for line in parts[1].strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            front_matter[key.strip()] = value.strip()
                    content = parts[2].strip()
                except Exception:
                    # Skip front matter if parsing fails
                    pass
        
        return content, front_matter
    
    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into logical sections."""
        sections = []
        
        # Split content by headers
        lines = content.split("\n")
        current_section = {"type": "text", "content": "", "level": 0}
        
        for line in lines:
            # Check for headers
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = {
                    "type": "header",
                    "content": title,
                    "level": level,
                    "markdown_line": line,
                }
                sections.append(current_section)
                
                # Start new text section
                current_section = {"type": "text", "content": "", "level": level}
            
            # Check for code blocks
            elif line.strip().startswith("```"):
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Find end of code block
                code_content = [line]
                current_section = {"type": "code", "content": line + "\n", "level": 0}
            
            # Check for lists
            elif re.match(r"^\s*[-*+]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                if current_section["type"] != "list":
                    if current_section["content"].strip():
                        sections.append(current_section)
                    current_section = {"type": "list", "content": "", "level": 0}
                current_section["content"] += line + "\n"
            
            # Regular text
            else:
                current_section["content"] += line + "\n"
        
        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _create_text_block(
        self, section: Dict[str, Any], y_position: float
    ) -> TextBlock:
        """Create a text block from a markdown section."""
        content = section["content"].strip()
        section_type = section["type"]
        level = section.get("level", 0)
        
        # Estimate dimensions based on content
        lines = content.split("\n")
        line_count = len(lines)
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        # Estimate width and height
        estimated_width = min(max_line_length * 8, 600)
        estimated_height = line_count * 20
        
        # Adjust for section type
        if section_type == "header":
            estimated_height = 30 + (6 - level) * 5  # Larger headers
            font_size = 24 - (level * 2)
        elif section_type == "code":
            estimated_height = line_count * 16  # Smaller line height for code
            font_size = 12
        else:
            font_size = 14
        
        font_info = {
            "type": section_type,
            "level": level,
            "size": font_size,
            "monospace": section_type == "code",
        }
        
        return TextBlock(
            text=content,
            page=1,  # Markdown is single "page"
            bbox={
                "x": 0,
                "y": y_position,
                "width": estimated_width,
                "height": estimated_height,
            },
            font_info=font_info,
        )
    
    def _extract_images(self, content: str, file_path: Path) -> List[ImageData]:
        """Extract images from markdown content."""
        images: List[ImageData] = []
        
        # Find image references in markdown
        image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        matches = re.finditer(image_pattern, content)
        
        image_index = 0
        y_position = 0
        
        for match in matches:
            alt_text = match.group(1)
            image_url = match.group(2)
            
            try:
                # Handle different image sources
                image_path = self._resolve_image_path(image_url, file_path)
                
                if image_path and Path(image_path).exists():
                    # Copy image to temporary location for consistency
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(image_path).suffix,
                        delete=False,
                        prefix=f"{file_path.stem}_img{image_index}_"
                    ) as temp_file:
                        shutil.copy2(image_path, temp_file.name)
                        temp_image_path = temp_file.name
                    
                    # Determine format
                    format_ext = Path(image_path).suffix.upper().lstrip(".")
                    if not format_ext:
                        format_ext = "PNG"
                    
                    image_data = ImageData(
                        image_path=temp_image_path,
                        page=1,
                        bbox={
                            "x": 0,
                            "y": y_position,
                            "width": 400,  # Default width
                            "height": 300,  # Default height
                        },
                        format=format_ext,
                    )
                    images.append(image_data)
                    image_index += 1
                    y_position += 320  # Space between images
            
            except Exception as e:
                # Skip problematic images
                continue
        
        return images
    
    def _resolve_image_path(self, image_url: str, markdown_file: Path) -> Optional[str]:
        """Resolve image path from markdown reference."""
        # Parse URL to check if it's local or remote
        parsed = urlparse(image_url)
        
        if parsed.scheme in ("http", "https"):
            # Remote image - would need to download
            # For now, skip remote images
            return None
        
        # Local image path
        if Path(image_url).is_absolute():
            return image_url
        else:
            # Relative to markdown file
            base_dir = markdown_file.parent
            resolved_path = base_dir / image_url
            return str(resolved_path) if resolved_path.exists() else None
    
    def _extract_document_metadata(
        self, content: str, file_path: Path
    ) -> Dict[str, Any]:
        """Extract metadata from markdown content."""
        # Count various elements
        header_count = len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE))
        image_count = len(re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", content))
        link_count = len(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content))
        code_block_count = len(re.findall(r"```", content)) // 2
        
        return {
            "format": "Markdown",
            "page_count": 1,
            "header_count": header_count,
            "image_count": image_count,
            "link_count": link_count,
            "code_block_count": code_block_count,
            **self._extract_text_metadata(content),
        }