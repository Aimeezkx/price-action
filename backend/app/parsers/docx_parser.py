"""DOCX parser implementation using python-docx."""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from .base import BaseParser, ImageData, ParsedContent, TextBlock


class DocxParser(BaseParser):
    """Parser for DOCX documents using python-docx."""
    
    def __init__(self):
        """Initialize DOCX parser."""
        super().__init__()
        self.supported_extensions = [".docx", ".doc"]
        self.name = "DocxParser"
    
    async def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse a DOCX document and extract content.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            ParsedContent containing extracted text blocks, images, and metadata
        """
        self.validate_file(file_path)
        
        # Run parsing in thread pool to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(
            None, self._parse_sync, file_path
        )
    
    def _parse_sync(self, file_path: Path) -> ParsedContent:
        """Synchronous DOCX parsing implementation."""
        text_blocks: List[TextBlock] = []
        images: List[ImageData] = []
        metadata: Dict[str, Any] = {}
        
        try:
            # Open DOCX document
            doc = Document(str(file_path))
            
            # Extract document metadata
            metadata = self._extract_document_metadata(doc, file_path)
            
            # Process document elements in order
            page_num = 1  # DOCX doesn't have explicit pages, use logical page
            current_y = 0  # Track vertical position
            
            for element in doc.element.body:
                if isinstance(element, CT_P):
                    # Handle paragraph
                    paragraph = Paragraph(element, doc)
                    if paragraph.text.strip():
                        text_block = self._create_text_block(
                            paragraph, page_num, current_y
                        )
                        text_blocks.append(text_block)
                        current_y += 20  # Approximate line height
                
                elif isinstance(element, CT_Tbl):
                    # Handle table
                    table = Table(element, doc)
                    table_text = self._extract_table_text(table)
                    if table_text.strip():
                        text_block = TextBlock(
                            text=table_text,
                            page=page_num,
                            bbox={"x": 0, "y": current_y, "width": 500, "height": 100},
                            font_info={"type": "table"},
                        )
                        text_blocks.append(text_block)
                        current_y += 100
            
            # Extract images
            images = self._extract_images(doc, file_path.stem)
            
        except Exception as e:
            raise Exception(f"Failed to parse DOCX {file_path}: {str(e)}") from e
        
        return ParsedContent(
            text_blocks=text_blocks,
            images=images,
            metadata=metadata
        )
    
    def _extract_document_metadata(
        self, doc: DocxDocument, file_path: Path
    ) -> Dict[str, Any]:
        """Extract metadata from DOCX document."""
        core_props = doc.core_properties
        
        return {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "subject": core_props.subject or "",
            "creator": core_props.author or "",
            "creation_date": str(core_props.created) if core_props.created else "",
            "modification_date": str(core_props.modified) if core_props.modified else "",
            "page_count": 1,  # DOCX doesn't have explicit page count
            "format": "DOCX",
            "word_count": len(doc.paragraphs),
        }
    
    def _create_text_block(
        self, paragraph: Paragraph, page_num: int, y_position: float
    ) -> TextBlock:
        """Create a text block from a paragraph."""
        # Extract font information from first run
        font_info = {}
        if paragraph.runs:
            first_run = paragraph.runs[0]
            font_info = {
                "font": first_run.font.name,
                "size": first_run.font.size.pt if first_run.font.size else None,
                "bold": first_run.bold,
                "italic": first_run.italic,
                "underline": first_run.underline,
            }
        
        # Estimate text dimensions
        text_length = len(paragraph.text)
        estimated_width = min(text_length * 8, 500)  # Rough character width
        estimated_height = 15  # Approximate line height
        
        return TextBlock(
            text=paragraph.text,
            page=page_num,
            bbox={
                "x": 0,
                "y": y_position,
                "width": estimated_width,
                "height": estimated_height,
            },
            font_info=font_info,
        )
    
    def _extract_table_text(self, table: Table) -> str:
        """Extract text content from a table."""
        table_text = []
        
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    row_text.append(cell_text)
            
            if row_text:
                table_text.append(" | ".join(row_text))
        
        return "\n".join(table_text)
    
    def _extract_images(self, doc: DocxDocument, doc_name: str) -> List[ImageData]:
        """Extract images from DOCX document."""
        images: List[ImageData] = []
        
        try:
            # Get document relationships to find images
            rels = doc.part.rels
            
            image_index = 0
            for rel in rels.values():
                if "image" in rel.target_ref:
                    try:
                        # Get image data
                        image_part = rel.target_part
                        image_data = image_part.blob
                        
                        # Determine image format
                        content_type = image_part.content_type
                        if "png" in content_type:
                            ext = ".png"
                        elif "jpeg" in content_type or "jpg" in content_type:
                            ext = ".jpg"
                        elif "gif" in content_type:
                            ext = ".gif"
                        else:
                            ext = ".png"  # Default
                        
                        # Save image to temporary location
                        with tempfile.NamedTemporaryFile(
                            suffix=ext, delete=False, prefix=f"{doc_name}_img{image_index}_"
                        ) as temp_file:
                            temp_file.write(image_data)
                            image_path = temp_file.name
                        
                        # Create image data (DOCX doesn't provide exact positioning)
                        image_data_obj = ImageData(
                            image_path=image_path,
                            page=1,  # DOCX doesn't have explicit pages
                            bbox={
                                "x": 0,
                                "y": image_index * 200,  # Estimate position
                                "width": 300,  # Default width
                                "height": 200,  # Default height
                            },
                            format=ext.upper().lstrip("."),
                        )
                        images.append(image_data_obj)
                        image_index += 1
                    
                    except Exception as e:
                        # Skip problematic images
                        continue
        
        except Exception as e:
            # Skip image extraction if it fails
            pass
        
        return images