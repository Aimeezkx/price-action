# Document Learning App - Backend

FastAPI backend for the Document Learning App.

## Setup

1. Install dependencies:
```bash
pip install -e .[dev]
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run the development server:
```bash
uvicorn main:app --reload
```

## Development

### Code Quality

- **Linting**: `ruff check .`
- **Formatting**: `black .`
- **Type Checking**: `mypy .`
- **Testing**: `pytest`

### Database

- **Migrations**: `alembic upgrade head`
- **Create Migration**: `alembic revision --autogenerate -m "description"`

### Environment Variables

Create a `.env` file with:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/document_learning
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```