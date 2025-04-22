# DBT Models

This directory contains DBT models for the workflow. DBT models are used to transform raw data into analytics-ready tables.

## Structure

- `schema.yml` - Model schema definitions
- `sources.yml` - Data source definitions
- `models/` - SQL model files

## Usage

Models should follow DBT best practices:

- Use the source macro for raw data references: `{{ source('schema', 'table') }}`
- Use the ref macro for model dependencies: `{{ ref('model_name') }}`
- Document all models in schema.yml files

## Example Models

For this workflow, we recommend implementing the following models:

1. `staging/` - Stage raw data with minimal transformations
2. `intermediate/` - Build reusable data structures
3. `mart/` - Build end-user facing views and tables

## Testing

DBT tests should be defined in the schema.yml file using standard test types:

- not_null
- unique
- relationships
- accepted_values

Custom tests can be added to the `tests/` directory.
