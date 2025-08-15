# Requirements Document

## Introduction

This document outlines the requirements for a document-based learning application that automatically extracts knowledge points, images, and annotations from books and files to generate interactive flashcards. The system will parse various document formats (PDF, DOCX, Markdown), extract structured knowledge using NLP techniques, and provide a spaced repetition system (SRS) for effective learning. The application will organize content by chapters and support multiple card types including Q&A, cloze deletion, and image hotspot cards.

## Requirements

### Requirement 1: Document Upload and Processing

**User Story:** As a learner, I want to upload documents (PDF, DOCX, Markdown) so that the system can automatically extract learning content from them.

#### Acceptance Criteria

1. WHEN a user uploads a supported document format THEN the system SHALL accept the file and create a document record
2. WHEN a document is uploaded THEN the system SHALL queue it for background processing
3. WHEN processing begins THEN the system SHALL update the document status to "processing"
4. WHEN processing completes THEN the system SHALL update the document status to "completed" or "failed"
5. IF the document format is unsupported THEN the system SHALL reject the upload with a clear error message

### Requirement 2: Document Parsing and Content Extraction

**User Story:** As a learner, I want the system to automatically extract text, images, and structure from my documents so that I don't have to manually input content.

#### Acceptance Criteria

1. WHEN processing a PDF document THEN the system SHALL extract text blocks with page and position information
2. WHEN processing a PDF document THEN the system SHALL extract images with bounding box coordinates and page numbers
3. WHEN processing a DOCX document THEN the system SHALL extract text content and embedded images
4. WHEN processing a Markdown document THEN the system SHALL parse text content and linked images
5. WHEN extracting content THEN the system SHALL preserve the original document structure and formatting context

### Requirement 3: Chapter Structure Recognition

**User Story:** As a learner, I want the system to automatically identify chapters and sections in my documents so that content is properly organized.

#### Acceptance Criteria

1. WHEN processing a document with bookmarks/outlines THEN the system SHALL use them to create chapter structure
2. WHEN no bookmarks exist THEN the system SHALL use heuristic methods (font size, formatting, patterns) to identify headings
3. WHEN chapter structure is identified THEN the system SHALL create a hierarchical table of contents
4. WHEN chapters are created THEN the system SHALL assign content blocks to appropriate chapters
5. IF no clear structure is found THEN the system SHALL create a single default chapter containing all content

### Requirement 4: Image and Caption Pairing

**User Story:** As a learner, I want images to be automatically paired with their captions and descriptions so that visual content is properly contextualized.

#### Acceptance Criteria

1. WHEN an image is found THEN the system SHALL search nearby text for caption patterns (图x, Fig.x, Figure x)
2. WHEN a caption pattern is found THEN the system SHALL associate it with the nearest image
3. WHEN no caption pattern is found THEN the system SHALL use the nearest text paragraph as a fallback description
4. WHEN pairing images and captions THEN the system SHALL achieve at least 90% accuracy on standard academic documents
5. WHEN image-caption pairs are created THEN the system SHALL store the relationship for card generation

### Requirement 5: Knowledge Point Extraction

**User Story:** As a learner, I want the system to automatically identify and extract key knowledge points from the text so that I can focus on the most important concepts.

#### Acceptance Criteria

1. WHEN processing text content THEN the system SHALL segment it into knowledge point candidates (300-600 characters)
2. WHEN segmenting text THEN the system SHALL identify definitions, facts, theorems, processes, and examples
3. WHEN extracting knowledge points THEN the system SHALL include entity recognition for key terms
4. WHEN knowledge points are created THEN the system SHALL include anchor information (page, chapter)
5. WHEN using LLM extraction THEN the system SHALL validate output against a strict JSON schema
6. IF LLM extraction fails THEN the system SHALL fall back to rule-based extraction methods

### Requirement 6: Flashcard Generation

**User Story:** As a learner, I want the system to automatically generate different types of flashcards from extracted knowledge so that I can study effectively.

#### Acceptance Criteria

1. WHEN a definition knowledge point is found THEN the system SHALL generate a Q&A flashcard
2. WHEN key entities are identified THEN the system SHALL generate cloze deletion cards with 2-3 blanks maximum
3. WHEN images with captions exist THEN the system SHALL generate image hotspot cards with clickable regions
4. WHEN flashcards are generated THEN the system SHALL link them back to source knowledge points and original text
5. WHEN creating cards THEN the system SHALL assign difficulty levels based on text complexity and term density

### Requirement 7: Duplicate Detection and Content Deduplication

**User Story:** As a learner, I want to avoid studying duplicate or highly similar content so that my time is used efficiently.

#### Acceptance Criteria

1. WHEN generating flashcards THEN the system SHALL use semantic similarity to detect duplicates (>0.9 threshold)
2. WHEN duplicates are found THEN the system SHALL merge or remove them automatically
3. WHEN deduplication is complete THEN similar cards SHALL represent less than 5% of the total card set
4. WHEN merging cards THEN the system SHALL preserve the most comprehensive version
5. WHEN removing duplicates THEN the system SHALL maintain traceability to original sources

### Requirement 8: Spaced Repetition System (SRS)

**User Story:** As a learner, I want to review flashcards using spaced repetition so that I can optimize my learning retention.

#### Acceptance Criteria

1. WHEN a user reviews a card THEN the system SHALL implement the SM-2 algorithm for scheduling
2. WHEN a user grades a card (0-5 scale) THEN the system SHALL update the card's repetition parameters
3. WHEN calculating next review date THEN the system SHALL use ease factor, repetition count, and interval
4. WHEN a card is graded poorly (quality < 3) THEN the system SHALL reset its learning progress
5. WHEN generating daily review sets THEN the system SHALL include overdue and due cards

### Requirement 9: Search and Filtering

**User Story:** As a learner, I want to search and filter content so that I can quickly find specific topics or review targeted material.

#### Acceptance Criteria

1. WHEN searching content THEN the system SHALL support both full-text and semantic search
2. WHEN filtering cards THEN the system SHALL support filtering by chapter, difficulty, and card type
3. WHEN searching THEN the system SHALL return knowledge points and cards with highlighted matching text
4. WHEN using semantic search THEN the system SHALL achieve MRR ≥ 0.8 on test datasets
5. WHEN filtering by chapter THEN the system SHALL only show content from selected chapters

### Requirement 10: Export and Integration

**User Story:** As a learner, I want to export my flashcards to other platforms so that I can use them in my preferred study tools.

#### Acceptance Criteria

1. WHEN exporting cards THEN the system SHALL support CSV format compatible with Anki and Notion
2. WHEN exporting THEN the system SHALL include all card metadata (difficulty, source, anchors)
3. WHEN creating backups THEN the system SHALL export complete data in JSONL format
4. WHEN importing backups THEN the system SHALL restore all documents, chapters, knowledge points, and cards
5. WHEN exporting to external tools THEN the system SHALL maintain proper field mapping and formatting

### Requirement 11: Privacy and Security

**User Story:** As a learner, I want my documents and learning data to remain private so that sensitive information is protected.

#### Acceptance Criteria

1. WHEN privacy mode is enabled THEN the system SHALL process all content locally without external API calls
2. WHEN logging activities THEN the system SHALL hash or anonymize sensitive information (filenames, paths, names)
3. WHEN storing user data THEN the system SHALL implement appropriate access controls
4. WHEN processing documents THEN the system SHALL not transmit content to external services in privacy mode
5. WHEN privacy settings change THEN the system SHALL apply them to all subsequent processing

### Requirement 12: Performance and Scalability

**User Story:** As a learner, I want the system to process documents efficiently so that I can start studying without long delays.

#### Acceptance Criteria

1. WHEN uploading a document THEN the system SHALL provide immediate feedback and status updates
2. WHEN processing large documents THEN the system SHALL use background workers to avoid blocking the UI
3. WHEN the application starts THEN the frontend SHALL load in under 2 seconds locally
4. WHEN reviewing cards THEN the system SHALL respond to user interactions within 200ms
5. WHEN processing multiple documents THEN the system SHALL handle concurrent operations safely