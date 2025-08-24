FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and README for build
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary pgvector redis rq pydantic pydantic-settings python-multipart PyMuPDF python-docx markdown sentence-transformers spacy jieba scikit-learn pillow python-jose[cryptography] passlib[bcrypt] aiofiles python-magic PyJWT nltk numpy pandas psutil

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]