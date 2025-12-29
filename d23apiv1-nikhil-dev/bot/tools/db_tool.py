"""
Postgres DB Tool

Connects to a PostgreSQL database and executes SQL queries.
"""

import asyncio
from typing import Optional, List, Dict, Any
import json
import psycopg2
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from bot.config import get_settings
from bot.state import ToolResult


# Helper function to build LLM
def build_chat_llm(settings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )


class PostgresService:
    def __init__(self, settings):
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
            "host": self.settings.POSTGRES_HOST,
            "port": self.settings.POSTGRES_PORT,
            "user": self.settings.POSTGRES_USER,
            "password": self.settings.POSTGRES_PASSWORD,
            "dbname": self.settings.POSTGRES_DB,
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
                        (self.settings.POSTGRES_SCHEMA,),
                    )
                    rows = cur.fetchall()
        except Exception as exc:
            raise Exception("Failed to load database schema") from exc

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
            raise Exception("Destructive SQL operations are not allowed")

    def _generate_sql(self, question: str) -> str:
        messages = self.prompt.format_messages(
            schema=self.schema_info, question=question
        )
        result = self.llm.invoke(messages)
        return result.content.replace("```", "").replace("sql", "", 1).strip().strip("`")

    def _rewrite_sql_for_postgres(self, sql: str) -> str:
        rewritten = sql
        rewritten = rewritten.replace("signup_date", "created_at")
        rewritten = rewritten.replace("DATE_SUB(CURDATE(), INTERVAL 7 DAY)", "CURRENT_DATE - INTERVAL '7 days'")
        rewritten = rewritten.replace("CURDATE()", "CURRENT_DATE")
        return rewritten

    def _validate_sql(self, sql: str) -> None:
        normalized = sql.replace("\n", " ").strip()
        if normalized.endswith(";"):
            normalized = normalized[:-1].strip()
        parts = [p.strip() for p in normalized.split(";") if p.strip()]
        if len(parts) != 1:
            raise Exception("Multiple statements are not allowed")
        lowered = parts[0].lower()
        if not lowered.startswith("select"):
            raise Exception("Only SELECT queries are allowed")
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
        if any(word in lowered for word in forbidden):
            raise Exception("Destructive SQL operations are not allowed")

    def run_sql(self, question: str) -> str:
        self._validate_question(question)
        try:
            sql = self._generate_sql(question)
            sql = self._rewrite_sql_for_postgres(sql)
            self._validate_sql(sql)
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {self.settings.POSTGRES_SCHEMA};")
                    cur.execute(sql)
                    rows = cur.fetchall()
                    col_names = [desc[0] for desc in cur.description] if cur.description else []
        except Exception as exc:
            raise Exception(f"SQL execution failed: {exc}") from exc

        if not rows:
            return "No results."
        return self._format_rows(rows, col_names, question)

    def healthcheck(self) -> bool:
        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as exc:
            return False

    def _format_rows(self, rows: List[Any], col_names: List[str], question: str) -> str:
        cols = col_names or [f"col{i+1}" for i in range(len(rows[0]))]
        if len(rows) == 1 and len(rows[0]) == 1:
            return f"Answer: {rows[0][0]}"

        as_dicts = [dict(zip(cols, row)) for row in rows]
        if len(as_dicts) == 1:
            return "Answer: " + ", ".join(f"{k}={v}" for k, v in as_dicts[0].items())
        items = ["; ".join(f"{k}={v}" for k, v in row.items()) for row in as_dicts]
        return "Results: " + " | ".join(items)


async def query_db(question: str) -> ToolResult:
    """
    Queries the PostgreSQL database using a natural language question.

    Args:
        question: The natural language question to convert to SQL.

    Returns:
        A ToolResult with the query results or an error.
    """
    try:
        settings = get_settings()
        db_service = PostgresService(settings)
        result = await asyncio.to_thread(db_service.run_sql, question)
        return ToolResult(
            success=True,
            data={"result": result},
            error=None,
            tool_name="db_query",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="db_query",
        )