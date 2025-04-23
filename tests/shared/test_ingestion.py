"""Tests for shared ingestion utilities.

This module tests the shared ingestion utilities including base classes,
API clients, and file operations.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from dataflow.shared.ingestion import (
    AuthenticationError,
    BaseAPIClient,
    BaseDataIngestion,
    DataIngestionError,
    RateLimitError,
    ResourceNotFoundError,
    RetryConfig,
    read_csv_as_dataframe,
    read_csv_file,
    read_json_file,
    save_to_local_file,
    save_to_minio,
)

# Test Data
SAMPLE_JSON = {"key": "value", "nested": {"inner": "data"}}
SAMPLE_CSV = "id,name\n1,test1\n2,test2"
SAMPLE_CSV_DICT = [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}]


# Fixtures
@pytest.fixture
def sample_json_file(tmp_path):
    """Create a sample JSON file for testing."""
    file_path = tmp_path / "test.json"
    with open(file_path, "w") as f:
        json.dump(SAMPLE_JSON, f)
    return file_path


@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a sample CSV file for testing."""
    file_path = tmp_path / "test.csv"
    with open(file_path, "w") as f:
        f.write(SAMPLE_CSV)
    return file_path


# Mock Classes for Testing
class MockSource:
    """Mock source for testing BaseDataIngestion."""

    def extract(self) -> Iterable[Any]:
        return [1, 2, 3]


class MockProcessor:
    """Mock processor for testing BaseDataIngestion."""

    def process(self, data: int) -> str:
        return f"processed_{data}"


class MockSink:
    """Mock sink for testing BaseDataIngestion."""

    def store(self, data: str) -> None:
        pass


class TestIngestion(BaseDataIngestion[int, str]):
    """Test implementation of BaseDataIngestion."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.source = MockSource()
        self.processor = MockProcessor()
        self.sink = MockSink()

    def extract(self) -> Iterable[int]:
        return self.source.extract()

    def process(self, data: int) -> str:
        return self.processor.process(data)

    def store(self, data: str) -> None:
        self.sink.store(data)


# Tests for Base Classes
class TestBaseDataIngestion:
    """Tests for the BaseDataIngestion class."""

    def test_successful_ingestion(self):
        """Test successful ingestion workflow."""
        config = {"test": "config"}
        ingestion = TestIngestion(config)

        with (
            patch.object(MockSource, "extract") as mock_extract,
            patch.object(MockProcessor, "process") as mock_process,
            patch.object(MockSink, "store") as mock_store,
        ):
            mock_extract.return_value = [1, 2, 3]
            mock_process.side_effect = lambda x: f"processed_{x}"

            ingestion.run()

            assert mock_extract.called
            assert mock_process.call_count == 3
            assert mock_store.call_count == 3

    def test_extraction_error(self):
        """Test handling of extraction errors."""
        config = {"test": "config"}
        ingestion = TestIngestion(config)

        with patch.object(MockSource, "extract") as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")

            with pytest.raises(DataIngestionError) as exc_info:
                ingestion.run()

            assert "Extraction failed" in str(exc_info.value)

    def test_processing_error(self):
        """Test handling of processing errors."""
        config = {"test": "config"}
        ingestion = TestIngestion(config)

        with (
            patch.object(MockSource, "extract") as mock_extract,
            patch.object(MockProcessor, "process") as mock_process,
            patch.object(ingestion, "handle_item_error") as mock_handle_error,
        ):
            mock_extract.return_value = [1, 2, 3]
            mock_process.side_effect = Exception("Processing failed")

            ingestion.run()

            assert mock_handle_error.call_count == 3


# Tests for File Operations
def test_read_json_file(sample_json_file):
    """Test reading JSON file."""
    result = read_json_file(sample_json_file)
    assert result == SAMPLE_JSON


def test_read_csv_file(sample_csv_file):
    """Test reading CSV file as list of dictionaries."""
    result = read_csv_file(sample_csv_file)
    assert result == SAMPLE_CSV_DICT


def test_read_csv_as_dataframe(sample_csv_file):
    """Test reading CSV file as pandas DataFrame."""
    result = read_csv_as_dataframe(sample_csv_file)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == ["id", "name"]


@patch("dataflow.shared.ingestion.get_minio_client")
def test_save_to_minio(mock_get_client):
    """Test saving data to MinIO."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    data = {"test": "data"}
    bucket_name = "test-bucket"
    object_name = "test/object.json"

    result = save_to_minio(bucket_name, data, object_name)

    assert result == object_name
    assert len(mock_client.put_object.call_args_list) == 1
    args = mock_client.put_object.call_args_list[0][0]
    kwargs = mock_client.put_object.call_args_list[0][1]
    print(args)
    assert kwargs["bucket_name"] == bucket_name
    assert kwargs["object_name"] == object_name
    assert kwargs["content_type"] == "application/json"

    # Verify the uploaded content was valid JSON
    file_stream = kwargs["data"]
    uploaded_data = json.loads(file_stream.getvalue().decode("utf-8"))
    assert uploaded_data == data


def test_save_to_local_file(tmp_path):
    """Test saving data to local file."""
    file_path = tmp_path / "test_output.json"
    data = {"test": "data"}

    result = save_to_local_file(data, file_path)

    assert Path(result).exists()
    with open(result) as f:
        saved_data = json.load(f)
    assert saved_data == data


# Tests for API Client
class TestBaseAPIClient:
    """Tests for the BaseAPIClient class."""

    @pytest.fixture
    def api_client(self):
        """Create a test API client."""
        return BaseAPIClient(
            base_url="https://api.test.com",
            headers={"Authorization": "Bearer test"},
            retry_config=RetryConfig(max_retries=2),
        )

    def test_build_url(self, api_client):
        """Test URL building."""
        url = api_client._build_url("/endpoint")
        assert url == "https://api.test.com/endpoint"

    def test_handle_response_success(self, api_client):
        """Test successful response handling."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        result = api_client.handle_response(mock_response)
        assert result == {"data": "test"}

    def test_handle_response_rate_limit(self, api_client):
        """Test rate limit response handling."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 429

        with pytest.raises(RateLimitError):
            api_client.handle_response(mock_response)

    def test_handle_response_auth_error(self, api_client):
        """Test authentication error handling."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 401

        with pytest.raises(AuthenticationError):
            api_client.handle_response(mock_response)

    def test_handle_response_not_found(self, api_client):
        """Test not found error handling."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 404

        with pytest.raises(ResourceNotFoundError):
            api_client.handle_response(mock_response)

    @patch("requests.get")
    def test_get_request_success(self, mock_get, api_client):
        """Test successful GET request."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = api_client.get("/test")
        assert result == {"data": "test"}

    @patch("requests.get")
    def test_get_request_retry(self, mock_get, api_client):
        """Test GET request with retry on failure."""
        mock_response_fail = MagicMock(spec=requests.Response)
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock(spec=requests.Response)
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "test"}

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        result = api_client.get("/test")
        assert result == {"data": "test"}
        assert mock_get.call_count == 2
