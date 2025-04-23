"""Integration tests for the Nightscout workflow."""

import os
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pytest
from dagster import ExecuteInProcessResult
from minio import Minio

from dataflow.workflows.nightscout.dagster_job import nightscout_job
from dataflow.workflows.nightscout.ingestion import NightscoutIngestion
from dataflow.workflows.nightscout.transform import NightscoutTransformer


@pytest.fixture
def test_config() -> dict[str, Any]:
    """Test configuration for integration tests."""
    return {
        "base_url": os.getenv("TEST_NIGHTSCOUT_URL", "https://test.herokuapp.com"),
        "api_secret": os.getenv("TEST_NIGHTSCOUT_SECRET", "test_secret"),
        "entries_count": 100,
        "treatments_days": 7,
        "profile_enabled": True,
        "bucket_name": "nightscout-test",
    }


@pytest.mark.integration
def test_workflow_execution(docker_services, test_config: dict[str, Any]) -> None:
    """Test end-to-end workflow execution."""
    # Execute the job
    result: ExecuteInProcessResult = nightscout_job.execute_in_process(
        run_config={"ops": {"ingest_entries": {"config": test_config}}}
    )

    # Check job execution
    assert result.success


@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_pipeline(
    docker_services, test_config: dict[str, Any], minio_client: Minio
) -> None:
    """Test the complete data pipeline from ingestion to transformation."""
    # Initialize components
    ingestion = NightscoutIngestion(test_config)
    transform = NightscoutTransformer(test_config)

    # Extract data
    extracted_data = list(ingestion.extract())
    entries = next(item["data"] for item in extracted_data if item["type"] == "entries")

    # Transform data
    df: pd.DataFrame = transform.transform_entries(entries)

    # Verify data pipeline results
    assert len(df) > 0
    assert "glucose" in df.columns
    assert "timestamp" in df.columns
    glucose_series = cast(pd.Series, df["glucose"])
    assert glucose_series.notna().all()


@pytest.mark.integration
def test_minio_storage(docker_services, minio_client: Minio, test_config: dict[str, Any]) -> None:
    """Test MinIO storage integration."""
    bucket_name = "nightscout-test"
    test_file = "test_data.parquet"

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # Create test file
    test_path = Path("test_data.parquet")
    test_path.write_bytes(b"test data")

    try:
        # Upload test file
        minio_client.fput_object(bucket_name, test_file, str(test_path))

        # Verify file exists
        assert minio_client.stat_object(bucket_name, test_file)
    finally:
        # Cleanup
        if test_path.exists():
            test_path.unlink()
        try:
            minio_client.remove_object(bucket_name, test_file)
        except Exception as e:
            print(f"Failed to remove test object: {e}")
