"""Dagster job definitions for the example workflow.

This module contains Dagster job and op definitions and the workflow registration.
"""

import os
from typing import Any

from dagster import OpExecutionContext, job, op

from dataflow.shared.logging import get_logger
from dataflow.workflows.example_workflow.ingestion import extract_data
from dataflow.workflows.example_workflow.transform import transform_data
from dataflow.workflows.registry import register_workflow

log = get_logger("example_workflow.dagster_job")


@op
def extract_op(context: OpExecutionContext) -> list[dict[str, Any]]:
    """Extract data from source.

    Args:
        context: Dagster execution context

    Returns:
        List of raw data records
    """
    # Get config from context
    source_config = context.op_config.get("source", {})

    # Check for mock data mode
    if os.environ.get("EXAMPLE_WORKFLOW_MOCK_DATA", "false").lower() == "true":
        source_config = {"type": "mock", "mock": {"count": 20}}
        context.log.info("Using mock data instead of configured source")

    # Extract data
    data = extract_data(source_config)

    context.log.info(f"Extracted {len(data)} raw records")
    return data


@op
def transform_op(
    context: OpExecutionContext, raw_data: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Transform raw data.

    Args:
        context: Dagster execution context
        raw_data: Raw data from the extract_op

    Returns:
        List of transformed data records
    """
    # Transform data
    transformed = transform_data(raw_data)

    context.log.info(f"Transformed {len(transformed)} records")
    return transformed


@op
def load_op(context: OpExecutionContext, transformed_data: list[dict[str, Any]]) -> None:
    """Load transformed data.

    Args:
        context: Dagster execution context
        transformed_data: Transformed data from the transform_op
    """
    # TODO: Implement actual loading logic here
    # This could involve:
    # - Writing to a database (using dataflow.shared.db)
    # - Writing to files (using dataflow.shared.minio)
    # - Calling an API

    # For now, just log what would be loaded
    if not transformed_data:
        context.log.warning("No data to load")
        return

    # Group data by type
    type1_count = len([r for r in transformed_data if r.get("type") == "type1"])
    type2_count = len([r for r in transformed_data if r.get("type") == "type2"])
    other_count = len([r for r in transformed_data if r.get("type") not in ("type1", "type2")])

    context.log.info(
        f"Would load {len(transformed_data)} records",
        extra={"type1_count": type1_count, "type2_count": type2_count, "other_count": other_count},
    )


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
    """Main job for the example workflow.

    This job orchestrates the extract, transform, and load operations.
    """
    load_op(transform_op(extract_op()))
