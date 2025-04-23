## Workflow Authoring Guide

This guide explains how to author and register new workflows in the DataFlow platform.

### Workflow Directory Structure

Each workflow should be created in its own directory under `src/dataflow/workflows/` with the following structure:

```
src/dataflow/workflows/my_workflow/
├── __init__.py             # Exports public components and registers the workflow
├── config.yaml             # Workflow configuration
├── ingestion.py            # Data extraction logic
├── transform.py            # Data transformation logic
├── assets.py               # Dagster assets/resources (optional)
├── dagster_job.py          # Dagster job definition and registration
├── dbt/                    # DBT models (optional)
│   └── ...
├── evidence/               # Evidence dashboards (optional)
│   └── ...
└── tests/                  # Unit and integration tests
    └── ...
```

### Implementing a New Workflow

#### Step 1: Create the Basic Structure

Create the workflow directory and required files:

```bash
mkdir -p src/dataflow/workflows/my_workflow/tests
mkdir -p src/dataflow/workflows/my_workflow/dbt
mkdir -p src/dataflow/workflows/my_workflow/evidence
touch src/dataflow/workflows/my_workflow/__init__.py
touch src/dataflow/workflows/my_workflow/config.yaml
touch src/dataflow/workflows/my_workflow/ingestion.py
touch src/dataflow/workflows/my_workflow/transform.py
touch src/dataflow/workflows/my_workflow/assets.py
touch src/dataflow/workflows/my_workflow/dagster_job.py
```

#### Step 2: Define Configuration in config.yaml

Define your workflow's configuration parameters:

```yaml
# src/dataflow/workflows/my_workflow/config.yaml
source:
  type: "api" # or file, database, etc.
  url: "https://api.example.com/data"
  auth:
    type: "bearer"
    token: "${MY_API_TOKEN}" # Environment variable reference

transform:
  normalize_timestamps: true
  timezone: "UTC"

destination:
  bucket_name: "my-workflow-data"
```

#### Step 3: Implement Ingestion Logic

Implement data extraction in `ingestion.py`:

```python
"""Data ingestion for My Workflow."""

from typing import Any, Dict

from pydantic import BaseModel, Field

from dataflow.shared.ingestion import APIIngestionSource, DataIngestionPipeline
from dataflow.shared.logging import get_logger

log = get_logger("dataflow.workflows.my_workflow.ingestion")


class MyWorkflowConfig(BaseModel):
    """Configuration for My Workflow ingestion."""

    url: str = Field(..., description="API endpoint URL")
    auth_token: str = Field(None, description="Bearer token for API authentication")
    # Add other configuration parameters


def run_my_workflow_ingestion(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the ingestion process for My Workflow.

    Args:
        config: Configuration parameters

    Returns:
        Dictionary with ingestion results and metadata
    """
    # Implementation details...

    return {"status": "success", "records": 100}
```

#### Step 4: Implement Transformation Logic

Implement data transformation in `transform.py`:

```python
"""Data transformation for My Workflow."""

from typing import Any, Dict

import pandas as pd

from dataflow.shared.logging import get_logger
from dataflow.shared.transform import standardize_timestamps

log = get_logger("dataflow.workflows.my_workflow.transform")


def transform_my_workflow_data(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Transform data from My Workflow.

    Args:
        data: Raw data from ingestion
        config: Transformation configuration

    Returns:
        Dictionary of transformed DataFrames
    """
    # Implementation details...

    return {"main_table": pd.DataFrame()}
```

#### Step 5: Define Dagster Assets (Optional)

Define Dagster assets in `assets.py` to represent data artifacts:

```python
"""Dagster assets for My Workflow."""

from typing import Any, Dict

import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetOut,
    asset,
    multi_asset,
)
from pydantic import BaseModel, Field

from dataflow.shared.logging import get_logger
from dataflow.shared.minio import get_minio_client, upload_dataframe

log = get_logger("dataflow.workflows.my_workflow.assets")


class MyWorkflowAssetsConfig(BaseModel):
    """Configuration for My Workflow assets."""

    raw_bucket: str = Field("my-workflow-raw", description="MinIO bucket for raw data")
    transformed_bucket: str = Field("my-workflow-transformed", description="MinIO bucket for transformed data")


@asset(
    name="my_workflow_raw_data",
    description="Raw data from My Workflow",
    io_manager_key="minio_io_manager",
    group_name="my_workflow",
)
def my_workflow_raw_data(context: AssetExecutionContext, config: MyWorkflowAssetsConfig) -> Dict[str, Any]:
    """Asset representing raw data ingested from My Workflow.

    Args:
        context: The asset execution context
        config: Configuration for My Workflow assets

    Returns:
        Dictionary containing references to the raw data
    """
    # Implementation details...

    return {"files": []}


@asset(
    name="my_workflow_transformed_data",
    description="Transformed My Workflow data",
    ins={"raw_data": AssetIn("my_workflow_raw_data")},
    io_manager_key="minio_io_manager",
    group_name="my_workflow",
)
def my_workflow_transformed_data(
    context: AssetExecutionContext,
    raw_data: Dict[str, Any],
    config: MyWorkflowAssetsConfig
) -> Dict[str, Any]:
    """Asset representing transformed My Workflow data.

    Args:
        context: The asset execution context
        raw_data: The raw data asset
        config: Configuration for My Workflow assets

    Returns:
        Dictionary containing references to the transformed data
    """
    # Implementation details...

    return {"files": []}
```

#### Step 6: Implement Dagster Job

Implement and register the Dagster job in `dagster_job.py`:

```python
"""Dagster job definition for My Workflow."""

from typing import Any, Dict

from dagster import (
    ConfigurableResource,
    OpExecutionContext,
    job,
    op,
)
from pydantic import Field

from dataflow.shared.logging import get_logger
from dataflow.workflows.my_workflow.ingestion import run_my_workflow_ingestion
from dataflow.workflows.my_workflow.transform import transform_my_workflow_data
from dataflow.workflows.registry import register_workflow

log = get_logger("dataflow.workflows.my_workflow.job")


class MyWorkflowResource(ConfigurableResource):
    """Resource representing My Workflow configuration."""

    url: str = Field(..., description="API endpoint URL")
    auth_token: str = Field(None, description="Bearer token for API authentication")
    # Add other configuration parameters


@op(
    name="my_workflow_ingestion",
    description="Ingests data from My Workflow",
    required_resource_keys={"my_workflow_config"},
)
def my_workflow_ingestion_op(context: OpExecutionContext) -> Dict[str, Any]:
    """Dagster operation for ingesting data from My Workflow.

    Args:
        context: The Dagster execution context

    Returns:
        Dict with ingested data and metadata
    """
    # Get configuration from resource
    config_dict = context.resources.my_workflow_config.dict()

    # Run the ingestion process
    return run_my_workflow_ingestion(config_dict)


@op(
    name="my_workflow_transform",
    description="Transforms ingested My Workflow data",
    required_resource_keys={"my_workflow_config"},
)
def my_workflow_transform_op(
    context: OpExecutionContext, ingestion_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Dagster operation for transforming My Workflow data.

    Args:
        context: The Dagster execution context
        ingestion_result: Result from the ingestion operation

    Returns:
        Dict with transformed data and metadata
    """
    # Get configuration from resource
    config_dict = context.resources.my_workflow_config.dict()

    # Transform the data
    transformed_data = transform_my_workflow_data(ingestion_result["data"], config_dict)

    return {
        "data": transformed_data,
        "metadata": {
            "record_counts": {k: len(v) for k, v in transformed_data.items()},
        },
    }


@register_workflow(
    name="my_workflow",
    metadata={
        "description": "My Workflow for processing data from Example API",
        "author": "DataFlow Team",
        "tags": ["example", "api"],
    },
)
@job(
    name="my_workflow_job",
    description="Job for ingesting and transforming My Workflow data",
    resource_defs={
        "my_workflow_config": MyWorkflowResource.configure_at_launch(),
    },
)
def my_workflow_job():
    """Dagster job for ingesting and processing My Workflow data."""
    transformation_result = my_workflow_transform_op(my_workflow_ingestion_op())


def load_my_workflow_job():
    """Load the My Workflow job with default configuration.

    Returns:
        Configured My Workflow job
    """
    # Load configuration from file
    from dataflow.shared.config import load_workflow_config

    config_dict = load_workflow_config("my_workflow")

    return my_workflow_job.with_resources(
        resource_defs={
            "my_workflow_config": MyWorkflowResource(
                url=config_dict["source"]["url"],
                auth_token=config_dict["source"]["auth"]["token"],
                # Other parameters
            ),
        }
    )
```

#### Step 7: Update **init**.py

Update the `__init__.py` file to expose components and register the workflow:

```python
"""My Workflow for DataFlow.

This workflow ingests data from Example API and transforms it for analytics.
"""

from dataflow.workflows.my_workflow.assets import (
    MyWorkflowAssetsConfig,
    my_workflow_raw_data,
    my_workflow_transformed_data,
)
from dataflow.workflows.my_workflow.dagster_job import (
    MyWorkflowResource,
    load_my_workflow_job,
    my_workflow_job,
)
from dataflow.workflows.my_workflow.ingestion import (
    MyWorkflowConfig,
    run_my_workflow_ingestion,
)
from dataflow.workflows.my_workflow.transform import transform_my_workflow_data

__all__ = [
    "my_workflow_job",
    "load_my_workflow_job",
    "run_my_workflow_ingestion",
    "transform_my_workflow_data",
    "MyWorkflowConfig",
    "MyWorkflowResource",
    "my_workflow_raw_data",
    "my_workflow_transformed_data",
    "MyWorkflowAssetsConfig",
]
```

#### Step 8: Add Assets to Dagster Repository

To register your workflow's assets in the Dagster repository, update `src/dataflow/dagster_repo.py`:

```python
# In the collect_assets function
def collect_assets() -> List[AssetsDefinition]:
    """Collect assets from all workflows."""
    return [
        # Existing assets...
        my_workflow_raw_data,
        my_workflow_transformed_data,
    ]
```

### Testing Your Workflow

Test your workflow with the following commands:

```bash
# Run the workflow via CLI
python -m dataflow.cli workflow run my_workflow

# Run tests
python -m pytest src/dataflow/workflows/my_workflow/tests/
```

### Workflow Registration and Discovery

Your workflow is automatically discovered and registered with Dagster when:

1. You apply the `@register_workflow` decorator to your job function
2. Your module is imported by the dynamic discovery in `dagster_repo.py`

This registration makes your workflow available through both:

1. The Dagster UI at `http://localhost:3000`
2. The DataFlow CLI: `python -m dataflow.cli workflow run my_workflow`
3. The DataFlow API: `GET /api/workflows` and `POST /api/workflows/my_workflow/run`

### Best Practices

1. **Configuration Management**: Use `config.yaml` for static configuration and environment variables for secrets
2. **Error Handling**: Add proper error handling in ingestion and transformation code
3. **Logging**: Use the platform's logging utilities (`get_logger`) for consistent logs
4. **Testing**: Write unit tests for ingestion and transformation logic, and integration tests for the entire workflow
5. **Documentation**: Document your workflow in code comments and README files
6. **Type Hints**: Use Python type hints for better code quality and IDE support
