"""Nightscout data transformation implementation.

This module handles the transformation of raw Nightscout data into a normalized format.
"""

from datetime import datetime
from typing import Any, cast

import pandas as pd
from pydantic import BaseModel, Field

from dataflow.shared.logging import get_logger
from dataflow.shared.transform import (
    DataCleaner,
    DataFrameTransformer,
    DateTimeNormalizer,
    TransformationError,
    TransformerPipeline,
    camel_to_snake,
)

log = get_logger("dataflow.workflows.nightscout.transform")


# Pydantic models for validation
class GlucoseReading(BaseModel):
    """Schema for a glucose reading."""

    timestamp: datetime = Field(..., description="Time of the reading")
    sgv: int = Field(..., description="Sensor glucose value in mg/dL")
    direction: str | None = Field(None, description="Trend direction")
    device: str | None = Field(None, description="Device name")
    type: str = Field(..., description="Entry type")


class Treatment(BaseModel):
    """Schema for a treatment record."""

    timestamp: datetime = Field(..., description="Time of the treatment")
    eventType: str = Field(..., description="Type of treatment")
    insulin: float | None = Field(None, description="Insulin amount")
    carbs: float | None = Field(None, description="Carbohydrate amount")
    notes: str | None = Field(None, description="Treatment notes")


class DeviceStatus(BaseModel):
    """Schema for device status."""

    timestamp: datetime = Field(..., description="Time of the status update")
    device: str = Field(..., description="Device name")
    uploaderBattery: int | None = Field(None, description="Uploader battery level")
    battery: int | None = Field(None, description="Device battery level")


# Transformer implementations
class NightscoutEntriesToDataFrame(DataFrameTransformer):
    """Transforms Nightscout entries into a normalized DataFrame."""

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Nightscout entries DataFrame.

        Args:
            df: Raw entries DataFrame

        Returns:
            Normalized entries DataFrame
        """
        # Convert dateString to timestamp
        if "dateString" in df.columns:
            df["timestamp"] = pd.to_datetime(df["dateString"])
        elif "date" in df.columns:
            # Convert milliseconds to seconds for datetime conversion
            df["timestamp"] = pd.to_datetime(df["date"], unit="ms")
        else:
            raise TransformationError("No date column found in entries data")

        # Define column mapping
        columns: dict[str, str] = {
            "sgv": "glucose",
            "direction": "trend",
            "device": "device",
            "type": "type",
            "timestamp": "timestamp",
        }

        # Only keep columns that exist in the DataFrame
        valid_columns: dict[str, str] = {k: v for k, v in columns.items() if k in df.columns}

        # Select columns and rename
        result = df[list(valid_columns.keys())]
        result.columns = pd.Index([valid_columns[col] for col in result.columns])

        return cast(pd.DataFrame, result)


class NightscoutTreatmentsToDataFrame(DataFrameTransformer):
    """Transforms Nightscout treatments into a normalized DataFrame."""

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Nightscout treatments DataFrame.

        Args:
            df: Raw treatments DataFrame

        Returns:
            Normalized treatments DataFrame
        """
        # Convert created_at to timestamp
        if "created_at" in df.columns:
            df["timestamp"] = pd.to_datetime(df["created_at"])
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        else:
            raise TransformationError("No timestamp column found in treatments data")

        # Rename columns to snake_case
        renamed_columns = {col: camel_to_snake(col) for col in df.columns}
        df = df.rename(columns=renamed_columns)

        # Ensure required columns exist
        required_cols = ["timestamp", "event_type"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise TransformationError(
                f"Missing required columns in treatments data: {missing_cols}"
            )

        return df


class NightscoutDeviceStatusToDataFrame(DataFrameTransformer):
    """Transforms Nightscout device status into a normalized DataFrame."""

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Nightscout device status DataFrame.

        Args:
            df: Raw device status DataFrame

        Returns:
            Normalized device status DataFrame
        """
        # Convert created_at to timestamp
        if "created_at" in df.columns:
            df["timestamp"] = pd.to_datetime(df["created_at"])
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        else:
            raise TransformationError("No timestamp column found in device status data")

        # Extract device information
        if "device" not in df.columns and "pump" in df.columns:
            # Use pump as device if available
            df["device"] = df["pump"].apply(
                lambda x: x.get("device", "unknown") if isinstance(x, dict) else "unknown"
            )

        # Extract battery information
        if "uploaderBattery" not in df.columns and "uploader" in df.columns:
            # Extract uploader battery if available
            df["uploaderBattery"] = df["uploader"].apply(
                lambda x: x.get("battery", None) if isinstance(x, dict) else None
            )

        # Rename columns to snake_case
        renamed_columns = {col: camel_to_snake(col) for col in df.columns}
        df = df.rename(columns=renamed_columns)

        # Select relevant columns
        relevant_cols = ["timestamp", "device", "uploader_battery", "battery"]
        existing_cols = [col for col in relevant_cols if col in df.columns]

        return cast(pd.DataFrame, df[existing_cols])


class GlucoseDataCleaner(DataCleaner):
    """Cleaner for glucose data with domain-specific cleaning rules."""

    def __init__(
        self,
        min_glucose: int = 40,
        max_glucose: int = 400,
        name: str | None = None,
    ):
        """Initialize the glucose data cleaner.

        Args:
            min_glucose: Minimum valid glucose value
            max_glucose: Maximum valid glucose value
            name: Optional name for the cleaner
        """
        super().__init__(
            drop_duplicates=True,
            drop_null_columns=None,
            drop_null_rows=None,
            fill_null_values=None,
            strip_strings=True,
            name=name or "GlucoseDataCleaner",
        )
        self.min_glucose = min_glucose
        self.max_glucose = max_glucose

    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean glucose data.

        Args:
            df: Glucose data DataFrame

        Returns:
            Cleaned glucose data DataFrame
        """
        # Apply standard cleaning
        result = super()._transform_dataframe(df)

        # Filter out invalid glucose values
        if "glucose" in result.columns:
            original_rows = result.shape[0]
            valid_mask = (result["glucose"] >= self.min_glucose) & (
                result["glucose"] <= self.max_glucose
            )
            result = result[valid_mask]

            if result.shape[0] < original_rows:
                self.log.info(
                    "Filtered out invalid glucose values",
                    original_rows=original_rows,
                    new_rows=result.shape[0],
                    dropped=original_rows - result.shape[0],
                    min_glucose=self.min_glucose,
                    max_glucose=self.max_glucose,
                )

        return cast(pd.DataFrame, result)


class NightscoutTransformer:
    """Main transformer for Nightscout data."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the Nightscout transformer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.log = get_logger("dataflow.transform.nightscout")

        # Extract config values with defaults
        self.normalize_timestamps = config.get("normalize_timestamps", True)
        self.timezone = config.get("timezone", "UTC")
        self.merge_device_status = config.get("merge_device_status", True)

        # Initialize pipelines
        self._init_pipelines()

    def _init_pipelines(self) -> None:
        """Initialize transformation pipelines."""
        # Entries pipeline
        self.entries_pipeline = TransformerPipeline(
            [
                NightscoutEntriesToDataFrame(name="EntriesNormalizer"),
                GlucoseDataCleaner(
                    min_glucose=40,
                    max_glucose=400,
                    name="GlucoseCleaner",
                ),
                DateTimeNormalizer(
                    columns=["timestamp"],
                    target_timezone=self.timezone,
                    errors="raise",
                    name="TimestampNormalizer",
                ),
            ],
            name="EntriesPipeline",
        )

        # Treatments pipeline
        self.treatments_pipeline = TransformerPipeline(
            [
                NightscoutTreatmentsToDataFrame(name="TreatmentsNormalizer"),
                DataCleaner(
                    drop_duplicates=True,
                    drop_null_rows=None,
                    strip_strings=True,
                    name="TreatmentsCleaner",
                ),
                DateTimeNormalizer(
                    columns=["timestamp"],
                    target_timezone=self.timezone,
                    errors="raise",
                    name="TimestampNormalizer",
                ),
            ],
            name="TreatmentsPipeline",
        )

        # Device status pipeline
        self.device_status_pipeline = TransformerPipeline(
            [
                NightscoutDeviceStatusToDataFrame(name="DeviceStatusNormalizer"),
                DateTimeNormalizer(
                    columns=["timestamp"],
                    target_timezone=self.timezone,
                    errors="raise",
                    name="TimestampNormalizer",
                ),
            ],
            name="DeviceStatusPipeline",
        )

    def transform_entries(self, entries: list[dict[str, Any]]) -> pd.DataFrame:
        """Transform glucose entries.

        Args:
            entries: List of raw entry dictionaries

        Returns:
            Transformed entries DataFrame
        """
        try:
            self.log.info("Transforming glucose entries", count=len(entries))

            # Convert to DataFrame
            df = pd.DataFrame(entries)

            # Apply transformation pipeline
            result = self.entries_pipeline.transform(df)

            self.log.info(
                "Successfully transformed glucose entries",
                original_count=len(entries),
                transformed_count=len(result),
            )

            return result
        except Exception as e:
            self.log.error("Failed to transform glucose entries", error=str(e))
            raise TransformationError(f"Failed to transform glucose entries: {e}") from e

    def transform_treatments(self, treatments: list[dict[str, Any]]) -> pd.DataFrame:
        """Transform treatments.

        Args:
            treatments: List of raw treatment dictionaries

        Returns:
            Transformed treatments DataFrame
        """
        try:
            self.log.info("Transforming treatments", count=len(treatments))

            # Convert to DataFrame
            df = pd.DataFrame(treatments)

            # Apply transformation pipeline
            result = self.treatments_pipeline.transform(df)

            self.log.info(
                "Successfully transformed treatments",
                original_count=len(treatments),
                transformed_count=len(result),
            )

            return result
        except Exception as e:
            self.log.error("Failed to transform treatments", error=str(e))
            raise TransformationError(f"Failed to transform treatments: {e}") from e

    def transform_device_status(self, device_status: list[dict[str, Any]]) -> pd.DataFrame:
        """Transform device status.

        Args:
            device_status: List of raw device status dictionaries

        Returns:
            Transformed device status DataFrame
        """
        try:
            self.log.info("Transforming device status", count=len(device_status))

            # Convert to DataFrame
            df = pd.DataFrame(device_status)

            # Apply transformation pipeline
            result = self.device_status_pipeline.transform(df)

            self.log.info(
                "Successfully transformed device status",
                original_count=len(device_status),
                transformed_count=len(result),
            )

            return result
        except Exception as e:
            self.log.error("Failed to transform device status", error=str(e))
            raise TransformationError(f"Failed to transform device status: {e}") from e

    def transform(self, data: dict[str, Any]) -> dict[str, pd.DataFrame]:
        """Transform all Nightscout data.

        Args:
            data: Dictionary containing raw Nightscout data

        Returns:
            Dictionary of transformed DataFrames
        """
        result = {}

        # Transform entries if available
        entries_data = data.get("entries")
        if entries_data:
            result["entries"] = self.transform_entries(entries_data)

        # Transform treatments if available
        treatments_data = data.get("treatments")
        if treatments_data:
            result["treatments"] = self.transform_treatments(treatments_data)

        # Transform device status if available
        device_status_data = data.get("device_status")
        if device_status_data:
            result["device_status"] = self.transform_device_status(device_status_data)

        # Merge with device status if requested
        if self.merge_device_status and "entries" in result and "device_status" in result:
            self.log.info("Merging device status with glucose entries")

            # Create a copy of entries data
            merged_df = result["entries"].copy()

            # Merge with device status using nearest timestamp
            ds_df = result["device_status"].copy()

            # Use pd.merge_asof for time-based merging
            try:
                # Sort both DataFrames by timestamp and clean out NaT values
                merged_df = merged_df.dropna(subset=["timestamp"]).sort_values("timestamp")
                ds_df = ds_df.dropna(subset=["timestamp"]).sort_values("timestamp")

                # Skip merge if we have no data after cleanup
                if len(merged_df.index) == 0 or len(ds_df.index) == 0:
                    self.log.warning("Skipping merge due to empty dataframes after NaT removal")
                else:
                    # Create a fixed tolerance value that's guaranteed to be a Timedelta
                    tolerance_val = cast(pd.Timedelta, pd.Timedelta(minutes=30))

                    # Merge with device status using nearest timestamp
                    merged_df = pd.merge_asof(
                        merged_df,
                        ds_df,
                        on="timestamp",
                        direction="nearest",
                        tolerance=tolerance_val,
                        suffixes=("", "_device"),
                    )

                    # Add the merged data to the result
                    result["merged"] = merged_df
                    self.log.info("Successfully merged device status with glucose entries")
            except Exception as e:
                self.log.error("Failed to merge device status with glucose entries", error=str(e))

        return result


def transform_nightscout_data(
    data: dict[str, Any], config: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    """Transform Nightscout data.

    Args:
        data: Raw Nightscout data dictionary
        config: Configuration dictionary

    Returns:
        Dictionary of transformed DataFrames
    """
    transformer = NightscoutTransformer(config)
    return transformer.transform(data)
