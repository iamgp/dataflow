# Example Workflow DBT Models

This directory contains DBT models for the example workflow.

## Models

- `staged_data.sql` - Initial staging of the extracted data
- `summary_table.sql` - Aggregated metrics by date

## Usage

Run these models using the DBT CLI:

```bash
cd dbt
dbt run --select example_workflow
```

Or via the DATAFLOW CLI:

```bash
dataflow workflow run example_workflow --dbt-only
```
