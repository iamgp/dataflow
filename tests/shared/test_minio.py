import io
import os
from unittest.mock import MagicMock, patch

import pytest
from minio import Minio

from dataflow.shared.minio import (
    check_bucket_exists,
    create_bucket,
    download_file,
    ensure_bucket_exists,
    get_minio_client,
    upload_file,
    upload_file_with_client,
)


# Make sure the tests don't try to connect to a real Minio instance
@pytest.fixture(autouse=True)
def mock_environ():
    with patch.dict(
        os.environ,
        {
            "MINIO_ENDPOINT": "test-minio:9000",
            "MINIO_ACCESS_KEY": "test-access-key",
            "MINIO_SECRET_KEY": "test-secret-key",
            "MINIO_SECURE": "false",
        },
    ):
        yield


@patch("dataflow.shared.minio.Minio")
def test_get_minio_client(mock_minio):
    """Test that get_minio_client initializes Minio client with correct parameters."""
    # Setup mock
    mock_client = MagicMock()
    mock_minio.return_value = mock_client

    # Call function
    client = get_minio_client()

    # Verify Minio was initialized with the correct parameters
    mock_minio.assert_called_once_with(
        "localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
    )

    # Verify the returned client is our mock
    assert client == mock_client


def test_ensure_bucket_exists_existing_bucket():
    """Test ensure_bucket_exists with an already existing bucket."""
    # Setup mock
    mock_client = MagicMock(spec=Minio)
    mock_client.bucket_exists.return_value = True

    # Call the function
    ensure_bucket_exists(mock_client, "test-bucket")

    # Verify client methods were called correctly
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.make_bucket.assert_not_called()  # Should not be called if bucket exists


def test_ensure_bucket_exists_new_bucket():
    """Test ensure_bucket_exists with a non-existing bucket."""
    # Setup mock
    mock_client = MagicMock(spec=Minio)
    mock_client.bucket_exists.return_value = False

    # Call the function
    ensure_bucket_exists(mock_client, "test-bucket")

    # Verify client methods were called correctly
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.make_bucket.assert_called_once_with("test-bucket")


@patch("dataflow.shared.minio.ensure_bucket_exists")
def test_upload_file_with_file_path(mock_ensure_bucket_exists):
    """Test upload_file function with a file path."""
    # Setup mocks
    mock_client = MagicMock(spec=Minio)

    # Call the function
    upload_file_with_client(
        client=mock_client,
        bucket_name="test-bucket",
        object_name="test-object.txt",
        file_path="/tmp/test-file.txt",
        content_type="text/plain",
    )

    # Verify methods were called correctly
    mock_ensure_bucket_exists.assert_called_once_with(mock_client, "test-bucket")
    mock_client.fput_object.assert_called_once_with(
        "test-bucket", "test-object.txt", "/tmp/test-file.txt", content_type="text/plain"
    )


@patch("dataflow.shared.minio.ensure_bucket_exists")
def test_upload_file_with_file_stream(mock_ensure_bucket_exists):
    """Test upload_file function with a file stream."""
    # Setup mocks
    mock_client = MagicMock(spec=Minio)
    mock_file_stream = io.BytesIO(b"test content")

    # Call the function
    upload_file_with_client(
        client=mock_client,
        bucket_name="test-bucket",
        object_name="test-object.txt",
        file_stream=mock_file_stream,
        content_type="text/plain",
    )

    # Verify methods were called correctly
    mock_ensure_bucket_exists.assert_called_once_with(mock_client, "test-bucket")
    mock_client.put_object.assert_called_once()  # Content length will vary, so just check it was called


def test_download_file():
    """Test download_file function."""
    # Setup mock
    mock_client = MagicMock(spec=Minio)

    # Call the function
    download_file(
        client=mock_client,
        bucket_name="test-bucket",
        object_name="test-object.txt",
        file_path="/tmp/downloaded.txt",
    )

    # Verify client methods were called correctly
    mock_client.fget_object.assert_called_once_with(
        "test-bucket", "test-object.txt", "/tmp/downloaded.txt"
    )


@patch("dataflow.shared.minio.get_minio_client")
def test_check_bucket_exists(mock_get_client):
    """Test that check_bucket_exists calls Minio client correctly."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.bucket_exists.return_value = True

    # Call function
    result = check_bucket_exists("test-bucket")

    # Verify client method called with correct bucket
    mock_client.bucket_exists.assert_called_once_with("test-bucket")

    # Verify result matches mock return
    assert result is True


@patch("dataflow.shared.minio.get_minio_client")
def test_create_bucket(mock_get_client):
    """Test that create_bucket calls Minio client correctly."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.bucket_exists.return_value = False

    # Call function
    create_bucket("test-bucket")

    # Verify bucket existence was checked
    mock_client.bucket_exists.assert_called_once_with("test-bucket")

    # Verify bucket was created
    mock_client.make_bucket.assert_called_once_with("test-bucket")


@patch("dataflow.shared.minio.get_minio_client")
def test_create_bucket_already_exists(mock_get_client):
    """Test that create_bucket doesn't create a bucket if it already exists."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.bucket_exists.return_value = True

    # Call function
    create_bucket("test-bucket")

    # Verify bucket existence was checked
    mock_client.bucket_exists.assert_called_once_with("test-bucket")

    # Verify bucket was not created
    mock_client.make_bucket.assert_not_called()


@patch("dataflow.shared.minio.get_minio_client")
def test_upload_file(mock_get_client):
    """Test that upload_file calls Minio client correctly."""
    # Setup mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Test file path and content
    test_file_path = "test_file.txt"

    # Create test file
    with open(test_file_path, "w") as f:
        f.write("test data")

    try:
        # Call function
        upload_file("test-bucket", "test/object/path.txt", test_file_path)

        # Verify fput_object was called with correct parameters
        mock_client.fput_object.assert_called_once_with(
            "test-bucket",
            "test/object/path.txt",
            test_file_path,
            content_type="application/octet-stream",
        )
    finally:
        # Clean up test file
        os.remove(test_file_path)
