# Working with Workflows

Dataflow uses a workflow-centric approach where each data pipeline is organized as a self-contained workflow. This document explains how to work with workflows, including their Evidence dashboards.

## Workflow Structure

Each workflow follows this directory structure:

```
src/dataflow/workflows/<workflow_name>/
  __init__.py
  ingestion.py      # Data extraction logic
  transform.py      # Data transformation logic
  assets.py         # Dagster assets/resources (optional)
  dagster_job.py    # Dagster job/op definitions, registry decorator
  config.yaml       # Workflow-specific config
  dbt/              # DBT models for this workflow
  evidence/         # Evidence dashboards for this workflow
  tests/            # Unit and integration tests for this workflow
```

## Setting Up a New Workflow

To create a new workflow, follow these steps:

1. Create the workflow directory structure:

```bash
mkdir -p src/dataflow/workflows/my_workflow/{evidence,dbt,tests}
touch src/dataflow/workflows/my_workflow/__init__.py
touch src/dataflow/workflows/my_workflow/ingestion.py
touch src/dataflow/workflows/my_workflow/transform.py
touch src/dataflow/workflows/my_workflow/dagster_job.py
touch src/dataflow/workflows/my_workflow/config.yaml
```

2. Initialize the Evidence dashboard for the workflow:

```bash
docker run -v=$(pwd)/src/dataflow/workflows/my_workflow/evidence:/evidence-workspace -it --rm evidencedev/devenv:latest --init
```

3. Implement your workflow:
   - Add data extraction logic in `ingestion.py`
   - Add data transformation logic in `transform.py`
   - Define Dagster assets/resources in `assets.py` (optional)
   - Wire everything together in `dagster_job.py`
   - Add workflow-specific configuration in `config.yaml`
   - Add DBT models in the `dbt/` directory
   - Develop the Evidence dashboard in the `evidence/` directory
   - Add tests in the `tests/` directory

## Working with Evidence Dashboards

Each workflow has its own Evidence dashboard in the `evidence/` directory. These dashboards can access data processed by the workflow and present it to users.

To work with a workflow's Evidence dashboard:

1. Start the Evidence service:

```bash
docker-compose up -d evidence
```

2. Access the dashboard at http://localhost:9000

3. Develop the dashboard by editing files in the workflow's `evidence/` directory:

   - Create pages in `evidence/pages/`
   - Define data sources in `evidence/sources/`
   - Add custom components in `evidence/components/` (optional)

4. Evidence will automatically reload when you make changes to the dashboard files.

## Running Workflows

Workflows are orchestrated by Dagster. To run a workflow:

1. Start the Dagster service:

```bash
docker-compose up -d dagster
```

2. Access the Dagster UI at http://localhost:3000

3. Navigate to the workflow job and run it manually or set up a schedule.

For more details on creating workflows, see the [Workflow Authoring Checklist](workflow-authoring.md).
