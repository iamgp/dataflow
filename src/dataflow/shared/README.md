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

## Transformation Framework (`transform.py`)

The transformation framework provides reusable components for transforming data, including data cleaning, mapping, enrichment, and validation utilities. It is built around a flexible and composable pattern using transformer classes.

### Using the Transformation Framework

The core of the transformation framework is the `Transformer` interface:

```python
from dataflow.shared.transform import Transformer, TransformationError

class MyTransformer(Transformer[InputType, OutputType]):
    def transform(self, data: InputType) -> OutputType:
        # Transform the data
        return transformed_data
```

### Creating Transformation Pipelines

You can chain transformers together to create a pipeline:

```python
from dataflow.shared.transform import TransformerPipeline, DataCleaner, ColumnMapper

# Create a pipeline of transformers
pipeline = TransformerPipeline([
    DataCleaner(drop_duplicates=True, strip_strings=True),
    ColumnMapper(mapping={"old_name": "new_name"}),
    # Add more transformers as needed
])

# Apply the pipeline to data
result = pipeline.transform(data)
```

### Data Cleaning and Preparation

The framework includes several built-in transformers for common data preparation tasks:

```python
from dataflow.shared.transform import (
    DataCleaner,
    DateTimeNormalizer,
    ColumnMapper,
    TypeConverter,
    TextCleaner,
)

# Clean data (remove duplicates, handle nulls, etc.)
cleaner = DataCleaner(
    drop_duplicates=True,
    drop_null_columns=0.8,  # Drop columns with >80% nulls
    fill_null_values={"numeric_col": 0, "string_col": "unknown"},
    strip_strings=True,
)

# Normalize datetime columns
date_normalizer = DateTimeNormalizer(
    columns=["created_at", "updated_at"],
    target_timezone="UTC",
    target_format="%Y-%m-%dT%H:%M:%SZ",
)

# Map columns to a new schema
mapper = ColumnMapper(
    mapping={"old_name1": "new_name1", "old_name2": "new_name2"},
    drop_unmapped=True,
)

# Convert column types
type_converter = TypeConverter(
    type_mapping={"id": "int64", "price": "float64", "active": "bool"},
)

# Clean text data
text_cleaner = TextCleaner(
    columns=["description", "title"],
    lower=True,
    remove_punctuation=True,
)
```

### Validation

You can validate data against a schema using the `SchemaValidator`:

```python
from pydantic import BaseModel, Field
from dataflow.shared.transform import SchemaValidator

# Define a schema using Pydantic
class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = Field(default=True)

# Create a validator
validator = SchemaValidator(model=UserSchema)

# Validate data
valid_data = validator.transform(data)
```

### DataFrame Transformers

For operations on pandas DataFrames, you can extend the `DataFrameTransformer` class:

```python
from dataflow.shared.transform import DataFrameTransformer
import pandas as pd

class MyDataFrameTransformer(DataFrameTransformer):
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Transform the DataFrame
        result = df.copy()
        # Apply transformations...
        return result
```

### Error Handling

Like the ingestion framework, the transformation framework provides a hierarchy of exception types:

- `TransformationError`: Base exception for all transformation errors
- `ValidationError`: For data validation failures
- `MappingError`: For issues with mapping data to a schema
- `EnrichmentError`: For problems with data enrichment

Use these in your implementations to provide consistent error handling:

```python
from dataflow.shared.transform import TransformationError, ValidationError

try:
    # Transformation logic
except ValidationError as e:
    # Handle validation errors
except TransformationError as e:
    # Handle other transformation errors
```

### Utility Functions

The framework also includes utility functions for common transformation tasks:

```python
from dataflow.shared.transform import (
    normalize_timestamp,
    camel_to_snake,
    snake_to_camel,
    merge_dataframes,
)

# Normalize timestamps
iso_timestamp = normalize_timestamp("2023-01-01 12:30:45", target_format="%Y-%m-%dT%H:%M:%SZ")

# Convert between naming conventions
snake_case = camel_to_snake("myVariableName")  # my_variable_name
camel_case = snake_to_camel("my_variable_name")  # myVariableName
pascal_case = snake_to_camel("my_variable_name", pascal=True)  # MyVariableName

# Merge DataFrames with error handling
merged_df = merge_dataframes(left_df, right_df, on="id", how="left")
```

## Database Utilities (`db.py`)

Provides connection and query utilities for DuckDB databases.

## Minio Storage (`minio.py`)

Provides utilities for storing and retrieving data from Minio object storage.

## Configuration (`config.py`)

Provides utilities for loading and validating workflow configurations.

## Logging (`logging.py`)

Provides structured logging utilities for consistent log formatting.
