# Nightscout DBT Models

This directory contains DBT models for transforming raw Nightscout data into analytics-ready tables.

## Models

- `readings.sql` - Processes raw glucose readings data
- `treatments.sql` - Processes raw treatment events data
- `daily_summary.sql` - Aggregates readings and treatments into daily summaries

## Dependencies

These models expect raw data to be available in a source called `raw_data` with the following tables:

- `nightscout_entries` - Raw glucose readings
- `nightscout_treatments` - Raw treatment events
- `nightscout_profiles` - Raw profile data

## Usage

Run these models using the DBT CLI:

```bash
cd dbt
dbt run --select nightscout
```

Or via the DATAFLOW CLI:

```bash
dataflow workflow run nightscout --dbt-only
```

## Data Dictionary

See `schema.yml` for detailed documentation of each model and column.
