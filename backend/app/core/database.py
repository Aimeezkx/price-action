"""
Database connection and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator, AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async SQLAlchemy engine for async operations
# For testing, we'll use a simpler sync approach
try:
    async_engine = create_async_engine(
        settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
        echo=settings.debug,
    )
except ImportError:
    # Fallback to sync engine for testing
    async_engine = None

# Create async session maker (SQLAlchemy 1.4 compatible)
if async_engine:
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
else:
    async_session = None

# Create synchronous engine for compatibility
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

# Create SessionLocal class for sync operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session (sync)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    if async_session:
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        # Fallback to sync session for testing
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def get_async_session():
    """Get async session for workers (context manager)"""
    if async_session:
        return async_session()
    else:
        # Fallback to sync session
        return SessionLocal()


async def init_db() -> None:
    """
    Initialize database with pgvector extension
    """
    try:
        with engine.connect() as conn:
            # Enable pgvector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_tables() -> None:
    """
    Create all tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def drop_tables() -> None:
    """
    Drop all tables (for testing)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise