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

### CORS Configuration

The backend includes CORS middleware configured for the frontend application:

**Allowed Origins:**
- `http://localhost:3000` (legacy)
- `http://localhost:3001` (current frontend port)
- `http://127.0.0.1:3000` and `http://127.0.0.1:3001`
- `http://frontend:3000` (Docker container)

**Configuration Location:** `main.py` - CORSMiddleware setup

**Testing CORS Headers:**
```bash
# Test OPTIONS preflight request
curl -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Expected: 204 status with Access-Control-Allow-Origin header
```

**Note:** In development, the frontend uses Vite proxy, so CORS headers are primarily needed for production deployments or direct API testing.