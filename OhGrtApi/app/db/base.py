from __future__ import annotations

from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# Create engine without pool_pre_ping to avoid immediate connection attempt
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None

try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Set search_path to use the agentic schema for all connections
    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET search_path TO {settings.postgres_schema}, public")
        cursor.close()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    # Database not configured, engine will be None
    pass

# Create Base with schema explicitly set to ensure all operations use the correct schema
Base = declarative_base()
Base.metadata.schema = settings.postgres_schema


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    if SessionLocal is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not available")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_available() -> bool:
    """Check if database is configured and available."""
    return engine is not None and SessionLocal is not None
