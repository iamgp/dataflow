"""Shared utilities for data ingestion.

This module provides reusable components for data ingestion from various sources
including API clients, file readers, and base classes for creating ingestion pipelines.
"""

import asyncio
import csv
import json
import os
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Generic, Protocol, TextIO, TypeVar, cast

import aiohttp
import pandas as pd
import requests
from pydantic import BaseModel

from dataflow.shared.logging import get_logger
from dataflow.shared.minio import get_minio_client, upload_file_with_client

log = get_logger("dataflow.shared.ingestion")

# Type variable for generic ingestion data types
T = TypeVar("T")
SourceType = TypeVar("SourceType")
ResultType = TypeVar("ResultType")


class DataIngestionError(Exception):
    """Base exception for all ingestion-related errors."""

    pass


class RateLimitError(DataIngestionError):
    """Exception raised when a rate limit is hit during ingestion."""

    pass


class AuthenticationError(DataIngestionError):
    """Exception raised when authentication fails during ingestion."""

    pass


class ResourceNotFoundError(DataIngestionError):
    """Exception raised when a requested resource is not found."""

    pass


class ValidationError(DataIngestionError):
    """Exception raised when ingested data fails validation."""

    pass


class IngestionSource(Protocol):
    """Protocol defining the interface for data ingestion sources."""

    def extract(self) -> Iterable[Any]:
        """Extract data from the source."""
        ...


class DataProcessor(Protocol, Generic[SourceType, ResultType]):
    """Protocol defining the interface for data processors."""

    def process(self, data: SourceType) -> ResultType:
        """Process the input data and return the result."""
        ...


class DataSink(Protocol, Generic[T]):
    """Protocol defining the interface for data sinks."""

    def store(self, data: T) -> None:
        """Store the data in the sink."""
        ...


class BaseDataIngestion(ABC, Generic[SourceType, ResultType]):
    """Base class for data ingestion workflows.

    This class provides a template for implementing data ingestion workflows
    with the extract-transform-load pattern.
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the ingestion workflow.

        Args:
            config: Configuration dictionary for the ingestion workflow
        """
        self.config = config
        self.log = get_logger(f"dataflow.ingestion.{self.__class__.__name__}")

    @abstractmethod
    def extract(self) -> Iterable[SourceType]:
        """Extract data from the source.

        Returns:
            Iterable of source data objects

        Raises:
            DataIngestionError: If data extraction fails
        """
        pass

    @abstractmethod
    def process(self, data: SourceType) -> ResultType:
        """Process extracted data.

        Args:
            data: Source data object

        Returns:
            Processed data object

        Raises:
            DataIngestionError: If data processing fails
        """
        pass

    @abstractmethod
    def store(self, data: ResultType) -> None:
        """Store processed data.

        Args:
            data: Processed data object

        Raises:
            DataIngestionError: If data storage fails
        """
        pass

    def run(self) -> None:
        """Run the ingestion workflow.

        Raises:
            DataIngestionError: If any step of the ingestion fails
        """
        try:
            self.log.info("Starting ingestion workflow")
            self.pre_run()

            for item in self.extract():
                try:
                    processed = self.process(item)
                    self.store(processed)
                except Exception as e:
                    self.log.error("Error processing item", error=str(e))
                    self.handle_item_error(item, e)

            self.post_run()
            self.log.info("Ingestion workflow completed successfully")
        except Exception as e:
            self.log.error("Ingestion workflow failed", error=str(e))
            raise DataIngestionError(f"Ingestion workflow failed: {e}") from e

    def pre_run(self) -> None:
        """Hook that runs before the ingestion workflow."""
        pass

    def post_run(self) -> None:
        """Hook that runs after the ingestion workflow."""
        pass

    def handle_item_error(self, item: SourceType, error: Exception) -> None:
        """Handle an error that occurred during item processing.

        Args:
            item: Source data object that caused the error
            error: The exception that was raised
        """
        pass


# API client utilities


class RetryConfig(BaseModel):
    """Configuration for API client retry behavior."""

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    retry_on_status_codes: list[int] = [429, 500, 502, 503, 504]


class BaseAPIClient:
    """Base class for API clients with retry logic."""

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        retry_config: RetryConfig | None = None,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL for the API
            headers: Default headers to include in all requests
            retry_config: Configuration for retry behavior
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.retry_config = retry_config or RetryConfig()
        self.log = get_logger(f"dataflow.ingestion.api.{self.__class__.__name__}")

    def _build_url(self, endpoint: str) -> str:
        """Build a full URL from the endpoint."""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    def handle_response(self, response: requests.Response) -> Any:
        """Handle the API response.

        Args:
            response: Response object from the request

        Returns:
            Parsed response data

        Raises:
            DataIngestionError: If response handling fails
        """
        if response.status_code == 204:
            return None

        if not response.text:
            return None

        try:
            return response.json()
        except json.JSONDecodeError as e:
            self.log.error("Failed to parse JSON response", error=str(e))
            raise DataIngestionError(f"Failed to parse JSON response: {e}") from e

    def get(self, endpoint: str, params: dict[str, Any] | None = None, **kwargs) -> Any:
        """Send a GET request to the API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters
            **kwargs: Additional arguments to pass to requests.get

        Returns:
            Parsed response data

        Raises:
            DataIngestionError: If the request fails
        """
        url = self._build_url(endpoint)
        headers = {**self.headers, **kwargs.pop("headers", {})}

        retries = 0
        delay = self.retry_config.retry_delay

        while True:
            try:
                self.log.debug("Sending GET request", url=url)
                response = requests.get(url, params=params, headers=headers, **kwargs)

                if response.status_code in self.retry_config.retry_on_status_codes:
                    if retries >= self.retry_config.max_retries:
                        self.log.warning("Max retries reached", url=url)
                        break

                    retries += 1
                    self.log.warning(
                        "Retrying request",
                        url=url,
                        status_code=response.status_code,
                        retry=retries,
                        delay=delay,
                    )
                    asyncio.sleep(delay)
                    delay *= self.retry_config.backoff_factor
                    continue

                if response.status_code == 401:
                    raise AuthenticationError(f"Authentication failed: {response.text}")

                if response.status_code == 404:
                    raise ResourceNotFoundError(f"Resource not found: {response.text}")

                if response.status_code == 429:
                    raise RateLimitError(f"Rate limit exceeded: {response.text}")

                response.raise_for_status()
                return self.handle_response(response)

            except (requests.RequestException, json.JSONDecodeError) as e:
                self.log.error("Request failed", url=url, error=str(e))
                raise DataIngestionError(f"Request failed: {e}") from e

    async def async_get(
        self, session: aiohttp.ClientSession, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Send an asynchronous GET request to the API.

        Args:
            session: aiohttp client session
            endpoint: API endpoint to call
            params: Query parameters

        Returns:
            Parsed response data

        Raises:
            DataIngestionError: If the request fails
        """
        url = self._build_url(endpoint)

        retries = 0
        delay = self.retry_config.retry_delay

        while True:
            try:
                self.log.debug("Sending async GET request", url=url)
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status in self.retry_config.retry_on_status_codes:
                        if retries >= self.retry_config.max_retries:
                            self.log.warning("Max retries reached", url=url)
                            break

                        retries += 1
                        self.log.warning(
                            "Retrying request",
                            url=url,
                            status_code=response.status,
                            retry=retries,
                            delay=delay,
                        )
                        await asyncio.sleep(delay)
                        delay *= self.retry_config.backoff_factor
                        continue

                    if response.status == 401:
                        raise AuthenticationError(f"Authentication failed: {await response.text()}")

                    if response.status == 404:
                        raise ResourceNotFoundError(f"Resource not found: {await response.text()}")

                    if response.status == 429:
                        raise RateLimitError(f"Rate limit exceeded: {await response.text()}")

                    response.raise_for_status()

                    if response.status == 204:
                        return None

                    if response.content_type == "application/json":
                        return await response.json()
                    else:
                        return await response.text()

            except (aiohttp.ClientError, json.JSONDecodeError) as e:
                self.log.error("Async request failed", url=url, error=str(e))
                raise DataIngestionError(f"Async request failed: {e}") from e


# File utilities


def read_json_file(file_path: str | Path) -> Any:
    """Read a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data

    Raises:
        DataIngestionError: If file reading fails
    """
    try:
        with open(file_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.error("Failed to read JSON file", file_path=str(file_path), error=str(e))
        raise DataIngestionError(f"Failed to read JSON file {file_path}: {e}") from e


def read_csv_file(
    file_path: str | Path, delimiter: str = ",", encoding: str = "utf-8", **kwargs
) -> list[dict[str, Any]]:
    """Read a CSV file.

    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter character
        encoding: File encoding
        **kwargs: Additional arguments to pass to csv.DictReader

    Returns:
        List of dictionaries, one per row

    Raises:
        DataIngestionError: If file reading fails
    """
    try:
        with open(file_path, encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter, **kwargs)
            return list(reader)
    except (csv.Error, OSError) as e:
        log.error("Failed to read CSV file", file_path=str(file_path), error=str(e))
        raise DataIngestionError(f"Failed to read CSV file {file_path}: {e}") from e


def read_csv_as_dataframe(file_path: str | Path, **kwargs) -> pd.DataFrame:
    """Read a CSV file as a pandas DataFrame.

    Args:
        file_path: Path to the CSV file
        **kwargs: Additional arguments to pass to pandas.read_csv

    Returns:
        Pandas DataFrame

    Raises:
        DataIngestionError: If file reading fails
    """
    try:
        return pd.read_csv(file_path, **kwargs)
    except (pd.errors.ParserError, OSError) as e:
        log.error("Failed to read CSV as DataFrame", file_path=str(file_path), error=str(e))
        raise DataIngestionError(f"Failed to read CSV file {file_path} as DataFrame: {e}") from e


# Storage utilities


def save_to_minio(
    bucket_name: str,
    data: Any,
    object_name: str | None = None,
    content_type: str | None = None,
) -> str:
    """Save data to Minio.

    Args:
        bucket_name: Minio bucket name
        data: Data to save (string, bytes, or file-like object)
        object_name: Object name in Minio, defaults to ISO timestamp if None
        content_type: MIME type of the content

    Returns:
        Object name used for storage

    Raises:
        DataIngestionError: If saving to Minio fails
    """
    if object_name is None:
        timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
        object_name = f"data_{timestamp}.json"

    try:
        client = get_minio_client()

        if isinstance(data, (str, bytes)):
            # For string or bytes data, create a file-like object
            if isinstance(data, str):
                data = data.encode("utf-8")

            import io

            file_stream = io.BytesIO(data)
            ct = content_type or "application/octet-stream"
            upload_file_with_client(
                client=client,
                bucket_name=bucket_name,
                object_name=object_name,
                file_stream=cast(BinaryIO, file_stream),
                content_type=ct,
            )
        else:
            # Assume it's a file path
            upload_file_with_client(
                client=client,
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=str(data),
                content_type=content_type or "application/octet-stream",
            )

        return object_name

    except Exception as e:
        log.error("Failed to save data to Minio", bucket=bucket_name, error=str(e))
        raise DataIngestionError(f"Failed to save data to Minio: {e}") from e


def save_to_local_file(
    data: Any,
    file_path: str | Path,
    mode: str = "w",
    encoding: str | None = "utf-8",
) -> str:
    """Save data to a local file.

    Args:
        data: Data to save
        file_path: Path to the file
        mode: File open mode
        encoding: File encoding (for text mode)

    Returns:
        Path to the saved file

    Raises:
        DataIngestionError: If saving to file fails
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        is_binary = "b" in mode

        if isinstance(data, (dict, list)):
            # JSON serializable data
            with open(
                file_path, mode if is_binary else "w", encoding=None if is_binary else encoding
            ) as f:
                json.dump(data, cast(TextIO, f), indent=2)
        else:
            # String or bytes
            with open(file_path, mode, encoding=None if is_binary else encoding) as f:
                f.write(data)

        return str(file_path)

    except Exception as e:
        log.error("Failed to save data to file", file_path=str(file_path), error=str(e))
        raise DataIngestionError(f"Failed to save data to file {file_path}: {e}") from e
