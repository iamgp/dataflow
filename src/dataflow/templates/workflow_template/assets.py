"""Dagster assets for the workflow.

This module contains Dagster asset definitions and resources.
These assets are optional and can be used to define data dependencies.
"""

from typing import Any

from dagster import (
    AssetOut,
    Output,
    asset,
    multi_asset,
)

from dataflow.shared.logging import get_logger
from dataflow.templates.workflow_template.transform import transform_data

log = get_logger("workflow.assets")


@asset
def raw_data_asset(context) -> list[dict[str, Any]]:
    """Asset representing raw ingested data.

    This asset is responsible for data extraction.

    Args:
        context: Dagster execution context

    Returns:
        List of raw data records
    """
    from dataflow.templates.workflow_template.ingestion import extract_data

    # Get config from context
    source_config = context.op_config.get("source", {})

    # Extract data
    data = extract_data(source_config)

    context.log.info(f"Extracted {len(data)} raw records")
    return data


@asset(deps=[raw_data_asset])
def transformed_data_asset(context, raw_data_asset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Asset representing transformed data.

    This asset is responsible for data transformation.

    Args:
        context: Dagster execution context
        raw_data_asset: Raw data from the previous asset

    Returns:
        List of transformed data records
    """
    # Transform data
    transformed = transform_data(raw_data_asset)

    context.log.info(f"Transformed {len(transformed)} records")
    return transformed


@multi_asset(
    outs={
        "output_table_1": AssetOut(),
        "output_table_2": AssetOut(),
    },
    deps=[transformed_data_asset],
)
def output_tables(context, transformed_data_asset: list[dict[str, Any]]):
    """Multiple assets representing different output tables.

    This asset is responsible for splitting transformed data into multiple outputs.

    Args:
        context: Dagster execution context
        transformed_data_asset: Transformed data from the previous asset

    Returns:
        Multiple outputs for different destination tables
    """
    # Example of splitting data into multiple tables
    table_1_data = [r for r in transformed_data_asset if r.get("type") == "type1"]
    table_2_data = [r for r in transformed_data_asset if r.get("type") == "type2"]

    context.log.info(
        f"Split data into {len(table_1_data)} type1 and {len(table_2_data)} type2 records"
    )

    yield Output(table_1_data, output_name="output_table_1")
    yield Output(table_2_data, output_name="output_table_2")
