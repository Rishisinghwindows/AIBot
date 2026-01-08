"""
Database utilities for the unified platform.

Provides SQLAlchemy base classes and session management.
"""

from common.database.base import Base, get_engine, get_session, SessionLocal

__all__ = ["Base", "get_engine", "get_session", "SessionLocal"]
