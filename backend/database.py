"""
Database configuration and session management for ContextPilot.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from config import settings
from logger import logger


# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.database_echo
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for getting a database session.
    Use in non-FastAPI contexts. Handles all exceptions and ensures cleanup.
    
    Yields:
        Database session
        
    Raises:
        Exception: Re-raises any exception after rolling back transaction
    """
    db = SessionLocal()
    try:
        yield db
        # Commit if no exception occurred
        db.commit()
    except Exception as e:
        # Rollback on any exception
        db.rollback()
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        # Always close the session
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    
    Raises:
        Exception: If table creation fails
    """
    try:
        from db_models import ContextUnitDB, ConversationDB, MessageDB
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def drop_db() -> None:
    """
    Drop all database tables. Use with caution!
    
    Raises:
        Exception: If table drop fails
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}", exc_info=True)
        raise


def check_db_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        from sqlalchemy import text
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
