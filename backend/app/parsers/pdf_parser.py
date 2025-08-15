"""PDF parser implementation using PyMuPDF (fitz)."""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import fitz  # PyMuPDF
from PIL import Image

from .base import BaseParser, ImageData, ParsedContent, TextBlock


class PDFParser(BaseParser):
    """Parser for PDF documents using PyMuPDF."""
    
    def __init__(self):
        """Initialize PDF parser."""
        super().__init__()
        self.supported_extensions = [".pdf"]
        self.name = "PDFParser"
    
    async def parse(self, file_path: Path) -> ParsedContent:
        """
        Parse a PDF document and extract content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ParsedContent containing extracted text blocks, images, and metadata
        """
        self.validate_file(file_path)
        
        # Run parsing in thread pool to avoid blocking
        return await asyncio.get_event_loop().run_in_executor(
            None, self._parse_sync, file_path
        )
    
    def _parse_sync(self, file_path: Path) -> ParsedContent:
        """Synchronous PDF parsing implementation."""
        text_blocks: List[TextBlock] = []
        images: List[ImageData] = []
        metadata: Dict[str, Any] = {}
        
        try:
            # Open PDF document
            doc = fitz.open(str(file_path))
            
            # Extract document metadata
            metadata = self._extract_document_metadata(doc)
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text blocks from page
                page_text_blocks = self._extract_text_blocks(page, page_num + 1)
                text_blocks.extend(page_text_blocks)
                
                # Extract images from page
                page_images = self._extract_images(page, page_num + 1, file_path.stem)
                images.extend(page_images)
            
            doc.close()
            
        except Exception as e:
            raise Exception(f"Failed to parse PDF {file_path}: {str(e)}") from e
        
        return ParsedContent(
            text_blocks=text_blocks,
            images=images,
            metadata=metadata
        )
    
    def _extract_document_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata from PDF document."""
        doc_metadata = doc.metadata
        
        return {
            "title": doc_metadata.get("title", ""),
            "author": doc_metadata.get("author", ""),
            "subject": doc_metadata.get("subject", ""),
            "creator": doc_metadata.get("creator", ""),
            "producer": doc_metadata.get("producer", ""),
            "creation_date": doc_metadata.get("creationDate", ""),
            "modification_date": doc_metadata.get("modDate", ""),
            "page_count": len(doc),
            "format": "PDF",
        }
    
    def _extract_text_blocks(self, page: fitz.Page, page_num: int) -> List[TextBlock]:
        """Extract text blocks from a PDF page."""
        text_blocks: List[TextBlock] = []
        
        try:
            # Get text blocks with formatting information
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" not in block:
                    continue
                
                # Combine lines within a block
                block_text = ""
                block_bbox = block["bbox"]
                font_info = {}
                
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                        
                        # Collect font information from first span
                        if not font_info and span.get("font"):
                            font_info = {
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"],
                                "color": span.get("color", 0),
                            }
                    
                    if line_text.strip():
                        block_text += line_text + " "
                
                # Create text block if we have content
                if block_text.strip():
                    text_block = TextBlock(
                        text=block_text.strip(),
                        page=page_num,
                        bbox={
                            "x": block_bbox[0],
                            "y": block_bbox[1], 
                            "width": block_bbox[2] - block_bbox[0],
                            "height": block_bbox[3] - block_bbox[1],
                        },
                        font_info=font_info,
                    )
                    text_blocks.append(text_block)
        
        except Exception as e:
            # Fallback to simple text extraction
            text = page.get_text()
            if text.strip():
                page_rect = page.rect
                text_block = TextBlock(
                    text=text.strip(),
                    page=page_num,
                    bbox={
                        "x": page_rect.x0,
                        "y": page_rect.y0,
                        "width": page_rect.width,
                        "height": page_rect.height,
                    },
                )
                text_blocks.append(text_block)
        
        return text_blocks
    
    def _extract_images(
        self, page: fitz.Page, page_num: int, doc_name: str
    ) -> List[ImageData]:
        """Extract images from a PDF page."""
        images: List[ImageData] = []
        
        try:
            # Get list of images on the page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Skip if image is too small or has no data
                    if pix.width < 10 or pix.height < 10:
                        pix = None
                        continue
                    
                    # Convert to PIL Image and save
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        
                        # Save image to temporary location
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False, prefix=f"{doc_name}_p{page_num}_"
                        ) as temp_file:
                            temp_file.write(img_data)
                            image_path = temp_file.name
                        
                        # Get image position on page
                        img_rects = page.get_image_rects(xref)
                        if img_rects:
                            rect = img_rects[0]  # Use first occurrence
                            bbox = {
                                "x": rect.x0,
                                "y": rect.y0,
                                "width": rect.width,
                                "height": rect.height,
                            }
                        else:
                            # Fallback bbox if position not found
                            bbox = {"x": 0, "y": 0, "width": pix.width, "height": pix.height}
                        
                        image_data = ImageData(
                            image_path=image_path,
                            page=page_num,
                            bbox=bbox,
                            format="PNG",
                            original_size={"width": pix.width, "height": pix.height},
                        )
                        images.append(image_data)
                    
                    pix = None  # Free memory
                
                except Exception as e:
                    # Skip problematic images
                    continue
        
        except Exception as e:
            # Skip image extraction if it fails
            pass
        
        return images