# Document Learning App

A full-stack application that transforms documents into interactive learning experiences through automated content extraction and spaced repetition.

## Features

- **Document Processing**: Supports PDF, DOCX, and Markdown files
- **Automatic Content Extraction**: Extracts chapters, images, and knowledge points
- **Flashcard Generation**: Creates Q&A, cloze deletion, and image hotspot cards
- **Spaced Repetition System**: Implements SM-2 algorithm for optimal learning
- **Semantic Search**: Vector-based search with pgvector
- **Privacy-First**: Local processing options available

## Architecture

- **Backend**: FastAPI with PostgreSQL and Redis
- **Frontend**: React 18 with TypeScript and Vite
- **Processing**: Background workers with RQ (Redis Queue)
- **Infrastructure**: Docker Compose for local development

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Development Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd document-learning-app
```

2. Start the development environment:

```bash
cd infrastructure
docker-compose up -d
```

3. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend
pip install -e .[dev]
pre-commit install
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Test files
│   ├── alembic/      # Database migrations
│   └── uploads/      # File storage
├── frontend/         # React frontend
│   ├── src/          # Source code
│   ├── public/       # Static assets
│   └── dist/         # Build output
├── infrastructure/   # Docker configuration
│   └── docker-compose.yml
└── .github/          # CI/CD workflows
```

## Development Tools

### Backend

- **Linting**: ruff
- **Formatting**: black
- **Type Checking**: mypy
- **Testing**: pytest
- **Pre-commit**: Automated code quality checks

### Frontend

- **Linting**: ESLint
- **Type Checking**: TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite

## Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.
