# Database Setup and Models

This document describes the database schema and models for the Document Learning App.

## Overview

The application uses PostgreSQL with the pgvector extension for storing documents, extracted knowledge, and learning data. The database schema supports:

- Document storage and processing status tracking
- Hierarchical chapter structure
- Image/figure management with captions
- Knowledge point extraction with vector embeddings
- Flashcard generation and spaced repetition system (SRS)

## Models

### Document Hierarchy

```
Document (PDF, DOCX, Markdown files)
├── Chapter (Hierarchical structure)
    ├── Figure (Images with captions)
    └── Knowledge (Extracted knowledge points)
        └── Card (Generated flashcards)
            └── SRS (Spaced repetition data)
```

### Core Models

#### Document
- Stores uploaded files and processing status
- Tracks file metadata and processing errors
- Links to chapters for content organization

#### Chapter
- Hierarchical document structure (levels 1-6)
- Page ranges and content text
- Links to figures and knowledge points

#### Figure
- Images extracted from documents
- Captions and positioning information
- Bounding box coordinates for precise location

#### Knowledge
- Extracted knowledge points (definitions, facts, theorems, etc.)
- Named entities and anchor information
- Vector embeddings for semantic search (384-dimensional)

#### Card
- Generated flashcards (Q&A, cloze deletion, image hotspot)
- Difficulty scoring and metadata
- Links back to source knowledge

#### SRS (Spaced Repetition System)
- SM-2 algorithm implementation
- Ease factor, interval, and repetition tracking
- Due dates and review history

## Database Setup

### Prerequisites

1. PostgreSQL 12+ with pgvector extension
2. Python 3.11+ with required dependencies

### Installation

1. Install PostgreSQL and pgvector:
```bash
# On macOS with Homebrew
brew install postgresql pgvector

# On Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
# Install pgvector from source or package manager
```

2. Create database:
```sql
CREATE DATABASE document_learning;
CREATE USER doc_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE document_learning TO doc_user;
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
# Install dependencies first
pip install -e .

# Run migrations
python -m alembic upgrade head
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching and queues
- `DEBUG`: Enable debug mode and SQL logging
- `PRIVACY_MODE`: Enable local-only processing

### Database Connection

The application uses SQLAlchemy with connection pooling and automatic session management. Database sessions are provided via dependency injection in FastAPI endpoints.

## Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Create empty migration
python -m alembic revision -m "Description of changes"
```

### Running Migrations

```bash
# Upgrade to latest
python -m alembic upgrade head

# Upgrade to specific revision
python -m alembic upgrade <revision_id>

# Downgrade
python -m alembic downgrade -1
```

## Testing

### Model Tests

Run the model tests to verify database schema:

```bash
# Install test dependencies
pip install -e .[dev]

# Run model tests
python -m pytest tests/test_models.py -v
```

### Manual Verification

```bash
# Verify project structure
python verify_structure.py
```

## Performance Considerations

### Indexes

The schema includes indexes on:
- Foreign key relationships
- Frequently queried fields (status, due_date, etc.)
- Vector similarity search (pgvector IVFFLAT)

### Vector Search

Knowledge embeddings use 384-dimensional vectors from sentence-transformers. The pgvector extension provides efficient similarity search with cosine distance.

### Connection Pooling

SQLAlchemy connection pooling is configured for optimal performance with FastAPI's async capabilities.

## Security

- Database credentials via environment variables
- SQL injection protection through SQLAlchemy ORM
- Input validation via Pydantic models
- Optional privacy mode for local-only processing

## Monitoring

- SQL query logging in debug mode
- Database connection health checks
- Migration status tracking
- Error logging for processing failures