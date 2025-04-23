"""Tests for shared Dagster IO utilities.

This module tests the shared Dagster IO utilities, particularly the MinIO integration
for storing and retrieving assets.
"""

import json
import pickle
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from dagster import AssetKey, InputContext, OutputContext

from dataflow.shared.dagster_io import MinioIOManager, minio_io_manager

# Test Data
SAMPLE_DF = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"]})

SAMPLE_DICT = {"key1": "value1", "key2": "value2"}

SAMPLE_OBJECT = ["test", 123, {"nested": "data"}]


# Mock Contexts
def create_output_context(asset_key: list[str], partition_key: str | None = None) -> OutputContext:
    """Create a mock output context."""
    context = MagicMock()
    context.asset_key = AssetKey(asset_key)
    context.has_partition_key = partition_key is not None
    if partition_key:
        context.partition_key = partition_key
    return context


def create_input_context(asset_key: list[str], partition_key: str | None = None) -> InputContext:
    """Create a mock input context."""
    context = MagicMock()
    context.asset_key = AssetKey(asset_key)
    context.has_partition_key = partition_key is not None
    if partition_key:
        context.partition_key = partition_key
    return context


# Tests
class TestMinioIOManager:
    """Tests for the MinioIOManager class."""

    @pytest.fixture
    def io_manager(self):
        """Create a MinioIOManager instance."""
        return MinioIOManager()

    def test_get_bucket_and_key_simple(self, io_manager):
        """Test bucket and key generation for simple asset key."""
        context = create_output_context(["test_asset"])
        bucket, key = io_manager._get_bucket_and_key(context)

        assert bucket == "dagster-assets"
        assert key.startswith("test_asset/data_")
        assert key.endswith(".json")

    def test_get_bucket_and_key_group(self, io_manager):
        """Test bucket and key generation with group."""
        context = create_output_context(["my_group", "test_asset"])
        bucket, key = io_manager._get_bucket_and_key(context)

        assert bucket == "my_group"
        assert key.startswith("my_group_test_asset/data_")
        assert key.endswith(".json")

    def test_get_bucket_and_key_partition(self, io_manager):
        """Test bucket and key generation with partition."""
        context = create_output_context(["test_asset"], partition_key="2024-01-01")
        bucket, key = io_manager._get_bucket_and_key(context)

        assert bucket == "dagster-assets"
        assert key == "test_asset/2024-01-01.json"

    @patch("dataflow.shared.dagster_io.get_minio_client")
    def test_handle_df(self, mock_get_client, io_manager):
        """Test DataFrame handling."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        io_manager._handle_df(SAMPLE_DF, "test-bucket", "test/key.csv")

        # Verify upload_dataframe was called with correct arguments
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args.kwargs["bucket_name"] == "test-bucket"
        assert call_args.kwargs["object_name"] == "test/key.csv"
        assert call_args.kwargs["content_type"] == "text/csv"

    @patch("dataflow.shared.dagster_io.get_minio_client")
    def test_handle_dict(self, mock_get_client, io_manager):
        """Test dictionary handling."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        io_manager._handle_dict(SAMPLE_DICT, "test-bucket", "test/key.json")

        # Verify upload was called with correct arguments
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args.args[0] == "test-bucket"
        assert call_args.args[1] == "test/key.json"
        assert call_args.kwargs["content_type"] == "application/json"

        # Verify the uploaded content was valid JSON
        file_stream = call_args.args[2]  # The file stream is the third positional argument
        uploaded_data = json.loads(file_stream.getvalue().decode("utf-8"))
        assert uploaded_data == SAMPLE_DICT

    @patch("dataflow.shared.dagster_io.get_minio_client")
    def test_handle_object(self, mock_get_client, io_manager):
        """Test generic object handling."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        io_manager._handle_object(SAMPLE_OBJECT, "test-bucket", "test/key.pkl")

        # Verify upload was called with correct arguments
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args.args[0] == "test-bucket"
        assert call_args.args[1] == "test/key.pkl"
        assert call_args.kwargs["content_type"] == "application/octet-stream"

        # Verify the uploaded content was valid pickle
        file_stream = call_args.args[2]  # The file stream is the third positional argument
        uploaded_data = pickle.loads(file_stream.getvalue())
        assert uploaded_data == SAMPLE_OBJECT

    # @patch("dataflow.shared.dagster_io.get_minio_client")
    # def test_handle_output_dataframe(self, mock_get_client, io_manager):
    #     """Test output handling for DataFrame."""
    #     mock_client = MagicMock()
    #     mock_get_client.return_value = mock_client
    #     mock_client.bucket_exists.return_value = True

    #     context = create_output_context(["test_asset"])
    #     io_manager.handle_output(context, SAMPLE_DF)

    #     # Verify metadata was added
    #     assert context.add_output_metadata.called
    #     call = context.add_output_metadata.call_args_list[0]
    #     metadata = call[1]["metadata"]
    #     assert metadata["rows"].value == len(SAMPLE_DF)
    #     assert metadata["columns"].value == list(SAMPLE_DF.columns)

    # @patch("dataflow.shared.dagster_io.get_minio_client")
    # def test_handle_output_dict(self, mock_get_client, io_manager):
    #     """Test output handling for dictionary."""
    #     mock_client = MagicMock()
    #     mock_get_client.return_value = mock_client
    #     mock_client.bucket_exists.return_value = True

    #     context = create_output_context(["test_asset"])
    #     io_manager.handle_output(context, SAMPLE_DICT)

    #     # Verify metadata was added
    #     assert context.add_output_metadata.called
    #     call = context.add_output_metadata.call_args_list[0]
    #     metadata = call[1]["metadata"]
    #     assert metadata["keys"].value == list(SAMPLE_DICT.keys())

    # @patch("dataflow.shared.dagster_io.get_minio_client")
    # def test_handle_output_object(self, mock_get_client, io_manager):
    #     """Test output handling for generic object."""
    #     mock_client = MagicMock()
    #     mock_get_client.return_value = mock_client
    #     mock_client.bucket_exists.return_value = True

    #     context = create_output_context(["test_asset"])
    #     io_manager.handle_output(context, SAMPLE_OBJECT)

    #     # Verify metadata was added
    #     assert context.add_output_metadata.called
    #     call = context.add_output_metadata.call_args_list[0]
    #     metadata = call[1]["metadata"]
    #     assert metadata["type"].value == type(SAMPLE_OBJECT).__name__

    # @patch("dataflow.shared.dagster_io.get_minio_client")
    # def test_handle_output_new_bucket(self, mock_get_client, io_manager):
    #     """Test output handling with new bucket creation."""
    #     mock_client = MagicMock()
    #     mock_get_client.return_value = mock_client
    #     mock_client.bucket_exists.return_value = False

    #     context = create_output_context(["test_asset"])
    #     io_manager.handle_output(context, SAMPLE_DICT)

    #     # Verify bucket was created exactly once
    #     mock_client.make_bucket.assert_called_once()
    #     call_args = mock_client.make_bucket.call_args
    #     assert call_args.args[0] == "dagster-assets"

    @patch("dataflow.shared.dagster_io.get_minio_client")
    def test_load_input_missing_bucket(self, mock_get_client, io_manager):
        """Test input loading with missing bucket."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.bucket_exists.return_value = False

        context = create_input_context(["test_asset"])
        with pytest.raises(ValueError, match="Bucket .* does not exist"):
            io_manager.load_input(context)

    @patch("dataflow.shared.dagster_io.get_minio_client")
    def test_save_to_minio(self, mock_get_client, io_manager):
        """Test saving to MinIO."""
        # Set up mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Set up mock context
        context = MagicMock()
        context.asset_key = ["test_asset"]

        # Get bucket and key
        bucket, key = io_manager._get_bucket_and_key(context)

        # Execute the function
        io_manager.handle_output(context, SAMPLE_DF)

        # Verify put_object was called with correct arguments
        mock_client.put_object.assert_called_once()
        put_object_args = mock_client.put_object.call_args
        assert put_object_args.kwargs["bucket_name"] == bucket
        assert put_object_args.kwargs["object_name"] == key
        assert put_object_args.kwargs["content_type"] == "text/csv"

        # Verify metadata was added
        # assert context.add_output_metadata.called
        # call = context.add_output_metadata.call_args_list[0]
        # metadata = call[1]["metadata"]
        # assert metadata["rows"].value == len(SAMPLE_DF)
        # assert metadata["columns"].value == list(SAMPLE_DF.columns)


def test_minio_io_manager_factory():
    """Test the minio_io_manager factory function."""
    manager = minio_io_manager()
    assert isinstance(manager, MinioIOManager)
