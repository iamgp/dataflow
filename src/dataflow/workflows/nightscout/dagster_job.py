"""Dagster job definition for the Nightscout workflow."""

import json
import os
from datetime import datetime
from typing import Any

from dagster import (
    AssetMaterialization,
    ConfigurableResource,
    OpExecutionContext,
    job,
    op,
)
from pydantic import Field

from dataflow.shared.config import load_workflow_config
from dataflow.shared.logging import get_logger
from dataflow.shared.minio import get_minio_client, upload_file_with_client
from dataflow.workflows.nightscout.ingestion import NightscoutConfig, run_nightscout_ingestion
from dataflow.workflows.nightscout.transform import transform_nightscout_data
from dataflow.workflows.registry import register_workflow

log = get_logger("dataflow.workflows.nightscout.job")


class NightscoutResource(ConfigurableResource):
    """Resource representing Nightscout workflow configuration."""

    base_url: str = Field(..., description="Base URL for the Nightscout API")
    api_secret: str | None = Field(None, description="API secret for authenticated access")
    entries_count: int = Field(100, description="Number of entries to fetch")
    treatments_days: int = Field(7, description="Number of days of treatments to fetch")
    profile_enabled: bool = Field(True, description="Whether to fetch profile data")
    bucket_name: str = Field("nightscout-raw", description="Minio bucket for raw data storage")
    local_save_path: str | None = Field(None, description="Local path to save data (optional)")
    normalize_timestamps: bool = Field(True, description="Standardize timestamp formats")
    timezone: str = Field("UTC", description="Timezone for normalized timestamps")
    merge_device_status: bool = Field(True, description="Combine device status with readings")
    transformed_bucket_name: str = Field(
        "nightscout-transformed", description="Minio bucket for transformed data"
    )


@op(
    name="nightscout_ingestion",
    description="Ingests data from Nightscout API and stores it in Minio",
    required_resource_keys={"nightscout_config"},
)
def nightscout_ingestion_op(context: OpExecutionContext) -> dict[str, Any]:
    """Dagster operation for ingesting data from Nightscout API.

    Args:
        context: The Dagster execution context

    Returns:
        Dict with ingested data and metadata
    """
    context.log.info("Starting Nightscout ingestion operation")

    # Get configuration from resource
    config_dict = context.resources.nightscout_config.dict()
    context.log.debug("Using Nightscout configuration", **config_dict)

    # Create timestamp for this run
    run_timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")

    # Run the ingestion process
    try:
        # For now, we'll manually load the data from Minio after ingestion
        # In the future, we could modify the ingestion process to return the data directly
        run_nightscout_ingestion(config_dict)
        context.log.info("Nightscout ingestion completed successfully")

        # Create a client to access Minio
        client = get_minio_client()
        bucket_name = config_dict["bucket_name"]

        # Find the objects created during this ingestion
        # This is a simplification - in a real system, we'd need a more robust way to track ingested files
        all_objects = client.list_objects(bucket_name, recursive=True)
        ingested_objects = [
            obj.object_name for obj in all_objects if run_timestamp in (obj.object_name or "")
        ]

        # Load the ingested data
        data = {}
        for obj_name in ingested_objects:
            # Create a temporary file to store the object
            temp_file_path = f"/tmp/{obj_name}"
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            # Download the object
            if obj_name:  # Add a null check
                client.fget_object(bucket_name, obj_name, temp_file_path)

                # Load the JSON data
                with open(temp_file_path) as f:
                    obj_data = json.load(f)

                # Add to the data dictionary
                data_type = obj_data.get("type", "unknown")
                data[data_type] = obj_data.get("data")

                # Clean up the temporary file
                os.remove(temp_file_path)

        # Return the loaded data
        return {
            "data": data,
            "metadata": {
                "timestamp": run_timestamp,
                "bucket": bucket_name,
                "objects": ingested_objects,
                "config": config_dict,
            },
        }
    except Exception:
        context.log.error("Nightscout ingestion failed", exc_info=True)
        raise


@op(
    name="nightscout_transform",
    description="Transforms ingested Nightscout data",
    required_resource_keys={"nightscout_config"},
)
def nightscout_transform_op(
    context: OpExecutionContext, ingestion_result: dict[str, Any]
) -> dict[str, Any]:
    """Dagster operation for transforming Nightscout data.

    Args:
        context: The Dagster execution context
        ingestion_result: Result from the ingestion operation

    Returns:
        Dict with transformed data and metadata
    """
    context.log.info("Starting Nightscout transformation operation")

    # Get configuration from resource
    config_dict = context.resources.nightscout_config.dict()
    context.log.debug("Using Nightscout configuration", **config_dict)

    # Extract data and metadata from ingestion result
    data = ingestion_result["data"]
    metadata = ingestion_result["metadata"]
    run_timestamp = metadata["timestamp"]

    try:
        # Transform the data
        transform_config = {
            "normalize_timestamps": config_dict["normalize_timestamps"],
            "timezone": config_dict["timezone"],
            "merge_device_status": config_dict["merge_device_status"],
        }

        transformed_data = transform_nightscout_data(data, transform_config)
        context.log.info("Nightscout transformation completed successfully")

        # Save the transformed data to Minio
        client = get_minio_client()
        bucket_name = config_dict["transformed_bucket_name"]

        # Make sure the bucket exists
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            context.log.info(f"Created bucket: {bucket_name}")

        # Save each DataFrame as a CSV file
        saved_objects = []
        for data_type, df in transformed_data.items():
            # Create a temporary file to store the DataFrame
            temp_file_path = f"/tmp/nightscout_{data_type}_{run_timestamp}.csv"

            # Save the DataFrame to the temporary file
            df.to_csv(temp_file_path, index=False)

            # Upload to Minio
            object_name = f"nightscout_{data_type}_{run_timestamp}.csv"
            upload_file_with_client(
                client=client,
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=temp_file_path,
                content_type="text/csv",
            )

            saved_objects.append(object_name)

            # Clean up the temporary file
            os.remove(temp_file_path)

            # Record the asset materialization
            context.log_event(
                AssetMaterialization(
                    asset_key=f"nightscout_{data_type}",
                    description=f"Transformed Nightscout {data_type} data",
                    metadata={
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": ", ".join(df.columns),
                        "bucket": bucket_name,
                        "object_name": object_name,
                    },
                )
            )

        # Return the result
        return {
            "metadata": {
                "timestamp": run_timestamp,
                "bucket": bucket_name,
                "objects": saved_objects,
                "data_types": list(transformed_data.keys()),
                "row_counts": {k: len(v) for k, v in transformed_data.items()},
            }
        }
    except Exception:
        context.log.error("Nightscout transformation failed", exc_info=True)
        raise


@register_workflow(
    name="nightscout",
    metadata={
        "description": "Ingests and transforms data from Nightscout diabetes management API",
        "author": "DataFlow Team",
        "tags": ["diabetes", "health", "api"],
    },
)
@job(
    name="nightscout_job",
    description="Job for ingesting and transforming Nightscout data",
    resource_defs={
        "nightscout_config": NightscoutResource.configure_at_launch(),
    },
)
def nightscout_job():
    """Dagster job for ingesting and processing Nightscout data."""
    # Just call the op without storing the result, since we're not using it
    nightscout_transform_op(nightscout_ingestion_op())


def load_nightscout_job():
    """Load the Nightscout job with default configuration.

    Returns:
        Configured Nightscout job
    """
    # Load configuration from file
    config = load_workflow_config("nightscout")
    # For now, we validate the config but don't use it to configure the job
    # This would be done in a real implementation
    NightscoutConfig(**config)

    # Apply configuration to the job
    # Since job configuration is more complex in Dagster, we return the unmodified job
    # A real implementation would properly configure the job with resources
    return nightscout_job
