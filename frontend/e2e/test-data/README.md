# Test Data Files

This directory contains test files used by the end-to-end testing suite.

## File Types

### PDF Files
- `sample.pdf` - Small PDF with basic text content (5 pages)
- `medium.pdf` - Medium-sized PDF for performance testing (20 pages)
- `large.pdf` - Large PDF for stress testing (50+ pages)
- `multi-chapter.pdf` - PDF with clear chapter structure
- `with-images.pdf` - PDF containing images and figures
- `with-charts.pdf` - PDF with charts and diagrams for accessibility testing
- `comprehensive.pdf` - PDF that generates various card types
- `hotspot-images.pdf` - PDF with images suitable for hotspot testing

### DOCX Files
- `document.docx` - Word document for format testing

### Markdown Files
- `notes.md` - Markdown file for parser testing

### Invalid Files
- `invalid.txt` - Text file for error testing
- `malicious.exe` - Executable file for security testing

## Usage

These files are referenced in the E2E tests using relative paths like:
```typescript
await fileInput.setInputFiles('test-data/sample.pdf')
```

## Creating Test Files

To create actual test files for your testing environment:

1. Create small PDF files with the specified characteristics
2. Ensure files contain searchable text content
3. Include images in the image-based test files
4. Make sure file sizes match the performance testing requirements

## File Size Guidelines

- Small files: < 1MB
- Medium files: 1-5MB  
- Large files: 5-20MB (for performance testing)

## Content Guidelines

Test files should contain:
- Searchable text with terms like "machine learning", "algorithm", "AI"
- Clear chapter/section structure
- Various content types (text, images, formulas)
- Different difficulty levels for card generation