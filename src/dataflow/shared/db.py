import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

"""
Database utilities for connecting to and querying DuckDB databases.

This module provides a connection context manager and helper functions
for common database operations using DuckDB.
"""

import duckdb

from dataflow.shared.logging import get_logger

log = get_logger("dataflow.shared.db")

# Validate and set database path
DATABASE_PATH = os.path.abspath(os.environ.get("DUCKDB_DATABASE_PATH", "data/dataflow.db"))


@contextmanager
def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for DuckDB connections."""
    connection = None
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        connection = duckdb.connect(database=DATABASE_PATH, read_only=False)
        yield connection
    except duckdb.Error as e:
        # Log using structlog for consistent error reporting
        log.error("Database connection error", error=str(e))
        raise
    finally:
        if connection:
            connection.close()


def execute_query(query: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> None:
    """Executes a write query (INSERT, UPDATE, DELETE, CREATE)."""
    with get_db_connection() as conn:
        # Optional: Add transaction support
        # conn.execute("BEGIN")
        conn.execute(query, params)
        # conn.execute("COMMIT")


def fetch_query(
    query: str, params: tuple[Any, ...] | dict[str, Any] | None = None
) -> list[tuple[Any, ...]]:
    """Executes a read query (SELECT) and fetches all results."""
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchall()


def fetch_one_query(
    query: str, params: tuple[Any, ...] | dict[str, Any] | None = None
) -> tuple[Any, ...] | None:
    """Executes a read query (SELECT) and fetches one result."""
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchone()
