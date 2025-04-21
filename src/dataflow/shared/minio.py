import os
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

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
        return client
    except S3Error as e:
        print(f"Error connecting to Minio: {e}")
        raise
    except Exception as e:
        # Catch potential issues like DNS resolution errors
        print(f"Could not initialize Minio client: {e}")
        raise


def ensure_bucket_exists(client: Minio, bucket_name: str) -> None:
    """Creates a bucket if it does not already exist."""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as e:
        print(f"Error checking/creating bucket '{bucket_name}': {e}")
        raise


def upload_file(
    client: Minio,
    bucket_name: str,
    object_name: str,
    file_path: str | None = None,
    file_stream: BinaryIO | None = None,
    content_type: str = "application/octet-stream",
) -> None:
    """Uploads a file or stream to a Minio bucket."""
    ensure_bucket_exists(client, bucket_name)
    try:
        if file_path:
            client.fput_object(bucket_name, object_name, file_path, content_type=content_type)
            print(
                f"'{file_path}' successfully uploaded as '{object_name}' to bucket '{bucket_name}'."
            )
        elif file_stream:
            # Get stream size (required by put_object)
            file_stream.seek(0, os.SEEK_END)
            stream_size = file_stream.tell()
            file_stream.seek(0)
            client.put_object(
                bucket_name, object_name, file_stream, stream_size, content_type=content_type
            )
            print(f"Stream successfully uploaded as '{object_name}' to bucket '{bucket_name}'.")
        else:
            raise ValueError("Either file_path or file_stream must be provided.")

    except S3Error as e:
        print(f"Error uploading object '{object_name}' to bucket '{bucket_name}': {e}")
        raise


def download_file(client: Minio, bucket_name: str, object_name: str, file_path: str) -> None:
    """Downloads an object from a Minio bucket to a local file."""
    try:
        client.fget_object(bucket_name, object_name, file_path)
        print(f"Object '{object_name}' from bucket '{bucket_name}' downloaded to '{file_path}'.")
    except S3Error as e:
        print(f"Error downloading object '{object_name}' from bucket '{bucket_name}': {e}")
        raise


def list_objects(client: Minio, bucket_name: str, prefix: str | None = None) -> list[str]:
    """Lists objects in a Minio bucket, optionally filtered by prefix."""
    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects if obj.object_name is not None]
    except S3Error as e:
        print(f"Error listing objects in bucket '{bucket_name}': {e}")
        raise  # Or return empty list?
