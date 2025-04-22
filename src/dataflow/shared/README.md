# DataFlow Shared Utilities

This directory contains shared utilities used throughout the DataFlow platform.

## Ingestion Framework (`ingestion.py`)

The ingestion framework provides a standardized way to extract data from various sources, process it, and store it in the platform. It includes:

- Base classes for building ingestion workflows
- API client utilities with retry logic
- File handling utilities
- Storage utilities for Minio and local files

### Using the Ingestion Framework

To implement a new data source, create a new class that extends `BaseDataIngestion`:

```python
from dataflow.shared.ingestion import BaseDataIngestion, DataIngestionError

class MyDataIngestion(BaseDataIngestion[SourceType, ResultType]):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your specific components

    def extract(self) -> Iterable[SourceType]:
        # Implement extraction logic
        pass

    def process(self, data: SourceType) -> ResultType:
        # Implement processing logic
        pass

    def store(self, data: ResultType) -> None:
        # Implement storage logic
        pass
```

### API Client Usage

The framework includes a base API client with retry logic:

```python
from dataflow.shared.ingestion import BaseAPIClient, RetryConfig

class MyAPIClient(BaseAPIClient):
    def __init__(self, base_url, api_key=None):
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        retry_config = RetryConfig(max_retries=3, retry_delay=1.0)
        super().__init__(base_url, headers=headers, retry_config=retry_config)

    def get_data(self, endpoint, params=None):
        return self.get(endpoint, params=params)
```

### File and Storage Utilities

The framework provides utilities for reading and writing files:

```python
from dataflow.shared.ingestion import read_json_file, read_csv_file, save_to_minio, save_to_local_file

# Reading files
data = read_json_file("path/to/file.json")
rows = read_csv_file("path/to/file.csv")

# Storing data
save_to_minio("my-bucket", data, "object-name.json")
save_to_local_file(data, "path/to/output.json")
```

### Error Handling

The framework provides a hierarchy of exception types for handling different kinds of errors:

- `DataIngestionError`: Base exception for all ingestion errors
- `RateLimitError`: For API rate limiting issues
- `AuthenticationError`: For authentication failures
- `ResourceNotFoundError`: For missing resources
- `ValidationError`: For data validation failures

Use these in your implementations to provide consistent error handling:

```python
from dataflow.shared.ingestion import DataIngestionError, ResourceNotFoundError

try:
    # Ingestion logic
except ResourceNotFoundError as e:
    # Handle missing resource
except DataIngestionError as e:
    # Handle other ingestion errors
```

## Database Utilities (`db.py`)

Provides connection and query utilities for DuckDB databases.

## Minio Storage (`minio.py`)

Provides utilities for storing and retrieving data from Minio object storage.

## Configuration (`config.py`)

Provides utilities for loading and validating workflow configurations.

## Logging (`logging.py`)

Provides structured logging utilities for consistent log formatting.
