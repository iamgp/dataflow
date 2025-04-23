"""Unit tests for the Nightscout workflow components."""

from datetime import UTC, datetime
from typing import cast
from unittest.mock import patch

import pandas as pd
import pytest
from dagster import (
    AssetExecutionContext,
    build_asset_context,
)

from dataflow.workflows.nightscout.assets import (
    NightscoutAssetsConfig,
    nightscout_raw_data,
    nightscout_statistics,
    nightscout_transformed_data,
)
from dataflow.workflows.nightscout.ingestion import NightscoutIngestion


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "base_url": "https://test.herokuapp.com",
        "api_secret": "test_secret",
        "entries_count": 100,
        "treatments_days": 7,
        "profile_enabled": True,
        "bucket_name": "nightscout-test",
    }


@pytest.fixture
def mock_entries_response():
    """Mock Nightscout entries response."""
    return [
        {
            "_id": "test_id_1",
            "type": "sgv",
            "date": int(datetime(2023, 1, 1, tzinfo=UTC).timestamp() * 1000),
            "sgv": 120,
            "direction": "Flat",
        },
        {
            "_id": "test_id_2",
            "type": "sgv",
            "date": int(datetime(2023, 1, 1, 1, tzinfo=UTC).timestamp() * 1000),
            "sgv": 130,
            "direction": "FortyFiveUp",
        },
    ]


class TestNightscoutIngestion:
    """Test suite for NightscoutIngestion class."""

    @pytest.mark.asyncio
    async def test_extract_entries(self, mock_config, mock_entries_response):
        """Test extracting entries from Nightscout API."""
        with patch("dataflow.workflows.nightscout.ingestion.NightscoutAPIClient") as mock_client:
            mock_client.return_value.get_entries.return_value = mock_entries_response

            ingestion = NightscoutIngestion(mock_config)
            extracted_data = list(ingestion.extract())

            assert len(extracted_data) > 0
            entries = next(item for item in extracted_data if item["type"] == "entries")
            assert entries["data"] == mock_entries_response

    @pytest.mark.asyncio
    async def test_extract_error(self, mock_config):
        """Test error handling during extraction."""
        with patch("dataflow.workflows.nightscout.ingestion.NightscoutAPIClient") as mock_client:
            mock_client.return_value.get_entries.side_effect = Exception("API Error")

            ingestion = NightscoutIngestion(mock_config)
            with pytest.raises(Exception, match="Nightscout extraction failed"):
                list(ingestion.extract())


class TestNightscoutTransform:
    """Test suite for NightscoutTransform class."""

    def test_transform_entries(self, mock_entries_response):
        """Test transforming Nightscout entries."""
        from dataflow.workflows.nightscout.transform import NightscoutTransformer

        transform = NightscoutTransformer({})
        df = transform.transform_entries(mock_entries_response)

        assert len(df) == 2
        assert "glucose" in df.columns
        assert "timestamp" in df.columns
        assert "trend" in df.columns

        assert df.iloc[0]["glucose"] == 120
        assert df.iloc[1]["glucose"] == 130

    def test_transform_empty_entries(self):
        """Test transforming empty entries list."""
        from dataflow.workflows.nightscout.transform import NightscoutTransformer

        transform = NightscoutTransformer({})
        with pytest.raises(Exception, match="No date column found in entries data"):
            transform.transform_entries([])


class TestNightscoutAssets:
    """Test suite for Nightscout assets."""

    @pytest.fixture
    def context(self) -> AssetExecutionContext:
        """Create a test context using Dagster's build_asset_context."""
        return build_asset_context()

    @pytest.fixture
    def mock_assets_config(self) -> NightscoutAssetsConfig:
        """Mock assets config."""
        return NightscoutAssetsConfig(
            raw_bucket="test-raw",
            transformed_bucket="test-transformed",
            analyzed_bucket="test-analyzed",
            time_ranges=["daily", "weekly", "monthly"],
        )

    def test_raw_data_asset(self, context, mock_assets_config):
        """Test raw data asset."""
        with patch("dataflow.workflows.nightscout.assets.get_minio_client") as mock_minio:
            mock_minio.return_value.bucket_exists.return_value = True
            mock_minio.return_value.list_objects.return_value = []

            result = nightscout_raw_data(context, mock_assets_config)

            assert isinstance(result, dict)
            assert "bucket" in result
            assert "files" in result
            assert "count" in result

    def test_transformed_data_asset(self, context, mock_assets_config):
        """Test transformed data asset."""
        with patch("dataflow.workflows.nightscout.assets.get_minio_client") as mock_minio:
            mock_minio.return_value.bucket_exists.return_value = True
            mock_minio.return_value.list_objects.return_value = []

            raw_data = {"bucket": "test-raw", "files": [], "count": 0}
            result = nightscout_transformed_data(context, raw_data, mock_assets_config)

            assert isinstance(result, dict)
            assert "bucket" in result
            assert "files" in result
            assert "count" in result

    def test_statistics_asset(self, context, mock_assets_config):
        """Test statistics asset."""
        with patch("dataflow.workflows.nightscout.assets.get_minio_client") as mock_minio:
            mock_minio.return_value.bucket_exists.return_value = True
            mock_minio.return_value.list_objects.return_value = []

            transformed_data = {"bucket": "test-transformed", "files": [], "count": 0}
            result = cast(
                tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
                nightscout_statistics(context, transformed_data, mock_assets_config),
            )
            daily_stats, weekly_stats, monthly_stats = result

            # Verify each DataFrame in the tuple
            assert isinstance(daily_stats, pd.DataFrame)
            assert isinstance(weekly_stats, pd.DataFrame)
            assert isinstance(monthly_stats, pd.DataFrame)

            # Verify DataFrame structure
            for df in [daily_stats, weekly_stats, monthly_stats]:
                assert "metric" in df.columns
                assert "value" in df.columns
                assert "unit" in df.columns
                assert len(df) == 4  # Should have 4 metrics

            # Verify specific metrics are present
            expected_metrics = [
                "mean_glucose",
                "time_in_range",
                "standard_deviation",
                "coefficient_of_variation",
            ]
            for df in [daily_stats, weekly_stats, monthly_stats]:
                actual_metrics = df["metric"].tolist()
                assert actual_metrics == expected_metrics
