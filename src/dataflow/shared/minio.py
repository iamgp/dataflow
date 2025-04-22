import io
import os
from typing import BinaryIO

import pandas as pd
from minio import Minio
from minio.error import S3Error

from dataflow.shared.logging import get_logger

log = get_logger("dataflow.shared.minio")

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"


def get_minio_client() -> Minio:
    """Initializes and returns a Minio client."""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        # Ping the server to check connectivity
        client.list_buckets()
        log.info("Successfully connected to MinIO", endpoint=MINIO_ENDPOINT, secure=MINIO_SECURE)
        return client
    except S3Error as e:
        log.error("Error connecting to MinIO", error=str(e), endpoint=MINIO_ENDPOINT)
        raise
    except Exception as e:
        # Catch potential issues like DNS resolution errors
        log.error("Could not initialize MinIO client", error=str(e), endpoint=MINIO_ENDPOINT)
        raise


def ensure_bucket_exists(client: Minio, bucket_name: str) -> None:
    """Creates a bucket if it does not already exist."""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            log.info("Bucket created", bucket_name=bucket_name)
        else:
            log.debug("Bucket already exists", bucket_name=bucket_name)
    except S3Error as e:
        log.error("Error checking/creating bucket", bucket_name=bucket_name, error=str(e))
        raise


def upload_file_with_client(
    client: Minio,
    bucket_name: str,
    object_name: str,
    file_path: str | None = None,
    file_stream: BinaryIO | None = None,
    content_type: str = "application/octet-stream",
) -> None:
    """Uploads a file or stream to a Minio bucket.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the bucket to upload to
        object_name: Name to give the object in the bucket
        file_path: Local path to the file to upload (mutually exclusive with file_stream)
        file_stream: Binary file-like object to upload (mutually exclusive with file_path)
        content_type: MIME type of the file

    Raises:
        ValueError: If neither file_path nor file_stream is provided
        S3Error: If there's an error during S3 operations
    """
    if not bucket_name or not object_name:
        raise ValueError("bucket_name and object_name must not be empty")

    ensure_bucket_exists(client, bucket_name)
    try:
        if file_path:
            client.fput_object(bucket_name, object_name, file_path, content_type=content_type)
            log.info(
                "File successfully uploaded",
                file_path=file_path,
                object_name=object_name,
                bucket_name=bucket_name,
            )
        elif file_stream:
            # Get stream size (required by put_object)
            file_stream.seek(0, os.SEEK_END)
            stream_size = file_stream.tell()
            file_stream.seek(0)
            client.put_object(
                bucket_name, object_name, file_stream, stream_size, content_type=content_type
            )
            log.info(
                "Stream successfully uploaded",
                object_name=object_name,
                bucket_name=bucket_name,
                size_bytes=stream_size,
            )
        else:
            raise ValueError("Either file_path or file_stream must be provided.")

    except S3Error as e:
        log.error(
            "Error uploading object",
            object_name=object_name,
            bucket_name=bucket_name,
            error=str(e),
        )
        raise


def upload_file(bucket_name: str, object_name: str, file_path: str) -> None:
    """Uploads a file to a Minio bucket.

    Args:
        bucket_name: Name of the bucket to upload to
        object_name: Name to give the object in the bucket
        file_path: Local path to the file to upload

    Raises:
        S3Error: If there's an error during S3 operations
    """
    client = get_minio_client()
    upload_file_with_client(
        client=client, bucket_name=bucket_name, object_name=object_name, file_path=file_path
    )


def download_file(client: Minio, bucket_name: str, object_name: str, file_path: str) -> None:
    """Downloads an object from a Minio bucket to a local file.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the bucket containing the object
        object_name: Name of the object to download
        file_path: Local path where the object will be saved

    Raises:
        S3Error: If there's an error during S3 operations
    """
    if not bucket_name or not object_name or not file_path:
        raise ValueError("bucket_name, object_name, and file_path must not be empty")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    try:
        client.fget_object(bucket_name, object_name, file_path)
        log.info(
            "Object successfully downloaded",
            object_name=object_name,
            bucket_name=bucket_name,
            file_path=file_path,
        )
    except S3Error as e:
        log.error(
            "Error downloading object",
            object_name=object_name,
            bucket_name=bucket_name,
            file_path=file_path,
            error=str(e),
        )
        raise


def list_objects(client: Minio, bucket_name: str, prefix: str | None = None) -> list[str]:
    """Lists objects in a Minio bucket, optionally filtered by prefix.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the bucket to list objects from
        prefix: Optional prefix to filter objects by

    Returns:
        List of object names in the bucket

    Raises:
        S3Error: If there's an error during S3 operations
    """
    if not bucket_name:
        raise ValueError("bucket_name must not be empty")

    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        result = [obj.object_name for obj in objects if obj.object_name is not None]
        log.debug(
            "Objects listed successfully",
            bucket_name=bucket_name,
            prefix=prefix,
            count=len(result),
        )
        return result
    except S3Error as e:
        log.error(
            "Error listing objects",
            bucket_name=bucket_name,
            prefix=prefix,
            error=str(e),
        )
        raise  # Raising the exception is better for error handling than returning an empty list


def check_bucket_exists(bucket_name: str) -> bool:
    """Checks if a bucket exists in Minio.

    Args:
        bucket_name: Name of the bucket to check

    Returns:
        True if the bucket exists, False otherwise

    Raises:
        S3Error: If there's an error during S3 operations
    """
    if not bucket_name:
        raise ValueError("bucket_name must not be empty")

    try:
        client = get_minio_client()
        exists = client.bucket_exists(bucket_name)
        log.debug("Bucket existence checked", bucket_name=bucket_name, exists=exists)
        return exists
    except S3Error as e:
        log.error("Error checking bucket existence", bucket_name=bucket_name, error=str(e))
        raise


def create_bucket(bucket_name: str) -> None:
    """Creates a bucket in Minio if it doesn't already exist.

    Args:
        bucket_name: Name of the bucket to create

    Raises:
        S3Error: If there's an error during S3 operations
    """
    if not bucket_name:
        raise ValueError("bucket_name must not be empty")

    try:
        client = get_minio_client()
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            log.info("Bucket created", bucket_name=bucket_name)
        else:
            log.debug("Bucket already exists", bucket_name=bucket_name)
    except S3Error as e:
        log.error("Error creating bucket", bucket_name=bucket_name, error=str(e))
        raise


def upload_dataframe(
    df: pd.DataFrame,
    bucket_name: str,
    object_name: str,
    content_type: str = "text/csv",
    index: bool = False,
) -> None:
    """Uploads a pandas DataFrame to a Minio bucket.

    Args:
        df: Pandas DataFrame to upload
        bucket_name: Name of the bucket to upload to
        object_name: Name to give the object in the bucket
        content_type: MIME type of the file (default: 'text/csv')
        index: Whether to include index in the CSV output (default: False)

    Raises:
        S3Error: If there's an error during S3 operations
    """
    # Create a buffer for the CSV content
    buffer = io.StringIO()
    df.to_csv(buffer, index=index)

    # Convert to bytes for upload
    bytes_content = buffer.getvalue().encode("utf-8")
    bytes_stream = io.BytesIO(bytes_content)

    # Upload to Minio
    client = get_minio_client()
    upload_file_with_client(
        client=client,
        bucket_name=bucket_name,
        object_name=object_name,
        file_stream=bytes_stream,
        content_type=content_type,
    )

    log.info(
        "DataFrame successfully uploaded",
        bucket_name=bucket_name,
        object_name=object_name,
        rows=len(df),
        columns=len(df.columns),
    )
