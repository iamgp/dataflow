"""Data transformation module for the example workflow.

This module contains functions for transforming and processing data.
"""

from datetime import datetime
from typing import Any

from dataflow.shared.logging import get_logger

log = get_logger("example_workflow.transform")


def transform_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform raw data into processed format.

    Args:
        data: List of raw data records to transform

    Returns:
        List of transformed data records

    Raises:
        ValueError: If the data is in an invalid format
    """
    if not isinstance(data, list):
        raise TypeError("Input data must be a list")

    log.info(f"Transforming {len(data)} records")

    transformed = []
    for record in data:
        # Skip invalid records
        if "is_valid" in record and not record["is_valid"]:
            log.warning("Skipping invalid record", id=record.get("id"))
            continue

        # Apply transformations
        transformed_record = _transform_record(record)
        transformed.append(transformed_record)

    log.info(f"Transformed {len(transformed)} records successfully")
    return transformed


def _transform_record(record: dict[str, Any]) -> dict[str, Any]:
    """Transform a single data record.

    Args:
        record: Raw data record

    Returns:
        Transformed data record
    """
    # Create a copy of the record to avoid modifying the original
    transformed = record.copy()

    # Format timestamp if present
    if "timestamp" in transformed:
        # Handle different timestamp formats
        try:
            # Try parsing as ISO format
            dt = datetime.fromisoformat(transformed["timestamp"].replace("Z", "+00:00"))
            # Format consistently
            transformed["timestamp"] = dt.isoformat()

            # Add derived date fields
            transformed["date"] = dt.date().isoformat()
            transformed["hour"] = dt.hour
        except (ValueError, TypeError):
            # If parsing fails, keep the original
            log.warning("Failed to parse timestamp", timestamp=transformed["timestamp"])
            transformed["date"] = None
            transformed["hour"] = None

    # Apply value transformations
    if "value" in transformed:
        try:
            # Ensure value is a float
            value = float(transformed["value"])

            # Apply business logic transformations
            # For example, normalize values over 100
            if value > 100:
                value = 100.0
                transformed["was_capped"] = True

            # Add derived metrics
            transformed["value_category"] = _categorize_value(value)
            transformed["value"] = value
        except (ValueError, TypeError):
            log.warning("Failed to process value", value=transformed["value"])
            transformed["value_category"] = "unknown"

    # Add metadata
    transformed["processed_at"] = datetime.now().isoformat()

    return transformed


def _categorize_value(value: float) -> str:
    """Categorize a numeric value into buckets.

    Args:
        value: The numeric value to categorize

    Returns:
        Category string
    """
    if value < 20:
        return "low"
    elif value < 50:
        return "medium"
    elif value < 80:
        return "high"
    else:
        return "very_high"
