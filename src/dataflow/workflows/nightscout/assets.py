"""Dagster assets for the Nightscout workflow.

This module defines Dagster assets that represent data produced by the Nightscout workflow.
Assets provide a way to materialize, track, and manage these data artifacts over time.
"""

from typing import Any

import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetOut,
    Config,
    asset,
    multi_asset,
)
from pydantic import Field

from dataflow.shared.logging import get_logger
from dataflow.shared.minio import get_minio_client, upload_dataframe

log = get_logger("dataflow.workflows.nightscout.assets")


class NightscoutAssetsConfig(Config):
    """Configuration for Nightscout assets."""

    raw_bucket: str = Field("nightscout-raw", description="MinIO bucket for raw Nightscout data")
    transformed_bucket: str = Field(
        "nightscout-transformed", description="MinIO bucket for transformed data"
    )
    analyzed_bucket: str = Field(
        "nightscout-analyzed", description="MinIO bucket for analyzed data"
    )
    time_ranges: list[str] = Field(
        ["daily", "weekly", "monthly"],
        description="Time ranges for glucose statistics",
    )


@asset(
    name="nightscout_raw_data",
    description="Raw data ingested from Nightscout API",
    io_manager_key="minio_io_manager",
    group_name="nightscout",
)
def nightscout_raw_data(
    context: AssetExecutionContext, config: NightscoutAssetsConfig
) -> dict[str, Any]:
    """Asset representing raw data ingested from Nightscout.

    Args:
        context: The asset execution context
        config: Configuration for Nightscout assets

    Returns:
        Dictionary containing file paths or references to the raw data
    """
    context.log.info("Materializing raw Nightscout data asset")

    # In a real implementation, this would reference the latest ingested data
    # For now, we'll list objects in the raw bucket to demonstrate the pattern
    minio_client = get_minio_client()
    bucket_name = config.raw_bucket

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        context.log.warning(f"Bucket {bucket_name} does not exist, no raw data available")
        return {"files": []}

    # List objects in the bucket
    objects = list(minio_client.list_objects(bucket_name, recursive=True))
    object_names = [obj.object_name for obj in objects]

    context.log.info(f"Found {len(object_names)} raw data files in bucket {bucket_name}")

    # Safely get the last modified date
    last_modified = None
    if objects:
        dates = [obj.last_modified for obj in objects]
        last_modified = max(date for date in dates if date is not None) if any(dates) else None

    return {
        "bucket": bucket_name,
        "files": object_names,
        "count": len(object_names),
        "last_updated": last_modified,
    }


@asset(
    name="nightscout_transformed_data",
    description="Transformed Nightscout data",
    ins={"raw_data": AssetIn("nightscout_raw_data")},
    io_manager_key="minio_io_manager",
    group_name="nightscout",
)
def nightscout_transformed_data(
    context: AssetExecutionContext, raw_data: dict[str, Any], config: NightscoutAssetsConfig
) -> dict[str, Any]:
    """Asset representing transformed Nightscout data.

    Args:
        context: The asset execution context
        raw_data: The raw data asset
        config: Configuration for Nightscout assets

    Returns:
        Dictionary containing file paths or references to the transformed data
    """
    context.log.info("Materializing transformed Nightscout data asset")

    # Reference the transformed data bucket
    minio_client = get_minio_client()
    bucket_name = config.transformed_bucket

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        context.log.warning(f"Bucket {bucket_name} does not exist, no transformed data available")
        return {"files": []}

    # List objects in the bucket
    objects = list(minio_client.list_objects(bucket_name, recursive=True))
    object_names = [obj.object_name for obj in objects]

    context.log.info(f"Found {len(object_names)} transformed data files in bucket {bucket_name}")

    # Safely get the last modified date
    last_modified = None
    if objects:
        dates = [obj.last_modified for obj in objects]
        last_modified = max(date for date in dates if date is not None) if any(dates) else None

    return {
        "bucket": bucket_name,
        "files": object_names,
        "count": len(object_names),
        "last_updated": last_modified,
    }


@multi_asset(
    name="nightscout_statistics",
    description="Statistical analyses of Nightscout glucose data",
    outs={
        "daily_stats": AssetOut(
            key=AssetKey("nightscout_daily_statistics"), io_manager_key="minio_io_manager"
        ),
        "weekly_stats": AssetOut(
            key=AssetKey("nightscout_weekly_statistics"), io_manager_key="minio_io_manager"
        ),
        "monthly_stats": AssetOut(
            key=AssetKey("nightscout_monthly_statistics"), io_manager_key="minio_io_manager"
        ),
    },
    ins={"transformed_data": AssetIn("nightscout_transformed_data")},
    group_name="nightscout",
)
def nightscout_statistics(
    context: AssetExecutionContext, transformed_data: dict[str, Any], config: NightscoutAssetsConfig
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate statistical analyses from transformed Nightscout data.

    Args:
        context: The asset execution context
        transformed_data: The transformed data asset
        config: Configuration for Nightscout assets

    Returns:
        Tuple of DataFrames with daily, weekly, and monthly statistics
    """
    context.log.info("Calculating Nightscout glucose statistics")

    # In a real implementation, this would load the transformed data
    # and calculate various statistics

    # For now, we'll create empty DataFrames to demonstrate the pattern
    stats = {}

    # Create a statistics DataFrame for each time range
    for time_range in config.time_ranges:
        stats[f"{time_range}_stats"] = pd.DataFrame(
            {
                "metric": [
                    "mean_glucose",
                    "time_in_range",
                    "standard_deviation",
                    "coefficient_of_variation",
                ],
                "value": [0.0, 0.0, 0.0, 0.0],
                "unit": ["mg/dL", "%", "mg/dL", "%"],
            }
        )

        # For a real implementation, we'd save these to MinIO
        minio_client = get_minio_client()
        analyzed_bucket = config.analyzed_bucket

        # Ensure bucket exists
        if not minio_client.bucket_exists(analyzed_bucket):
            minio_client.make_bucket(analyzed_bucket)

        # Upload the DataFrame
        upload_dataframe(
            df=stats[f"{time_range}_stats"],
            bucket_name=analyzed_bucket,
            object_name=f"nightscout_statistics_{time_range}.csv",
            content_type="text/csv",
        )

        context.log.info(f"Generated and saved {time_range} statistics")

    return (
        stats["daily_stats"],
        stats["weekly_stats"],
        stats["monthly_stats"],
    )
