"""Data ingestion module for the example workflow.

This module contains functions for extracting data from various sources.
"""

import json
import random
from datetime import datetime
from typing import Any

import requests

from dataflow.shared.logging import get_logger

log = get_logger("example_workflow.ingestion")


def extract_data(source_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract data from the configured source.

    Args:
        source_config: Configuration for the data source

    Returns:
        List of extracted data records

    Raises:
        ValueError: If the source configuration is invalid
        ConnectionError: If there's an issue connecting to the data source
    """
    source_name = source_config.get("name", "unknown")
    source_type = source_config.get("type", "api")

    log.info("Extracting data from source", source=source_name, type=source_type)

    if source_type == "api":
        return _extract_from_api(source_config.get("api", {}))
    elif source_type == "file":
        return _extract_from_file(source_config.get("file", {}))
    elif source_type == "mock":
        return _generate_mock_data(source_config.get("mock", {}))
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


def _extract_from_api(api_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract data from an API source.

    Args:
        api_config: API configuration

    Returns:
        List of data records

    Raises:
        ConnectionError: If the API request fails
    """
    url = api_config.get("url")
    if not url:
        raise ValueError("API URL is required")

    method = api_config.get("method", "GET")
    headers = api_config.get("headers", {})
    params = api_config.get("params", {})

    log.info("Making API request", url=url, method=method)

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        # Parse the response as JSON
        data = response.json()

        # Handle different response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, dict) and "results" in data:
            return data["results"]
        else:
            return [data]

    except requests.RequestException as e:
        log.error("API request failed", error=str(e), url=url)
        raise ConnectionError(f"Failed to connect to API: {e}") from e


def _extract_from_file(file_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract data from a file source.

    Args:
        file_config: File configuration

    Returns:
        List of data records

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is unsupported
    """
    path = file_config.get("path")
    if not path:
        raise ValueError("File path is required")

    file_format = file_config.get("format", "json")
    encoding = file_config.get("encoding", "utf-8")

    log.info("Reading from file", path=path, format=file_format)

    try:
        with open(path, encoding=encoding) as f:
            if file_format == "json":
                data = json.load(f)
                # Handle different JSON formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "data" in data:
                    return data["data"]
                elif isinstance(data, dict) and "results" in data:
                    return data["results"]
                else:
                    return [data]
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
    except FileNotFoundError:
        log.error("File not found", path=path)
        raise FileNotFoundError(f"File not found: {path}") from None


def _generate_mock_data(mock_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate mock data for testing.

    Args:
        mock_config: Mock data configuration

    Returns:
        List of mock data records
    """
    count = mock_config.get("count", 10)

    log.info("Generating mock data", count=count)

    data = []
    for i in range(count):
        # Generate a random value between 0 and 100
        value = random.uniform(0, 100)

        # Randomly assign a type
        data_type = "type1" if random.random() < 0.7 else "type2"

        # Create a timestamp for today with a random hour
        timestamp = (
            datetime.now()
            .replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )
            .isoformat()
        )

        # Create the record
        record = {
            "id": i + 1,
            "timestamp": timestamp,
            "value": value,
            "type": data_type,
            "is_valid": random.random() < 0.95,  # 95% are valid
        }

        data.append(record)

    return data
