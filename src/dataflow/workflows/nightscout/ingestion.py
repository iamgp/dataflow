"""Nightscout data ingestion implementation.

This module handles the extraction of data from a Nightscout API instance.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from dataflow.shared.ingestion import (
    BaseAPIClient,
    BaseDataIngestion,
    DataIngestionError,
    RetryConfig,
    save_to_local_file,
    save_to_minio,
)
from dataflow.shared.logging import get_logger

log = get_logger("dataflow.workflows.nightscout.ingestion")


class NightscoutConfig(BaseModel):
    """Nightscout API configuration."""

    base_url: str = Field(..., description="Base URL for the Nightscout API")
    api_secret: str | None = Field(None, description="API secret for authenticated access")
    entries_count: int = Field(100, description="Number of entries to fetch")
    treatments_days: int = Field(7, description="Number of days of treatments to fetch")
    profile_enabled: bool = Field(True, description="Whether to fetch profile data")
    bucket_name: str = Field("nightscout-raw", description="Minio bucket for raw data storage")
    local_save_path: str | None = Field(None, description="Local path to save data (optional)")


class NightscoutAPIClient(BaseAPIClient):
    """Client for interacting with the Nightscout API."""

    def __init__(self, base_url: str, api_secret: str | None = None):
        """Initialize the Nightscout API client.

        Args:
            base_url: Base URL for the Nightscout API
            api_secret: API secret for authenticated access
        """
        headers = {}
        if api_secret:
            headers["API-SECRET"] = api_secret

        # Configure with longer timeouts for potentially slow endpoints
        retry_config = RetryConfig(
            max_retries=5,
            retry_delay=1.5,
            backoff_factor=2.0,
        )

        super().__init__(base_url, headers=headers, retry_config=retry_config)

    def get_entries(self, count: int = 100) -> list[dict[str, Any]]:
        """Get the most recent glucose entries.

        Args:
            count: Number of entries to fetch

        Returns:
            List of glucose entries
        """
        self.log.info(f"Fetching {count} Nightscout entries")
        return self.get(f"api/v1/entries.json?count={count}")

    def get_treatments(self, days: int = 7) -> list[dict[str, Any]]:
        """Get treatments for the specified number of days.

        Args:
            days: Number of days of data to fetch

        Returns:
            List of treatments
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Format dates for Nightscout API
        find_params = {
            "find[created_at][$gte]": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "find[created_at][$lte]": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        self.log.info(f"Fetching Nightscout treatments for {days} days")
        return self.get("api/v1/treatments.json", params=find_params)

    def get_profiles(self) -> list[dict[str, Any]]:
        """Get all profiles.

        Returns:
            List of profiles
        """
        self.log.info("Fetching Nightscout profiles")
        return self.get("api/v1/profile.json")

    def get_status(self) -> dict[str, Any]:
        """Get Nightscout server status.

        Returns:
            Server status information
        """
        self.log.info("Fetching Nightscout status")
        return self.get("api/v1/status.json")


class NightscoutIngestion(BaseDataIngestion[dict[str, Any], dict[str, Any]]):
    """Ingestion workflow for Nightscout data."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the Nightscout ingestion workflow.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.validated_config = NightscoutConfig(**config)
        self.api_client = NightscoutAPIClient(
            base_url=self.validated_config.base_url,
            api_secret=self.validated_config.api_secret,
        )

        # Timestamp for this ingestion run
        self.run_timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
        self.collected_data: dict[str, list[dict[str, Any]] | dict[str, Any] | None] = {
            "entries": None,
            "treatments": None,
            "profiles": None,
            "status": None,
        }

    def extract(self) -> Iterable[dict[str, Any]]:
        """Extract data from Nightscout API.

        Yields:
            Each dataset (entries, treatments, profiles, status)
        """
        try:
            # Get entries
            entries = self.api_client.get_entries(count=self.validated_config.entries_count)
            self.collected_data["entries"] = entries
            yield {"type": "entries", "data": entries}

            # Get treatments
            treatments = self.api_client.get_treatments(days=self.validated_config.treatments_days)
            self.collected_data["treatments"] = treatments
            yield {"type": "treatments", "data": treatments}

            # Get profiles if enabled
            if self.validated_config.profile_enabled:
                profiles = self.api_client.get_profiles()
                self.collected_data["profiles"] = profiles
                yield {"type": "profiles", "data": profiles}

            # Get status
            status = self.api_client.get_status()
            self.collected_data["status"] = status
            yield {"type": "status", "data": status}

        except Exception as e:
            self.log.error("Error during Nightscout data extraction", error=str(e))
            raise DataIngestionError(f"Nightscout extraction failed: {e}") from e

    def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process extracted data.

        For this sample, we're just passing through the data without transformation.
        In a real implementation, this might validate, clean, or transform the data.

        Args:
            data: Source data from extraction

        Returns:
            Processed data for storage
        """
        data_type = data.get("type", "unknown")
        raw_data = data.get("data", [])

        self.log.info(
            f"Processing {data_type} data", count=len(raw_data) if isinstance(raw_data, list) else 1
        )

        # Add metadata
        result = {
            "type": data_type,
            "ingestion_timestamp": self.run_timestamp,
            "count": len(raw_data) if isinstance(raw_data, list) else 1,
            "data": raw_data,
        }

        return result

    def store(self, data: dict[str, Any]) -> None:
        """Store processed data.

        Saves data to Minio (and optionally to a local file).

        Args:
            data: Processed data for storage
        """
        data_type = data.get("type", "unknown")

        # Define object name for storage
        object_name = f"nightscout_{data_type}_{self.run_timestamp}.json"

        # Store to MinIO
        try:
            save_to_minio(
                bucket_name=self.validated_config.bucket_name,
                data=data,
                object_name=object_name,
                content_type="application/json",
            )
            self.log.info(
                f"Saved {data_type} data to Minio",
                bucket=self.validated_config.bucket_name,
                object=object_name,
            )
        except Exception as e:
            self.log.error(f"Failed to save {data_type} data to Minio", error=str(e))
            raise

        # Optionally store to local file
        if self.validated_config.local_save_path:
            try:
                file_path = f"{self.validated_config.local_save_path}/nightscout_{data_type}_{self.run_timestamp}.json"
                save_to_local_file(data, file_path)
                self.log.info(f"Saved {data_type} data to local file", file_path=file_path)
            except Exception as e:
                # Log but don't fail the ingestion if local save fails
                self.log.warning(f"Failed to save {data_type} data to local file", error=str(e))

    def pre_run(self) -> None:
        """Pre-run hook."""
        self.log.info(
            "Starting Nightscout ingestion",
            url=self.validated_config.base_url,
            entries_count=self.validated_config.entries_count,
            treatments_days=self.validated_config.treatments_days,
        )

    def post_run(self) -> None:
        """Post-run hook."""
        data_counts = {
            k: len(v) if isinstance(v, list) else (0 if v is None else 1)
            for k, v in self.collected_data.items()
            if v is not None
        }
        self.log.info("Completed Nightscout ingestion", data_counts=data_counts)

    def handle_item_error(self, item: dict[str, Any], error: Exception) -> None:
        """Handle error during item processing.

        Args:
            item: The data item that caused the error
            error: The exception that was raised
        """
        data_type = item.get("type", "unknown")
        self.log.error(f"Error processing {data_type} data", error=str(error))


def run_nightscout_ingestion(config: dict[str, Any]) -> None:
    """Run the Nightscout ingestion workflow.

    Args:
        config: Configuration dictionary
    """
    ingestion = NightscoutIngestion(config)
    ingestion.run()
