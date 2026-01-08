"""
Database base configuration.

Provides SQLAlchemy engine, session, and base model.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Declarative base for all models
Base = declarative_base()

# Module-level engine and session factory
_engine = None
_SessionLocal = None


def get_engine(database_url: str, schema: str = "agentic"):
    """
    Get or create database engine.

    Args:
        database_url: PostgreSQL connection URL
        schema: Database schema to use

    Returns:
        SQLAlchemy engine
    """
    global _engine

    if _engine is None:
        try:
            _engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"options": f"-c search_path={schema}"},
            )
            logger.info(f"Database engine created with schema: {schema}")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return None

    return _engine


def SessionLocal(database_url: Optional[str] = None, schema: str = "agentic"):
    """
    Get session factory.

    Args:
        database_url: PostgreSQL connection URL (uses env if not provided)
        schema: Database schema

    Returns:
        Session class or None
    """
    global _SessionLocal, _engine

    if _SessionLocal is None and database_url:
        engine = get_engine(database_url, schema)
        if engine:
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
            )

    return _SessionLocal


def get_session(database_url: Optional[str] = None) -> Generator[Session, None, None]:
    """
    Get database session as a context manager.

    Args:
        database_url: PostgreSQL connection URL

    Yields:
        Database session
    """
    session_factory = SessionLocal(database_url)

    if session_factory is None:
        raise RuntimeError("Database not configured")

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_session(database_url: Optional[str] = None) -> Generator[Session, None, None]:
    """
    Get database session as a context manager.

    Args:
        database_url: PostgreSQL connection URL

    Yields:
        Database session
    """
    session_factory = SessionLocal(database_url)

    if session_factory is None:
        raise RuntimeError("Database not configured")

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(database_url: str, schema: str = "agentic") -> bool:
    """
    Initialize database tables.

    Args:
        database_url: PostgreSQL connection URL
        schema: Database schema

    Returns:
        True if successful
    """
    engine = get_engine(database_url, schema)

    if engine is None:
        return False

    try:
        # Create schema if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def check_connection(database_url: str) -> bool:
    """
    Check database connection.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        True if connection is successful
    """
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
