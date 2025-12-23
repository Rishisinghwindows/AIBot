from __future__ import annotations

from typing import Optional
import json

import psycopg2
from langchain_core.prompts import ChatPromptTemplate

from app.config import Settings
from app.exceptions import SQLInjectionError, ValidationError, DatabaseError, ExternalServiceError
from app.logger import logger
from app.utils.llm import build_chat_llm


class PostgresService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = build_chat_llm(settings)
        self.schema_info = self._load_schema_info()
        self.prompt = ChatPromptTemplate.from_template(
            """You are a SQL expert. Given a user question and the database schema, produce a single safe SQL query.
Avoid destructive commands (DROP, DELETE, TRUNCATE, ALTER). Only return SQL, nothing else.

Schema:
{schema}

Question: {question}
SQL:"""
        )

    def _conn_kwargs(self) -> dict:
        return {
            "host": self.settings.postgres_host,
            "port": self.settings.postgres_port,
            "user": self.settings.postgres_user,
            "password": self.settings.postgres_password,
            "dbname": self.settings.postgres_db,
        }

    def _load_schema_info(self) -> str:
        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        ORDER BY table_name, ordinal_position
                        """,
                        (self.settings.postgres_schema,),
                    )
                    rows = cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.error("sql_schema_load_error", error=str(exc))
            raise DatabaseError("Failed to load database schema", operation="load_schema") from exc

        schema_lines = []
        current_table = None
        cols: list[str] = []
        for table, col, dtype in rows:
            if table != current_table:
                if current_table:
                    schema_lines.append(f"Table {current_table}({', '.join(cols)})")
                current_table = table
                cols = [f"{col} {dtype}"]
            else:
                cols.append(f"{col} {dtype}")
        if current_table:
            schema_lines.append(f"Table {current_table}({', '.join(cols)})")
        return "\n".join(schema_lines) if schema_lines else ""

    def _validate_question(self, question: str) -> None:
        forbidden = ["drop", "delete", "truncate", "alter"]
        lowered = question.lower()
        if any(word in lowered for word in forbidden):
            raise ValidationError("Destructive SQL operations are not allowed")

    def _generate_sql(self, question: str) -> str:
        messages = self.prompt.format_messages(
            schema=self.schema_info, question=question
        )
        result = self.llm.invoke(messages)
        return result.content.replace("```", "").replace("sql", "", 1).strip().strip("`")

    def _rewrite_sql_for_postgres(self, sql: str) -> str:
        """
        Normalize common MySQL-style functions/columns to our schema.
        """
        rewritten = sql
        rewritten = rewritten.replace("signup_date", "created_at")
        rewritten = rewritten.replace("DATE_SUB(CURDATE(), INTERVAL 7 DAY)", "CURRENT_DATE - INTERVAL '7 days'")
        rewritten = rewritten.replace("CURDATE()", "CURRENT_DATE")
        return rewritten

    def _validate_schema_name(self, schema: str) -> str:
        """
        Validate and sanitize schema name to prevent SQL injection.

        Only allows alphanumeric characters and underscores.
        """
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema):
            raise SQLInjectionError(f"Invalid schema name: {schema}")
        # Use PostgreSQL identifier quoting for safety
        return f'"{schema}"'

    def _validate_sql(self, sql: str) -> None:
        normalized = sql.replace("\n", " ").strip()
        # Allow a single trailing semicolon but forbid multiple statements.
        if normalized.endswith(";"):
            normalized = normalized[:-1].strip()
        parts = [p.strip() for p in normalized.split(";") if p.strip()]
        if len(parts) != 1:
            raise ValidationError("Multiple statements are not allowed")
        lowered = parts[0].lower()
        if not lowered.startswith("select"):
            raise ValidationError("Only SELECT queries are allowed")
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke", "create"]
        if any(word in lowered for word in forbidden):
            raise SQLInjectionError("Destructive SQL operations are not allowed")

    def run_sql(self, question: str) -> str:
        logger.info("postgres_service_run_sql_invoked", question=question)
        self._validate_question(question)
        logger.info("sql_query", question=question)
        try:
            sql = self._generate_sql(question)
            sql = self._rewrite_sql_for_postgres(sql)
            logger.info("sql_generated", sql=sql)
            self._validate_sql(sql)

            # Validate and quote schema name to prevent SQL injection
            safe_schema = self._validate_schema_name(self.settings.postgres_schema)

            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    # Use validated and quoted schema name
                    cur.execute(f"SET search_path TO {safe_schema};")
                    cur.execute(sql)
                    rows = cur.fetchall()
                    col_names = [desc[0] for desc in cur.description] if cur.description else []
        except (ValidationError, SQLInjectionError):
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("sql_error", error=str(exc))
            raise DatabaseError("SQL execution failed", operation="execute_query") from exc

        if not rows:
            return "No results."
        return self._format_rows(rows, col_names, question)

    def healthcheck(self) -> bool:
        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("sql_health_error", error=str(exc))
            return False

    def _format_rows(self, rows, col_names, question: str) -> str:
        cols = col_names or [f"col{i+1}" for i in range(len(rows[0]))]
        # Single scalar
        if len(rows) == 1 and len(rows[0]) == 1:
            return f"Answer: {rows[0][0]}"

        # Otherwise summarize briefly
        as_dicts = [dict(zip(cols, row)) for row in rows]
        if len(as_dicts) == 1:
            return "Answer: " + ", ".join(f"{k}={v}" for k, v in as_dicts[0].items())
        # Multiple rows: short list
        items = ["; ".join(f"{k}={v}" for k, v in row.items()) for row in as_dicts]
        return "Results: " + " | ".join(items)
