"""
Base Store Interface

Abstract interface for user profile and conversation context storage.
Allows switching between PostgreSQL and in-memory implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class UserProfile:
    """User profile data structure."""
    phone_number: str
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None

    # Cached chart data (calculated from birth details)
    moon_sign: Optional[str] = None
    sun_sign: Optional[str] = None
    ascendant: Optional[str] = None
    moon_nakshatra: Optional[str] = None

    # Preferences
    preferred_language: str = "en"
    notification_enabled: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def has_birth_details(self) -> bool:
        """Check if user has complete birth details."""
        return all([self.birth_date, self.birth_time, self.birth_place])

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class BaseStore(ABC):
    """
    Abstract base class for user/context storage.

    Implementations:
    - PostgresStore: Full persistence with PostgreSQL
    - MemoryStore: In-memory only (for lite mode/testing)
    """

    @abstractmethod
    async def get_user(self, phone: str) -> Optional[UserProfile]:
        """Get user profile by phone number."""
        pass

    @abstractmethod
    async def save_birth_details(
        self,
        phone: str,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: str = None
    ) -> bool:
        """Save user's birth details."""
        pass

    @abstractmethod
    async def save_chart_data(
        self,
        phone: str,
        moon_sign: str = None,
        sun_sign: str = None,
        ascendant: str = None,
        moon_nakshatra: str = None
    ) -> bool:
        """Save calculated chart data (cached)."""
        pass

    @abstractmethod
    async def get_birth_details(self, phone: str) -> Optional[Dict[str, str]]:
        """Get just the birth details for a user."""
        pass

    @abstractmethod
    async def save_context(
        self,
        phone: str,
        context_type: str,
        context_data: dict,
        expires_in_minutes: int = 30
    ) -> bool:
        """Save conversation context for multi-turn flows."""
        pass

    @abstractmethod
    async def get_context(self, phone: str, context_type: str) -> Optional[dict]:
        """Get conversation context if not expired."""
        pass

    @abstractmethod
    async def clear_context(self, phone: str, context_type: str = None) -> bool:
        """Clear conversation context."""
        pass

    @abstractmethod
    async def save_user_language(self, phone: str, language: str) -> bool:
        """Save user's preferred language."""
        pass

    @abstractmethod
    async def get_user_language(self, phone: str) -> str:
        """Get user's preferred language (default: 'en')."""
        pass

    # Flow state management (for step-based flows)
    @abstractmethod
    async def save_flow_state(
        self,
        phone: str,
        flow_name: str,
        current_step: str,
        collected_data: dict,
        expires_in_minutes: int = 10
    ) -> bool:
        """Save current flow state for step-based conversations."""
        pass

    @abstractmethod
    async def get_flow_state(self, phone: str) -> Optional[dict]:
        """Get active flow state if not expired."""
        pass

    @abstractmethod
    async def clear_flow_state(self, phone: str) -> bool:
        """Clear flow state (flow completed or cancelled)."""
        pass
