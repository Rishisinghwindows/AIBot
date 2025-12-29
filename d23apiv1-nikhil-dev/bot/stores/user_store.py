"""
User Profile Store

Manages persistent user data for personalized experiences:
- Birth details (for astrology features)
- Calculated chart data (cached)
- User preferences
- Query history

This enables:
1. "Remember my birth details" - Don't ask every time
2. Personalized predictions based on stored chart
3. Context-aware conversations
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from bot.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class UserStoreError(Exception):
    """Base exception for user store errors."""
    pass


class DatabaseConnectionError(UserStoreError):
    """Failed to connect to database."""
    pass


class DatabaseOperationError(UserStoreError):
    """Database operation failed."""
    pass


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


class UserStore:
    """
    User profile storage with PostgreSQL backend.

    Usage:
        store = get_user_store()
        profile = await store.get_user("919876543210")
        if profile and profile.has_birth_details():
            # Use stored birth details
            ...
        else:
            # Ask user for birth details
            await store.save_birth_details(phone, date, time, place)
    """

    def __init__(self, db_pool=None):
        """
        Initialize with database pool.

        Args:
            db_pool: PostgreSQL connection pool (uses settings if not provided)
        """
        self.pool = db_pool
        self._initialized = False

    async def _get_connection(self):
        """
        Get database connection from pool.

        Returns:
            Database connection

        Raises:
            DatabaseConnectionError: If connection fails
        """
        if self.pool:
            try:
                return await self.pool.acquire()
            except Exception as e:
                logger.error(f"Failed to acquire connection from pool: {e}")
                raise DatabaseConnectionError(f"Pool connection failed: {e}") from e

        # Fallback to direct connection if no pool
        try:
            import asyncpg
            return await asyncpg.connect(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
            )
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseConnectionError(f"Direct connection failed: {e}") from e

    async def _release_connection(self, conn):
        """Release connection back to pool."""
        if self.pool:
            await self.pool.release(conn)
        else:
            await conn.close()

    async def ensure_tables(self):
        """
        Create tables if they don't exist.

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseOperationError: If table creation fails
        """
        if self._initialized:
            return

        conn = await self._get_connection()

        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    phone_number VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100),
                    birth_date VARCHAR(20),
                    birth_time VARCHAR(20),
                    birth_place VARCHAR(100),
                    moon_sign VARCHAR(20),
                    sun_sign VARCHAR(20),
                    ascendant VARCHAR(20),
                    moon_nakshatra VARCHAR(30),
                    preferred_language VARCHAR(10) DEFAULT 'en',
                    notification_enabled BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_context (
                    phone_number VARCHAR(20),
                    context_type VARCHAR(50),
                    context_data JSONB,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (phone_number, context_type)
                )
            """)

            self._initialized = True
            logger.info("User store tables initialized")

        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseOperationError(f"Table creation failed: {e}") from e
        finally:
            await self._release_connection(conn)

    async def get_user(self, phone: str) -> Optional[UserProfile]:
        """
        Get user profile by phone number.

        Args:
            phone: User's phone number

        Returns:
            UserProfile if found, None on error/not found
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for get_user({phone}): {e}")
            return None

        try:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE phone_number = $1",
                phone
            )

            if row:
                return UserProfile(
                    phone_number=row["phone_number"],
                    name=row.get("name"),
                    birth_date=row.get("birth_date"),
                    birth_time=row.get("birth_time"),
                    birth_place=row.get("birth_place"),
                    moon_sign=row.get("moon_sign"),
                    sun_sign=row.get("sun_sign"),
                    ascendant=row.get("ascendant"),
                    moon_nakshatra=row.get("moon_nakshatra"),
                    preferred_language=row.get("preferred_language", "en"),
                    notification_enabled=row.get("notification_enabled", False),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                )
            return None

        except Exception as e:
            logger.error(f"Error getting user {phone}: {e}", exc_info=True)
            return None
        finally:
            await self._release_connection(conn)

    async def save_birth_details(
        self,
        phone: str,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: str = None
    ) -> bool:
        """
        Save user's birth details.

        Args:
            phone: User's phone number
            birth_date: Date of birth (DD-MM-YYYY)
            birth_time: Time of birth (HH:MM AM/PM)
            birth_place: Place of birth
            name: User's name (optional)

        Returns:
            True if saved successfully, False on error
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for save_birth_details({phone}): {e}")
            return False

        try:
            await conn.execute("""
                INSERT INTO user_profiles (phone_number, name, birth_date, birth_time, birth_place, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (phone_number) DO UPDATE
                SET name = COALESCE($2, user_profiles.name),
                    birth_date = $3,
                    birth_time = $4,
                    birth_place = $5,
                    updated_at = NOW()
            """, phone, name, birth_date, birth_time, birth_place)

            logger.info(f"Saved birth details for {phone}")
            return True

        except Exception as e:
            logger.error(f"Error saving birth details for {phone}: {e}", exc_info=True)
            return False
        finally:
            await self._release_connection(conn)

    async def save_chart_data(
        self,
        phone: str,
        moon_sign: str = None,
        sun_sign: str = None,
        ascendant: str = None,
        moon_nakshatra: str = None
    ) -> bool:
        """
        Save calculated chart data (cached).

        Args:
            phone: User's phone number
            moon_sign: Calculated moon sign
            sun_sign: Calculated sun sign
            ascendant: Calculated ascendant
            moon_nakshatra: Calculated moon nakshatra

        Returns:
            True if saved successfully, False on error
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for save_chart_data({phone}): {e}")
            return False

        try:
            await conn.execute("""
                UPDATE user_profiles
                SET moon_sign = COALESCE($2, moon_sign),
                    sun_sign = COALESCE($3, sun_sign),
                    ascendant = COALESCE($4, ascendant),
                    moon_nakshatra = COALESCE($5, moon_nakshatra),
                    updated_at = NOW()
                WHERE phone_number = $1
            """, phone, moon_sign, sun_sign, ascendant, moon_nakshatra)

            return True

        except Exception as e:
            logger.error(f"Error saving chart data for {phone}: {e}", exc_info=True)
            return False
        finally:
            await self._release_connection(conn)

    async def get_birth_details(self, phone: str) -> Optional[Dict[str, str]]:
        """
        Get just the birth details for a user.

        Args:
            phone: User's phone number

        Returns:
            Dict with birth_date, birth_time, birth_place if available
        """
        user = await self.get_user(phone)
        if user and user.has_birth_details():
            return {
                "birth_date": user.birth_date,
                "birth_time": user.birth_time,
                "birth_place": user.birth_place,
            }
        return None

    async def save_context(
        self,
        phone: str,
        context_type: str,
        context_data: dict,
        expires_in_minutes: int = 30
    ) -> bool:
        """
        Save conversation context for multi-turn flows.

        Args:
            phone: User's phone number
            context_type: Type of context (e.g., 'kundli_matching', 'life_prediction')
            context_data: Context data to store
            expires_in_minutes: When context expires

        Returns:
            True if saved successfully, False on error
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for save_context({phone}): {e}")
            return False

        try:
            # Calculate expiry timestamp in Python to avoid SQL injection
            expires_at = datetime.now() + timedelta(minutes=int(expires_in_minutes))

            await conn.execute("""
                INSERT INTO conversation_context (phone_number, context_type, context_data, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (phone_number, context_type) DO UPDATE
                SET context_data = $3,
                    expires_at = $4,
                    created_at = NOW()
            """, phone, context_type, json.dumps(context_data), expires_at)

            return True

        except Exception as e:
            logger.error(f"Error saving context for {phone}: {e}", exc_info=True)
            return False
        finally:
            await self._release_connection(conn)

    async def get_context(self, phone: str, context_type: str) -> Optional[dict]:
        """
        Get conversation context if not expired.

        Args:
            phone: User's phone number
            context_type: Type of context

        Returns:
            Context data dict if found and not expired, None otherwise
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for get_context({phone}): {e}")
            return None

        try:
            row = await conn.fetchrow("""
                SELECT context_data FROM conversation_context
                WHERE phone_number = $1 AND context_type = $2 AND expires_at > NOW()
            """, phone, context_type)

            if row:
                return json.loads(row["context_data"])
            return None

        except Exception as e:
            logger.error(f"Error getting context for {phone}: {e}", exc_info=True)
            return None
        finally:
            await self._release_connection(conn)

    async def clear_context(self, phone: str, context_type: str = None) -> bool:
        """
        Clear conversation context.

        Args:
            phone: User's phone number
            context_type: Specific context to clear (all if None)

        Returns:
            True if cleared successfully, False on error
        """
        try:
            conn = await self._get_connection()
        except DatabaseConnectionError as e:
            logger.error(f"Database unavailable for clear_context({phone}): {e}")
            return False

        try:
            if context_type:
                await conn.execute(
                    "DELETE FROM conversation_context WHERE phone_number = $1 AND context_type = $2",
                    phone, context_type
                )
            else:
                await conn.execute(
                    "DELETE FROM conversation_context WHERE phone_number = $1",
                    phone
                )
            return True

        except Exception as e:
            logger.error(f"Error clearing context for {phone}: {e}", exc_info=True)
            return False
        finally:
            await self._release_connection(conn)

    async def save_user_language(self, phone: str, language: str) -> bool:
        """
        Save user's preferred language.

        Args:
            phone: User's phone number
            language: Language code (e.g., 'hi', 'bn', 'ta')

        Returns:
            True if saved successfully, False on error
        """
        try:
            await self.ensure_tables()
            conn = await self._get_connection()
        except (DatabaseConnectionError, DatabaseOperationError) as e:
            logger.error(f"Database unavailable for save_user_language({phone}): {e}")
            return False

        try:
            await conn.execute("""
                INSERT INTO user_profiles (phone_number, preferred_language, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (phone_number) DO UPDATE
                SET preferred_language = $2, updated_at = NOW()
            """, phone, language)
            return True

        except Exception as e:
            logger.error(f"Error saving language for {phone}: {e}", exc_info=True)
            return False
        finally:
            await self._release_connection(conn)

    async def get_user_language(self, phone: str) -> str:
        """
        Get user's preferred language.

        Args:
            phone: User's phone number

        Returns:
            Language code (default: 'en')
        """
        user = await self.get_user(phone)
        return user.preferred_language if user else "en"

    async def save_flow_state(
        self,
        phone: str,
        flow_name: str,
        current_step: str,
        collected_data: dict,
        expires_in_minutes: int = 10
    ) -> bool:
        """
        Save current flow state for step-based conversations.

        Args:
            phone: User's phone number
            flow_name: Name of the flow (e.g., 'life_prediction')
            current_step: Current step in the flow
            collected_data: Data collected so far
            expires_in_minutes: When the flow expires

        Returns:
            True if saved successfully, False on error
        """
        flow_data = {
            "flow_name": flow_name,
            "current_step": current_step,
            "collected_data": collected_data
        }
        return await self.save_context(
            phone=phone,
            context_type="flow_state",
            context_data=flow_data,
            expires_in_minutes=expires_in_minutes
        )

    async def get_flow_state(self, phone: str) -> Optional[dict]:
        """
        Get active flow state if not expired.

        Args:
            phone: User's phone number

        Returns:
            Flow state dict if active, None otherwise
        """
        return await self.get_context(phone, "flow_state")

    async def clear_flow_state(self, phone: str) -> bool:
        """
        Clear flow state (flow completed or cancelled).

        Args:
            phone: User's phone number

        Returns:
            True if cleared successfully, False on error
        """
        return await self.clear_context(phone, "flow_state")


# Singleton instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """
    Get the singleton UserStore instance.

    Returns:
        UserStore instance
    """
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store
