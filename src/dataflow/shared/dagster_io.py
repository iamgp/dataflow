"""Dagster IO managers for DataFlow.

This module provides IO managers for Dagster to store and retrieve assets,
particularly with MinIO integration.
"""

import json
import os
import pickle
from datetime import datetime
from typing import Any

import pandas as pd
from dagster import (
    AssetKey,
    ConfigurableIOManager,
    InputContext,
    IOManager,
    MetadataValue,
    OutputContext,
    io_manager,
)

from dataflow.shared.logging import get_logger
from dataflow.shared.minio import get_minio_client, upload_file_with_client

log = get_logger("dataflow.shared.dagster_io")


class MinioIOManager(ConfigurableIOManager):
    """IO manager that stores and retrieves objects in MinIO.

    This IO manager is used to save and load assets from MinIO buckets.
    It handles serialization and deserialization of various data types.
    """

    base_bucket: str = "dagster-assets"
    default_format: str = "json"
    default_content_type: str = "application/json"

    def _get_bucket_and_key(self, context: InputContext | OutputContext) -> tuple[str, str]:
        """Generate bucket name and object key from asset context.

        Args:
            context: The Dagster context

        Returns:
            Tuple containing (bucket_name, object_key)
        """
        if isinstance(context.asset_key, AssetKey):
            asset_path = context.asset_key.path
        else:
            asset_path = context.asset_key

        # The first part is the group name or default to base_bucket
        if len(asset_path) > 1:
            bucket_name = asset_path[0]
        else:
            bucket_name = self.base_bucket

        # The rest forms the object key
        asset_id = "_".join(asset_path)

        # Add partition info if available
        has_partition = hasattr(context, "has_partition_key") and getattr(
            context, "has_partition_key", False
        )
        if has_partition and hasattr(context, "partition_key"):
            object_key = f"{asset_id}/{context.partition_key}.{self.default_format}"
        else:
            now = datetime.now().isoformat().replace(":", "-").replace(".", "-")
            object_key = f"{asset_id}/data_{now}.{self.default_format}"

        return bucket_name, object_key

    def _handle_df(self, df: pd.DataFrame, bucket: str, key: str) -> None:
        """Handle DataFrame storage.

        Args:
            df: The DataFrame to store
            bucket: The bucket name
            key: The object key
        """
        log.info(f"Storing DataFrame in MinIO: {bucket}/{key}")

        # Convert DataFrame to CSV string
        import io

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")

        # Create BytesIO object for MinIO upload
        file_stream = io.BytesIO(csv_bytes)

        # Upload using MinIO client
        client = get_minio_client()
        client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=file_stream,
            length=len(csv_bytes),
            content_type="text/csv",
        )

    def _handle_dict(self, data: dict[str, Any], bucket: str, key: str) -> None:
        """Handle dictionary storage.

        Args:
            data: The dictionary to store
            bucket: The bucket name
            key: The object key
        """
        log.info(f"Storing dictionary as JSON in MinIO: {bucket}/{key}")
        json_str = json.dumps(data)

        import io

        file_stream = io.BytesIO(json_str.encode("utf-8"))

        client = get_minio_client()
        upload_file_with_client(
            client=client,
            bucket_name=bucket,
            object_name=key,
            file_stream=file_stream,
            content_type="application/json",
        )

    def _handle_object(self, obj: Any, bucket: str, key: str) -> None:
        """Handle generic object storage using pickle.

        Args:
            obj: The object to store
            bucket: The bucket name
            key: The object key
        """
        log.info(f"Pickling object to MinIO: {bucket}/{key}")
        import io

        file_stream = io.BytesIO()
        pickle.dump(obj, file_stream)
        file_stream.seek(0)

        client = get_minio_client()
        upload_file_with_client(
            client=client,
            bucket_name=bucket,
            object_name=key,
            file_stream=file_stream,
            content_type="application/octet-stream",
        )

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        """Store an object in MinIO.

        Args:
            context: The output context
            obj: The object to store
        """
        bucket_name, object_key = self._get_bucket_and_key(context)

        # Ensure bucket exists
        client = get_minio_client()
        if not client.bucket_exists(bucket_name):
            log.info(f"Creating MinIO bucket: {bucket_name}")
            client.make_bucket(bucket_name)

        # Handle different data types
        metadata = {}
        if isinstance(obj, pd.DataFrame):
            self._handle_df(obj, bucket_name, object_key)
            # Add metadata about the DataFrame
            metadata = {
                "rows": MetadataValue.int(len(obj)),
                "columns": MetadataValue.json(list(obj.columns)),
                "preview": MetadataValue.md(obj.head().to_markdown() or ""),
                "minio_path": MetadataValue.path(f"minio://{bucket_name}/{object_key}"),
            }
        elif isinstance(obj, dict):
            self._handle_dict(obj, bucket_name, object_key)
            # Add metadata about the dictionary
            metadata = {
                "keys": MetadataValue.json(list(obj.keys())),
                "minio_path": MetadataValue.path(f"minio://{bucket_name}/{object_key}"),
            }
        else:
            self._handle_object(obj, bucket_name, object_key)
            # Add basic metadata
            metadata = {
                "type": MetadataValue.text(type(obj).__name__),
                "minio_path": MetadataValue.path(f"minio://{bucket_name}/{object_key}"),
            }

        # Add metadata to context
        context.add_output_metadata(metadata)

    def load_input(self, context: InputContext) -> Any:
        """Load an object from MinIO.

        Args:
            context: The input context

        Returns:
            The loaded object
        """
        bucket_name, object_key = self._get_bucket_and_key(context)

        client = get_minio_client()
        if not client.bucket_exists(bucket_name):
            raise ValueError(f"Bucket {bucket_name} does not exist")

        # Download the object to a temporary file
        temp_file = f"/tmp/dagster_io_{os.getpid()}_{datetime.now().timestamp()}"
        try:
            client.fget_object(bucket_name, object_key, temp_file)

            # Determine how to load based on file extension
            if object_key.endswith(".csv"):
                return pd.read_csv(temp_file)
            elif object_key.endswith(".json"):
                with open(temp_file) as f:
                    return json.load(f)
            else:
                # Assume it's a pickled object
                with open(temp_file, "rb") as f:
                    return pickle.load(f)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)


@io_manager
def minio_io_manager() -> IOManager:
    """Factory function to create a MinioIOManager.

    Returns:
        An instance of MinioIOManager
    """
    return MinioIOManager()
