from __future__ import annotations

from typing import Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError
from app.utils.models import Profile, ProfileCreate


class ProfileService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _conn_kwargs(self) -> dict:
        return {
            "host": self.settings.postgres_host,
            "port": self.settings.postgres_port,
            "user": self.settings.postgres_user,
            "password": self.settings.postgres_password,
            "dbname": self.settings.postgres_db,
        }

    def _execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: str = "none",
    ) -> Any:
        """
        Execute a SQL query safely.
        fetch: 'one', 'all', or 'none'
        """
        logger.debug("profile_service_execute_query", query=query, params=params)

        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)

                    # ✅ INSERT / UPDATE
                    if fetch == "none":
                        conn.commit()
                        return None

                    # ✅ FETCH ONE
                    if fetch == "one":
                        result = cur.fetchone()
                        return result if result else None

                    # ✅ FETCH ALL
                    if fetch == "all":
                        return cur.fetchall()

                    raise ValueError("Invalid fetch mode")

        except psycopg2.OperationalError as exc:
            logger.error("❌ Database connection failed", error=str(exc))
            raise ServiceError("Database connection failed") from exc

        except psycopg2.ProgrammingError as exc:
            logger.error("❌ SQL syntax / table error", error=str(exc))
            raise ServiceError("SQL syntax / table error") from exc

        except Exception as exc:
            logger.error("❌ Unknown SQL error", error=str(exc))
            raise ServiceError("SQL execution failed in ProfileService") from exc

    # ✅ GET PROFILE
    def get_by_email(self, email: str) -> Optional[Profile]:
        query = "SELECT * FROM profiles WHERE email = %s;"
        params = (email,)

        result = self._execute_query(query, params, fetch="one")

        if not result:
            return None

        return Profile(**result)

    # ✅ CREATE PROFILE
    def create(self, profile_create: ProfileCreate) -> Profile:
        query = """
            INSERT INTO profiles (email, first_name, last_name)
            VALUES (%s, %s, %s)
            RETURNING *;
        """

        params = (
            profile_create.email,
            profile_create.first_name,
            profile_create.last_name,
        )

        result = self._execute_query(query, params, fetch="one")

        if not result:
            raise ServiceError("Failed to create profile.")

        return Profile(**result)
