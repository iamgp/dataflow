import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import duckdb
import pytest

from dataflow.shared.db import execute_query, fetch_one_query, fetch_query, get_db_connection


# Make sure the tests don't try to connect to a real database
@pytest.fixture(autouse=True)
def mock_environ():
    with patch.dict(os.environ, {"DUCKDB_DATABASE_PATH": "test_database.db"}):
        yield


@contextmanager
def mock_duckdb_connection():
    """Mock DuckDB connection for testing."""
    mock_conn = MagicMock(spec=duckdb.DuckDBPyConnection)
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("test_data",)]
    mock_cursor.fetchone.return_value = ("test_data",)

    yield mock_conn


@pytest.fixture
def mock_conn():
    """Create a mock database connection."""
    conn = MagicMock(spec=duckdb.DuckDBPyConnection)
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@patch("os.makedirs")
@patch("duckdb.connect")
def test_get_db_connection(mock_connect, mock_makedirs):
    """Test that get_db_connection manages connections correctly."""
    # Setup mock
    mock_connection = MagicMock(spec=duckdb.DuckDBPyConnection)
    mock_connect.return_value = mock_connection

    # Use the context manager
    with get_db_connection() as conn:
        # Verify connection was made with correct parameters
        mock_connect.assert_called_once_with(
            database=os.path.join(os.getcwd(), "data", "dataflow.db"), read_only=False
        )
        # Verify we got the mocked connection back
        assert conn == mock_connection

    # Verify connection was closed
    mock_connection.close.assert_called_once()

    # Verify directory was created
    mock_makedirs.assert_called_once()


@patch("dataflow.shared.db.get_db_connection")
def test_execute_query(mock_get_conn, mock_conn):
    """Test execute_query function works correctly."""
    conn, cursor = mock_conn
    mock_get_conn.return_value.__enter__.return_value = conn

    # Call the function
    execute_query("CREATE TABLE test (id INTEGER)", params={"param1": "value1"})

    # Verify query was executed with parameters
    conn.execute.assert_called_once_with("CREATE TABLE test (id INTEGER)", {"param1": "value1"})


@patch("dataflow.shared.db.get_db_connection")
def test_fetch_query(mock_get_conn, mock_conn):
    """Test fetch_query function returns query results."""
    conn, cursor = mock_conn
    mock_get_conn.return_value.__enter__.return_value = conn

    # Setup return value
    conn.execute.return_value.fetchall.return_value = [{"id": 1}, {"id": 2}]

    # Call the function
    result = fetch_query("SELECT * FROM test", params={"param1": "value1"})

    # Verify query was executed and results returned
    conn.execute.assert_called_once_with("SELECT * FROM test", {"param1": "value1"})
    assert result == [{"id": 1}, {"id": 2}]


@patch("dataflow.shared.db.get_db_connection")
def test_fetch_one_query(mock_get_conn, mock_conn):
    """Test fetch_one_query function returns a single result."""
    conn, cursor = mock_conn
    mock_get_conn.return_value.__enter__.return_value = conn

    # Setup return value
    conn.execute.return_value.fetchone.return_value = {"id": 1}

    # Call the function
    result = fetch_one_query("SELECT * FROM test WHERE id = ?", params={"param1": "value1"})

    # Verify query was executed and results returned
    conn.execute.assert_called_once_with("SELECT * FROM test WHERE id = ?", {"param1": "value1"})
    assert result == {"id": 1}
