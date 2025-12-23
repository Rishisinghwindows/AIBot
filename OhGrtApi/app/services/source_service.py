from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID
import psycopg2
import psycopg2.extras

# Register UUID adapter for psycopg2
psycopg2.extras.register_uuid()

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError
from app.utils.models import Source, SourceCreate


class SourceService:
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

    def _execute_query(self, query: str, params: Optional[tuple] = None, fetch: str = "none") -> Any:
        logger.debug("source_service_execute_query", query=query, params=params)
        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch == "one":
                        res = cur.fetchone()
                        if res is None:
                            return None
                        col_names = [desc[0] for desc in cur.description]
                        return dict(zip(col_names, res))
                    elif fetch == "all":
                        col_names = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        return [dict(zip(col_names, row)) for row in rows]
                    return None
        except Exception as exc:
            logger.error("source_service_sql_error", error=str(exc))
            raise ServiceError("SQL execution failed in SourceService") from exc

    def get_sources_by_user(self, user_id: UUID) -> List[Source]:
        query = "SELECT * FROM sources WHERE user_id = %s ORDER BY created_at DESC;"
        params = (str(user_id),)
        results = self._execute_query(query, params, fetch="all")
        if not results:
            return []
        return [Source(**result) for result in results]

    def create_source(self, user_id: UUID, source_create: SourceCreate) -> Source:
        query = """
            INSERT INTO sources (user_id, type, path, content, filename)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
        """
        params = (
            str(user_id),
            source_create.type,
            source_create.path,
            source_create.content,
            source_create.filename,
        )
        result = self._execute_query(query, params, fetch="one")
        if not result:
            raise ServiceError("Failed to create source.")
        return Source(**result)

    def delete_source(self, source_id: UUID, user_id: UUID) -> bool:
        query = "DELETE FROM sources WHERE id = %s AND user_id = %s;"
        params = (str(source_id), str(user_id))
        self._execute_query(query, params, fetch="none")
        return True
