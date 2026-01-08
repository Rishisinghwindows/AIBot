import asyncio
from __future__ import annotations

from ohgrt_api.logger import logger
from ohgrt_api.services.postgres_service import PostgresService


class PostgresAgent:
    def __init__(self, service: PostgresService):
        self.service = service

    async def run(self, message: str) -> str:
        logger.info(f"sql_agent_run_invoked: {message[:50]}")
        result = await asyncio.to_thread(self.service.run_sql, message)
        logger.info("sql_agent_response")
        return f"SQL result: {result}"
