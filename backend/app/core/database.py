"""
Database connection and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Any, AsyncGenerator, Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async SQLAlchemy engine for async operations
try:
    if settings.database_url.startswith('postgresql://'):
        # Use asyncpg for PostgreSQL
        async_database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        async_engine = create_async_engine(
            async_database_url,
            echo=settings.debug,
        )
    elif settings.database_url.startswith('sqlite://'):
        # Use aiosqlite for SQLite
        async_database_url = settings.database_url.replace('sqlite://', 'sqlite+aiosqlite://')
        async_engine = create_async_engine(
            async_database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False}
        )
    else:
        async_engine = None
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
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        # Keep one async-facing session contract for API routes even when the
        # optional async SQLite driver is unavailable.
        db = SyncSessionAsyncAdapter(SessionLocal())
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()


def get_async_session():
    """Get async session for workers (context manager)"""
    if async_session:
        return async_session()

    # Worker services consistently use ``async with`` and await transaction
    # methods.  When the optional async SQLite driver is unavailable, expose
    # the synchronous SQLAlchemy session through the same small async contract
    # instead of leaking a sync Session into the processing pipeline.
    return SyncSessionAsyncAdapter(SessionLocal())


class SyncSessionAsyncAdapter:
    """Async-compatible facade for a synchronous SQLAlchemy session."""

    def __init__(self, session: Session):
        self._session = session

    async def __aenter__(self) -> "SyncSessionAsyncAdapter":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)

    def add(self, instance: Any) -> None:
        self._session.add(instance)

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        return self._session.execute(statement, *args, **kwargs)

    async def flush(self, *args: Any, **kwargs: Any) -> None:
        self._session.flush(*args, **kwargs)

    async def commit(self) -> None:
        self._session.commit()

    async def refresh(self, instance: Any, *args: Any, **kwargs: Any) -> None:
        self._session.refresh(instance, *args, **kwargs)

    async def rollback(self) -> None:
        self._session.rollback()

    async def delete(self, instance: Any) -> None:
        self._session.delete(instance)

    async def close(self) -> None:
        self._session.close()


def get_db_session() -> Session:
    """Get database session (sync)"""
    return SessionLocal()


async def init_db() -> None:
    """
    Initialize database with pgvector extension (PostgreSQL only)
    """
    try:
        with engine.connect() as conn:
            # Only enable pgvector extension for PostgreSQL
            if settings.database_url.startswith('postgresql://'):
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("PostgreSQL database initialized with pgvector extension")
            else:
                logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Application will continue without database connection")
        # Don't raise the exception - allow app to start without DB


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
