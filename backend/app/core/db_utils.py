"""
Database utilities for migrations and management
"""

import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations():
    """Run Alembic migrations"""
    try:
        # Get the backend directory path
        backend_dir = Path(__file__).parent.parent.parent
        
        # Run alembic upgrade
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Migration failed: {result.stderr}")
            raise RuntimeError(f"Migration failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


def create_migration(message: str):
    """Create a new migration"""
    try:
        backend_dir = Path(__file__).parent.parent.parent
        
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", message],
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Migration '{message}' created successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Failed to create migration: {result.stderr}")
            raise RuntimeError(f"Failed to create migration: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise


if __name__ == "__main__":
    # Run migrations when script is executed directly
    run_migrations()