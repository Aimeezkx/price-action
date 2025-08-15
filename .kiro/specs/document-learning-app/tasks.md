# Implementation Plan

- [x] 1. Set up project structure and development environment
  - Create mono-repo structure with /backend (FastAPI), /frontend (React + Vite), /infrastructure (Docker)
  - Configure Python development tools: ruff, black, mypy, pytest, pre-commit
  - Set up CI/CD pipeline with GitHub Actions for lint, typecheck, test, build
  - Create Docker Compose configuration for local development
  - _Requirements: 12.1, 12.2_

- [x] 2. Initialize database schema and core models
  - Implement SQLAlchemy models for Document, Chapter, Figure, Knowledge, Card, SRS
  - Create Alembic migrations for database schema
  - Add pgvector extension support for vector embeddings
  - Implement database connection and session management
  - _Requirements: 2.1, 2.2, 2.3, 6.1, 8.1_

- [x] 3. Create object storage abstraction layer
  - Implement Storage interface for file and image management
  - Create local filesystem storage implementation
  - Add methods for saving, retrieving, and deleting files
  - Write unit tests for storage operations
  - _Requirements: 2.2, 4.4_

- [x] 4. Implement document upload and task queue system
  - Create FastAPI endpoint for document upload (POST /ingest)
  - Implement document validation and file type checking
  - Set up Redis Queue (RQ) for background processing
  - Create RQ worker process for document processing pipeline
  - Add document status tracking and progress updates
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 5. Build document parser framework
  - Create BaseParser abstract class with common interface
  - Implement PDFParser using PyMuPDF for text and image extraction
  - Implement DocxParser using python-docx for Word documents
  - Implement MarkdownParser for Markdown files with image links
  - Add parser factory and registration system
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Implement chapter structure recognition
  - Create chapter extraction logic using PDF bookmarks/outlines
  - Implement heuristic chapter detection (font size, formatting patterns)
  - Build hierarchical table of contents generation
  - Add content block assignment to chapters
  - Create fallback single-chapter handling
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Build image and caption pairing system
  - Implement image extraction with bounding box coordinates
  - Create caption pattern matching (图x, Fig.x, Figure x)
  - Build proximity-based image-caption association
  - Add fallback text paragraph selection for captions
  - Implement relationship storage and validation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Create text segmentation and preprocessing
  - Implement text segmentation into 300-600 character blocks
  - Add sentence boundary detection and preservation
  - Create content block merging based on similarity
  - Implement anchor information tracking (page, chapter, position)
  - Add text cleaning and normalization utilities
  - _Requirements: 5.1, 5.4_

- [x] 9. Build NLP entity extraction pipeline
  - Integrate spaCy for English entity recognition
  - Add jieba/HanLP support for Chinese text processing
  - Implement entity filtering and deduplication
  - Create term frequency analysis and ranking
  - Add stopword removal and entity validation
  - _Requirements: 5.3, 5.4_

- [x] 10. Implement knowledge point extraction system
  - Create rule-based knowledge extraction for definitions, facts, theorems
  - Implement LLM integration with JSON schema validation
  - Add fallback mechanism from LLM to rule-based extraction
  - Create knowledge point classification (definition, fact, theorem, process, example)
  - Implement entity linking within knowledge points
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

d- [x] 11. Build semantic embedding and vector search
  - Integrate sentence-transformers for multilingual embeddings
  - Implement vector storage in PostgreSQL with pgvector
  - Create semantic similarity calculation and indexing
  - Add vector search API with similarity thresholds
  - Implement hybrid full-text and semantic search
  - _Requirements: 9.1, 9.2, 9.4_

- [x] 12. Create flashcard generation system
  - Implement Q&A card generation from definition knowledge points
  - Build cloze deletion card creation with entity blanking (max 2-3 blanks)
  - Create image hotspot card generation with clickable regions
  - Add card-to-knowledge traceability and source linking
  - Implement difficulty scoring based on text complexity and term density
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 13. Implement duplicate detection and deduplication
  - Create semantic similarity calculation for card comparison
  - Implement duplicate detection with >0.9 similarity threshold
  - Build card merging logic preserving comprehensive content
  - Add duplicate removal with source traceability
  - Ensure final duplicate rate <5% of total cards
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 14. Build spaced repetition system (SRS)
  - Implement SM-2 algorithm for card scheduling
  - Create SRS state management (ease factor, interval, repetitions)
  - Add card grading system with 0-5 scale
  - Implement review date calculation and updates
  - Add poor performance reset logic (quality < 3)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Create daily review and scheduling system
  - Implement daily review card selection (overdue + due)
  - Create review session management and progress tracking
  - Add concurrent review handling and state synchronization
  - Build review statistics and performance metrics
  - Implement review queue optimization
  - _Requirements: 8.5, 12.5_

- [x] 16. Build search and filtering API
  - Create full-text search with highlighting
  - Implement semantic search using vector embeddings
  - Add filtering by chapter, difficulty, and card type
  - Create combined search results ranking
  - Implement search performance optimization (MRR ≥ 0.8)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 17. Implement export functionality
  - Create CSV export compatible with Anki format
  - Add Notion-compatible CSV export with proper field mapping
  - Implement JSONL backup export for complete data
  - Create import functionality for JSONL backups
  - Add metadata preservation in exports (difficulty, source, anchors)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 18. Build core FastAPI endpoints
  - Implement document management endpoints (GET /doc/{id}, POST /ingest)
  - Create chapter and content endpoints (GET /doc/{id}/toc, GET /chapter/{id}/fig)
  - Add knowledge point endpoints (GET /chapter/{id}/k)
  - Implement card management endpoints (POST /card/gen, GET /cards)
  - Create review endpoints (GET /review/today, POST /review/grade)
  - _Requirements: 1.1, 1.2, 3.3, 4.5, 6.4, 8.1, 8.2_

- [x] 19. Add search and export API endpoints
  - Implement search endpoint (GET /search) with query and filter parameters
  - Create export endpoints (GET /export/csv, GET /export/jsonl)
  - Add import endpoint (POST /import/jsonl) for backup restoration
  - Implement proper error handling and validation
  - Add OpenAPI documentation and schema validation
  - _Requirements: 9.1, 9.3, 10.1, 10.3, 10.4_

- [x] 20. Create React frontend application structure
  - Set up React 18 + TypeScript + Vite project
  - Configure Tailwind CSS and component library
  - Implement React Router for client-side navigation
  - Set up TanStack Query for server state management
  - Create basic layout and navigation components
  - _Requirements: 12.3_

- [x] 21. Build document upload and management UI
  - Create document upload page with drag-and-drop support
  - Implement upload progress tracking and status display
  - Build document list view with processing status
  - Add document details page with chapter navigation
  - Create error handling and user feedback for upload failures
  - _Requirements: 1.1, 1.3, 12.3_

- [x] 22. Implement chapter and content browsing
  - Create table of contents (TOC) navigation component
  - Build chapter detail view with figures and knowledge points
  - Implement image viewer with caption display
  - Add knowledge point browser with source anchors
  - Create responsive design for mobile and desktop
  - _Requirements: 3.3, 4.5, 5.4_

- [x] 23. Build flashcard learning interface
  - Create card display component with front/back flip animation
  - Implement grading interface with 0-5 scale buttons
  - Add keyboard shortcuts (space for flip, 1-5 for grading, J/K navigation)
  - Build review session management with progress tracking
  - Create card filtering (chapter, difficulty, type)
  - _Requirements: 6.4, 8.1, 8.2, 9.5, 12.4_

- [x] 24. Implement image hotspot card interaction
  - Create image viewer component with zoom and pan
  - Implement clickable hotspot regions with hover effects
  - Add touch gesture support for mobile devices
  - Build hotspot validation and feedback system
  - Create responsive image scaling and positioning
  - _Requirements: 6.3, 12.4_

- [x] 25. Build search and filtering interface
  - Create search input with real-time suggestions
  - Implement search results display with highlighting
  - Add filter controls for chapter, difficulty, and card type
  - Build advanced search options (semantic vs full-text)
  - Create search history and saved searches
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 26. Implement privacy and security features
  - Add privacy mode toggle for local-only processing
  - Implement data anonymization in logging
  - Create secure file upload validation
  - Add user data protection and access controls
  - Implement privacy-compliant external service integration
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 27. Create performance monitoring and optimization
  - Implement frontend performance monitoring
  - Add backend API response time tracking
  - Create database query optimization and indexing
  - Build caching layer for frequently accessed data
  - Add memory usage monitoring for document processing
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 28. Build comprehensive test suite
  - Create unit tests for all parser implementations
  - Add integration tests for document processing pipeline
  - Implement API endpoint testing with test data
  - Build frontend component testing with React Testing Library
  - Create end-to-end testing for complete user workflows
  - _Requirements: All requirements - validation through testing_

- [ ] 29. Set up production deployment configuration
  - Create production Docker Compose with proper networking
  - Configure Nginx reverse proxy for API and static files
  - Set up environment variable management
  - Implement database backup and migration strategies
  - Add monitoring and logging for production environment
  - _Requirements: 12.1, 12.2_

- [ ] 30. Create sample data and documentation
  - Prepare sample documents for testing and demonstration
  - Create user documentation and API reference
  - Build developer setup and contribution guide
  - Add performance benchmarks and accuracy metrics
  - Create deployment and maintenance documentation
  - _Requirements: All requirements - documentation and validation_

## iOS Application Development

- [x] 31. Set up React Native iOS project structure
  - Initialize React Native 0.72 project with TypeScript
  - Configure navigation with React Navigation 6
  - Set up TanStack Query for API state management
  - Create shared types and API client for backend integration
  - Configure development environment and build tools
  - _Requirements: 12.3, 12.4_

- [x] 32. Build iOS flashcard learning interface
  - Create FlashCard component with native animations
  - Implement touch-optimized GradingInterface with 0-5 scale
  - Build StudyScreen with session management and progress tracking
  - Add native gesture support for card interactions
  - Create responsive design for iPhone and iPad
  - _Requirements: 6.4, 8.1, 8.2, 12.4_

- [x] 33. Implement iOS document management
  - Create DocumentsScreen with native file picker integration
  - Build document upload with progress tracking
  - Implement document list with processing status display
  - Add native iOS document picker for PDF/DOCX files
  - Create error handling and user feedback
  - _Requirements: 1.1, 1.3, 12.3_

- [x] 34. Build iOS search and discovery interface
  - Create SearchScreen with native keyboard handling
  - Implement search results display with highlighting
  - Add filter controls optimized for touch interaction
  - Build search history and suggestions
  - Create responsive search interface for mobile
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 35. Create iOS profile and settings
  - Build ProfileScreen with user statistics
  - Implement app settings and preferences
  - Add export functionality for Anki/Notion formats
  - Create data management and cache controls
  - Build study statistics and progress tracking
  - _Requirements: 10.1, 10.2, 12.5_

- [x] 36. Implement iOS-specific features
  - Add push notifications for study reminders
  - Implement offline study capability with local storage
  - Create iOS widgets for study progress
  - Add Siri Shortcuts integration for voice commands
  - Implement haptic feedback for interactions
  - _Requirements: 12.4, 12.5_

- [x] 37. Build iOS image hotspot interaction
  - Create native image viewer with zoom and pan gestures
  - Implement touch-based hotspot interaction
  - Add pinch-to-zoom and pan gesture recognition
  - Build hotspot validation with visual feedback
  - Create responsive image scaling for different screen sizes
  - _Requirements: 6.3, 12.4_

- [x] 38. Optimize iOS performance and user experience
  - Implement image caching for faster card loading
  - Add background sync for seamless data updates
  - Create memory optimization for large document sets
  - Implement battery usage optimization
  - Add accessibility support for VoiceOver
  - _Requirements: 12.1, 12.2, 12.4_

- [x] 39. Create iOS testing and quality assurance
  - Build unit tests for React Native components
  - Add integration tests for API interactions
  - Implement UI testing with Detox framework
  - Create performance testing for animations
  - Add crash reporting and error tracking
  - _Requirements: All iOS requirements - validation through testing_

- [x] 40. Prepare iOS App Store deployment
  - Configure app signing and provisioning profiles
  - Create App Store Connect listing and metadata
  - Build release version with optimizations
  - Set up TestFlight for beta testing
  - Prepare app review submission materials
  - _Requirements: 12.1, 12.2_

## Platform Integration and Maintenance

- [x] 41. Implement cross-platform data synchronization
  - Ensure seamless sync between web and iOS platforms
  - Create conflict resolution for concurrent edits
  - Implement offline-first architecture for iOS
  - Add data consistency validation across platforms
  - Build sync status indicators and error handling
  - _Requirements: 12.5_

- [x] 42. Create unified deployment and monitoring
  - Set up monitoring for both web and iOS platforms
  - Create unified analytics and usage tracking
  - Implement A/B testing framework for both platforms
  - Build performance monitoring across platforms
  - Add user feedback collection and analysis
  - _Requirements: 12.1, 12.2, 12.5_