# Test Document Library

This directory contains test documents in various formats for comprehensive testing.

## Document Categories

### Small Documents (1-5 pages)
- `small_text.pdf` - Simple text-only PDF
- `small_with_images.pdf` - PDF with embedded images
- `small_structured.pdf` - PDF with clear chapter structure
- `small_document.docx` - Word document with basic formatting
- `small_notes.md` - Markdown document with headers and lists

### Medium Documents (10-25 pages)
- `medium_textbook.pdf` - Academic textbook chapter
- `medium_manual.pdf` - Technical manual with diagrams
- `medium_report.docx` - Business report with tables and charts
- `medium_research.pdf` - Research paper with references

### Large Documents (50+ pages)
- `large_book.pdf` - Complete book with multiple chapters
- `large_thesis.pdf` - PhD thesis with complex structure
- `large_manual.docx` - Comprehensive user manual

### Special Format Documents
- `multilingual.pdf` - Document with multiple languages
- `math_heavy.pdf` - Document with mathematical formulas
- `image_heavy.pdf` - Document primarily composed of images
- `corrupted.pdf` - Intentionally corrupted file for error testing
- `password_protected.pdf` - Password-protected document
- `large_file.pdf` - File exceeding size limits

### Edge Cases
- `empty.pdf` - Empty PDF file
- `single_image.pdf` - PDF with only one image
- `no_text.pdf` - PDF with images but no extractable text
- `complex_layout.pdf` - PDF with complex multi-column layout
- `scanned_document.pdf` - Scanned document requiring OCR

## Usage

These documents are used across different test suites:
- Unit tests for parser validation
- Integration tests for complete workflows
- Performance tests for benchmarking
- Load tests for stress testing
- Security tests for malicious file detection