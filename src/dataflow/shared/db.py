import os
from collections.abc import Generator
from contextlib import contextmanager

import duckdb

DATABASE_PATH = os.environ.get("DUCKDB_DATABASE_PATH", "data/dataflow.db")


@contextmanager
def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for DuckDB connections."""
    connection = None
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        connection = duckdb.connect(database=DATABASE_PATH, read_only=False)
        yield connection
    except duckdb.Error as e:
        # Consider adding more specific error handling and logging
        print(f"Database connection error: {e}")
        raise
    finally:
        if connection:
            connection.close()


def execute_query(query: str, params: tuple | None = None) -> None:
    """Executes a write query (INSERT, UPDATE, DELETE, CREATE)."""
    with get_db_connection() as conn:
        conn.execute(query, params)


def fetch_query(query: str, params: tuple | None = None) -> list[tuple]:
    """Executes a read query (SELECT) and fetches all results."""
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchall()


def fetch_one_query(query: str, params: tuple | None = None) -> tuple | None:
    """Executes a read query (SELECT) and fetches one result."""
    with get_db_connection() as conn:
        return conn.execute(query, params).fetchone()
