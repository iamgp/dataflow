# Extending DATAFLOW

This guide explains how to extend DATAFLOW with new workflows, DBT models, and Evidence dashboards.

## Adding New Workflows

### Overview

DATAFLOW is designed to be extended with custom workflows. Each workflow is a self-contained unit that can:

1. Extract data from a source
2. Transform the data
3. Load the data into the database
4. Visualize the data through Evidence

### Steps to Add a New Workflow

#### 1. Create the Workflow Directory Structure

```bash
mkdir -p src/dataflow/workflows/my_workflow/{evidence,dbt,tests}
touch src/dataflow/workflows/my_workflow/__init__.py
touch src/dataflow/workflows/my_workflow/ingestion.py
touch src/dataflow/workflows/my_workflow/transform.py
touch src/dataflow/workflows/my_workflow/dagster_job.py
touch src/dataflow/workflows/my_workflow/config.yaml
```

Alternatively, use the CLI command:

```bash
dataflow workflow init my_workflow
```

#### 2. Configure the Workflow

Edit the `config.yaml` file to define your workflow's configuration:

```yaml
workflow:
  name: "My Workflow"
  description: "Extracts and processes data from Source X"
  schedule: "0 0 * * *" # Daily at midnight (cron format)

ingestion:
  source:
    type: "api"
    url: "https://api.example.com/data"
    auth_type: "bearer_token"
  parameters:
    batch_size: 100
    max_retries: 3

transformation:
  stages:
    - name: "cleaning"
      options:
        remove_duplicates: true
    - name: "enrichment"
      options:
        add_timestamps: true
```

#### 3. Implement Data Ingestion

Edit the `ingestion.py` file to implement data extraction:

```python
from dataflow.shared.logging import get_logger
from dataflow.shared.config import load_config
from datetime import datetime
import httpx

logger = get_logger(__name__)

def extract_data(params: dict) -> dict:
    """
    Extract data from the source specified in the workflow config.

    Args:
        params: Dictionary of parameters for extraction

    Returns:
        Dictionary containing extracted data and metadata
    """
    config = load_config("my_workflow")
    source_config = config.get("ingestion", {}).get("source", {})

    logger.info(f"Extracting data from {source_config.get('type')}")

    # Example: API extraction
    if source_config.get("type") == "api":
        url = source_config.get("url")
        try:
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

                return {
                    "data": data,
                    "metadata": {
                        "source": source_config.get("type"),
                        "record_count": len(data),
                        "timestamp": datetime.now().isoformat()
                    }
                }
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            raise
    else:
        raise ValueError(f"Unsupported source type: {source_config.get('type')}")
```

#### 4. Implement Data Transformation

Edit the `transform.py` file to implement data transformation:

```python
from dataflow.shared.logging import get_logger
from dataflow.shared.config import load_config
from datetime import datetime
import pandas as pd

logger = get_logger(__name__)

def transform_data(data: dict) -> dict:
    """
    Transform extracted data according to workflow configuration.

    Args:
        data: Dictionary containing extracted data and metadata

    Returns:
        Dictionary with transformed data and updated metadata
    """
    config = load_config("my_workflow")
    transform_config = config.get("transformation", {})

    df = pd.DataFrame(data["data"])

    for stage in transform_config.get("stages", []):
        stage_name = stage.get("name")
        options = stage.get("options", {})

        logger.info(f"Running transformation stage: {stage_name}")

        # Implement transformation logic for each stage
        if stage_name == "cleaning":
            if options.get("remove_duplicates"):
                df = df.drop_duplicates()
        elif stage_name == "enrichment":
            if options.get("add_timestamps"):
                df["processed_at"] = datetime.now().isoformat()

    return {
        "data": df.to_dict(orient="records"),
        "metadata": {
            **data["metadata"],
            "transformation_stages": [s["name"] for s in transform_config.get("stages", [])]
        }
    }
```

#### 5. Create the Dagster Job

Edit the `dagster_job.py` file to define the Dagster job:

```python
from dagster import job, op, Output, In
from dataflow.workflows.registry import register_workflow

from .ingestion import extract_data
from .transform import transform_data

@op
def extract():
    return extract_data(params={})

@op
def transform(extract_result):
    return transform_data(extract_result)

@op
def load(transform_result):
    # Implement loading logic here
    # Example: Save to DuckDB
    from dataflow.shared.db import get_duckdb_connection

    data = transform_result["data"]
    table_name = "my_workflow_data"

    with get_duckdb_connection() as conn:
        # Create table if it doesn't exist
        # Insert data
        pass

    return {"status": "success", "record_count": len(data)}

@job
def my_workflow_job():
    load(transform(extract()))

# Register the workflow with DATAFLOW
register_workflow(
    workflow_id="my_workflow",
    job=my_workflow_job,
    description="My workflow for processing data from Source X"
)
```

#### 6. Write Tests

Create tests for your workflow in the `tests/` directory:

```python
# tests/test_ingestion.py
import pytest
from unittest.mock import patch, MagicMock
from my_workflow.ingestion import extract_data

def test_extract_data():
    # Mock config and HTTP response
    with patch("my_workflow.ingestion.load_config") as mock_config:
        mock_config.return_value = {
            "ingestion": {
                "source": {
                    "type": "api",
                    "url": "https://api.example.com/data"
                }
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": 1}, {"id": 2}]
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = extract_data({})

            assert "data" in result
            assert "metadata" in result
            assert result["metadata"]["record_count"] == 2
```

#### 7. Run and Test the Workflow

Run the workflow using the CLI:

```bash
dataflow workflow run my_workflow
```

## Adding DBT Models

### Overview

DATAFLOW uses DBT for data transformation and modeling. Each workflow can have its own DBT models.

### Steps to Add New DBT Models

#### 1. Create the DBT Model Files

Create SQL files in the workflow's `dbt/` directory:

```bash
mkdir -p src/dataflow/workflows/my_workflow/dbt/models
touch src/dataflow/workflows/my_workflow/dbt/models/my_model.sql
```

#### 2. Define the DBT Model

Example DBT model (`my_model.sql`):

```sql
{{ config(
    materialized = 'table',
    schema = 'my_workflow'
) }}

SELECT
    id,
    name,
    value,
    processed_at
FROM {{ source('my_workflow', 'raw_data') }}
WHERE value > 0
```

#### 3. Create Sources Definition

Create a `src/dataflow/workflows/my_workflow/dbt/models/sources.yml` file:

```yaml
version: 2

sources:
  - name: my_workflow
    schema: public
    tables:
      - name: raw_data
        description: Raw data extracted from the source
```

#### 4. Integrate with the Workflow

Update your workflow's Dagster job to run the DBT models:

```python
from dagster import job, op
from dagster_dbt import dbt_cli_resource, dbt_run_op

# ... existing code ...

@op
def run_dbt_models(load_result):
    # This assumes load_result is successful
    dbt_resource = dbt_cli_resource.configured(
        {"project_dir": "./src/dataflow/workflows/my_workflow/dbt"}
    )

    dbt_run_op(
        dbt_resource=dbt_resource,
        select="my_workflow_models"
    )

    return {"status": "success", "models_run": ["my_model"]}

@job
def my_workflow_job():
    run_dbt_models(load(transform(extract())))
```

## Adding Evidence Dashboards

### Overview

DATAFLOW uses Evidence for data visualization. Each workflow can have its own Evidence dashboards.

### Steps to Add New Evidence Dashboards

#### 1. Initialize the Evidence Project

If not already initialized:

```bash
docker run -v=$(pwd)/src/dataflow/workflows/my_workflow/evidence:/evidence-workspace -it --rm evidencedev/devenv:latest --init
```

#### 2. Create the Dashboard Page

Create a Markdown file in `src/dataflow/workflows/my_workflow/evidence/pages/index.md`:

```markdown
---
title: My Workflow Dashboard
---

# My Workflow Dashboard

<sql query="select * from my_workflow.my_model" />

<BigValue
  data={query}
  value="record_count"
  title="Total Records"
/>

<BarChart
  data={query}
  x="category"
  y="value"
  title="Values by Category"
/>

## Data Details

<DataTable data={query} />
```

#### 3. Configure Data Sources

Create or update `src/dataflow/workflows/my_workflow/evidence/sources/duckdb.js`:

```javascript
export default {
  duckdb: {
    database:
      process.env.EVIDENCE_DUCKDB_PATH ||
      "../../../../../.duckdb/dataflow.duckdb",
    credentials: {
      // No credentials needed for file-based DuckDB
    },
  },
};
```

#### 4. Access the Dashboard

Start the Evidence service and access your dashboard:

```bash
dataflow service start evidence
```

Access the dashboard at http://localhost:9000/my-workflow

## Best Practices

### Workflow Design

- Keep workflows focused on a single data source or domain
- Follow the single responsibility principle
- Use type hints consistently
- Handle errors gracefully with appropriate logging
- Make configuration explicit and validate it early

### DBT Models

- Use consistent naming conventions
- Document models with comments and descriptions
- Create tests for your models
- Use incremental models for large datasets
- Keep transformations in DBT when possible

### Evidence Dashboards

- Create intuitive and user-friendly dashboards
- Add clear titles and descriptions
- Use appropriate visualizations for different data types
- Group related metrics and charts together
- Consider different user personas when designing dashboards

## Troubleshooting

### Common Workflow Issues

- **Configuration errors**: Verify the structure of your `config.yaml`
- **Data extraction failures**: Check network connectivity and API availability
- **Transformation errors**: Check for data type mismatches or missing columns

### DBT Issues

- **Model compilation errors**: Check SQL syntax and references
- **Missing sources**: Verify source definitions in `sources.yml`
- **Performance issues**: Consider optimizing SQL or using incremental models

### Evidence Issues

- **Data connection errors**: Check database connection configuration
- **Chart rendering issues**: Verify data format and column names
- **Missing data**: Check SQL queries and table references
