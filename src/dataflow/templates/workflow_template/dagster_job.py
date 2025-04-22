"""Dagster job definitions for the workflow.

This module contains Dagster job and op definitions and the workflow registration.
"""

from typing import Any

from dagster import OpExecutionContext, job, op

from dataflow.shared.logging import get_logger
from dataflow.templates.workflow_template.ingestion import extract_data
from dataflow.templates.workflow_template.transform import transform_data
from dataflow.workflows.registry import register_workflow

log = get_logger("workflow.dagster_job")


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
    # TODO: Implement loading logic
    # Examples:
    # - Database insert/update
    # - File writing
    # - API calls

    context.log.info(f"Loaded {len(transformed_data)} records")


@register_workflow(
    name="workflow_template",
    metadata={
        "description": "Template workflow for data processing",
        "owner": "data-team",
        "schedule": "0 0 * * *",  # Daily at midnight
    },
)
@job
def workflow_job():
    """Main job for the workflow.

    This job orchestrates the extract, transform, and load operations.
    """
    load_op(transform_op(extract_op()))
