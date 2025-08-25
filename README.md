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

### Option 1: Full Docker Setup (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd document-learning-app
```

2. Start the complete application stack:
```bash
make docker-up
```

3. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5433
   - Redis: localhost:6379

4. To stop the application:
```bash
make docker-down
```

### Option 2: Local Development Setup

For faster development with hot reloading:

1. Install dependencies:
```bash
make install
```

2. Start infrastructure services (database & redis):
```bash
make docker-up
```

3. Start backend development server:
```bash
make backend-dev
# or manually: cd backend && uvicorn main:app --reload
```

4. In a new terminal, start frontend development server:
```bash
make frontend-dev
# or manually: cd frontend && npm run dev
```

5. The application will be available at:
   - Frontend: http://localhost:5173 (Vite dev server)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 3: Quick Setup with Make Commands

```bash
# Set up development environment
make dev-setup

# Start all services
make docker-up

# View logs
make docker-logs
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

## CORS Configuration

This application implements a hybrid CORS solution to handle API connectivity between frontend (localhost:3001) and backend (localhost:8000):

### Development (Automatic)
- **Vite Proxy**: API requests to `/api/*` are automatically proxied to the backend
- **No CORS errors**: Browser sees same-origin requests
- **Zero configuration**: Works out of the box with `npm run dev`

### Production
- **Environment Variable**: Set `VITE_API_BASE_URL` to your API server URL
- **CORS Middleware**: Backend includes CORS headers for cross-origin requests
- **Flexible Deployment**: Supports both same-origin and cross-origin setups

### Verification
To verify the CORS fix is working:

1. Start both servers: `npm run dev` (frontend) and `uvicorn main:app --reload` (backend)
2. Open browser dev tools (F12) and navigate to http://localhost:3001
3. Check Network tab: API requests should show as `localhost:3001/api/*`
4. Check Console tab: No CORS errors should appear
5. Test file upload: Should complete without errors

For detailed troubleshooting, see `CORS_SOLUTION_DOCUMENTATION.md`.

## Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Create a Pull Request

## License

MIT License - see LICENSE file for details.
