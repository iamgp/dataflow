# Workflow System Foundation

This document provides comprehensive information about DATAFLOW's workflow system foundation, including templates, registry integration, and configuration.

## 1. Workflow Directory Template

The workflow system is designed around a standardized directory structure to ensure consistency and ease of use. Each workflow follows the same structure, making it easy to understand and extend.

### 1.1 Directory Structure

```
src/dataflow/workflows/<workflow_name>/
├── __init__.py                # Package initialization
├── ingestion.py               # Data extraction logic
├── transform.py               # Data transformation logic
├── assets.py                  # Dagster assets (optional)
├── dagster_job.py             # Dagster job definitions and workflow registration
├── config.yaml                # Workflow configuration
├── dbt/                       # DBT models
│   ├── schema.yml             # Model schema definitions
│   ├── sources.yml            # Data source definitions
│   └── models/                # SQL model files
├── evidence/                  # Evidence dashboards
│   ├── index.md               # Main dashboard
│   └── components/            # Dashboard components
└── tests/                     # Unit and integration tests
    ├── test_ingestion.py      # Tests for ingestion logic
    ├── test_transform.py      # Tests for transformation logic
    └── test_dagster_job.py    # Tests for Dagster job
```

### 1.2 Template Usage

To create a new workflow, you can use the workflow template provided in `src/dataflow/templates/workflow_template/`.

The template includes:

- Basic structure for data extraction (`ingestion.py`)
- Data transformation logic (`transform.py`)
- Dagster asset definitions (`assets.py`)
- Dagster job registration (`dagster_job.py`)
- Configuration file (`config.yaml`)
- DBT models (`dbt/`)
- Evidence dashboards (`evidence/`)
- Tests (`tests/`)

### 1.3 Example Workflow

An example workflow is provided in `src/dataflow/workflows/example_workflow/`. This workflow demonstrates best practices and patterns for implementing a complete workflow.

Key features of the example workflow:

- Flexible data extraction from multiple source types (API, file, mock)
- Robust data transformation with error handling
- Dagster job integration with environment variable overrides
- Configuration with environment variable support
- DBT models for data transformation
- Evidence dashboards for data visualization
- Comprehensive tests

## 2. Workflow Registry Integration

The workflow registry is a central component that enables workflow discovery and management.

### 2.1 Registry System

The workflow registry is implemented in `src/dataflow/workflows/registry.py`. It provides:

- A global registry for all workflows
- A decorator for registering workflows
- Discovery logic for the CLI and API

### 2.2 Registry Decorator

All workflows are registered using the `@register_workflow` decorator:

```python
from dataflow.workflows.registry import register_workflow

@register_workflow(
    name="example_workflow",
    metadata={
        "description": "Example workflow for data processing",
        "owner": "data-team",
        "schedule": "0 * * * *",  # Every hour
        "tags": ["example", "template"],
    },
)
@job
def example_workflow_job():
    """Main job for the example workflow."""
    load_op(transform_op(extract_op()))
```

This decorator automatically adds the workflow to the registry, making it discoverable by the Dagster repository, CLI, and API.

### 2.3 Discovery Mechanism

Workflows are discovered through:

1. `dataflow.dagster_repo.py`: Dynamically imports workflow modules, triggering registration
2. CLI commands: Lists and runs workflows via the registry
3. API endpoints: Exposes workflow information from the registry

## 3. Workflow Configuration

Each workflow has its own configuration file (`config.yaml`) with settings that control its behavior.

### 3.1 Configuration Structure

The configuration file follows a consistent structure:

```yaml
# Data Source Configuration
source:
  name: "example_source"
  type: "api" # Options: api, file, database, mock
  api:
    url: "https://api.example.com/data"
    # ... API settings ...

# Data Processing Configuration
processing:
  batch_size: 1000
  # ... processing settings ...

# Output Configuration
output:
  # ... output settings ...

# Schedule Configuration
schedule:
  cron: "0 0 * * *" # Daily at midnight
  timezone: "UTC"
```

### 3.2 Configuration Management

Configuration is managed through the `dataflow.shared.config` module, which provides:

- Loading and parsing of YAML configuration files
- Environment variable substitution (`${ENV_VAR}`)
- Validation using Pydantic models
- Configuration caching

### 3.3 Configuration Access

Configurations can be accessed through:

1. **CLI**:

   ```bash
   dataflow config show example_workflow
   dataflow config validate example_workflow
   dataflow config list
   ```

2. **API**:

   ```
   GET /configs/
   GET /configs/example_workflow
   POST /configs/example_workflow/validate
   ```

3. **Python API**:

   ```python
   from dataflow.shared.config import config_manager

   # Load configuration
   config = config_manager.load_config("example_workflow")

   # Validate configuration
   from my_model import WorkflowConfigModel
   validated_config = config_manager.validate_config("example_workflow", WorkflowConfigModel)
   ```

## 4. Integrating Workflows

When creating a new workflow, follow these steps:

1. Create a new directory in `src/dataflow/workflows/` with your workflow name
2. Copy the contents from the workflow template
3. Implement your ingestion logic in `ingestion.py`
4. Implement your transformation logic in `transform.py`
5. Define and register your Dagster job in `dagster_job.py`
6. Create your configuration in `config.yaml`
7. Add DBT models in the `dbt/` directory
8. Create Evidence dashboards in the `evidence/` directory
9. Write tests in the `tests/` directory

Your workflow will be automatically discovered and available through the CLI and API.
