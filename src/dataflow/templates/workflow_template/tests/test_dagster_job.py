"""Tests for the workflow Dagster job."""

from unittest.mock import MagicMock, patch

from dagster import build_op_context

from dataflow.templates.workflow_template.dagster_job import (
    extract_op,
    load_op,
    transform_op,
    workflow_job,
)

# Import shared test utilities
from tests.utils import unit_test, workflow_test


@unit_test
@workflow_test
@patch("dataflow.templates.workflow_template.dagster_job.extract_data")
def test_extract_op(mock_extract_data):
    """Test that extract_op calls extract_data with the right config."""
    # Set up the mock
    mock_extract_data.return_value = [{"id": 1, "value": 42}]

    # Set up the context
    context = build_op_context(op_config={"source": {"name": "test_source"}})

    # Run the op
    result = extract_op(context)

    # Check the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == 1

    # Check the mock was called with the right config
    mock_extract_data.assert_called_once_with({"name": "test_source"})


@unit_test
@workflow_test
@patch("dataflow.templates.workflow_template.dagster_job.transform_data")
def test_transform_op(mock_transform_data):
    """Test that transform_op calls transform_data with the right input."""
    # Set up the mock
    mock_transform_data.return_value = [
        {"id": 1, "value": 42, "processed_at": "2023-01-01T00:00:00Z"}
    ]

    # Set up the context
    context = build_op_context()

    # Set up the input data
    input_data = [{"id": 1, "value": 42}]

    # Run the op
    result = transform_op(context, input_data)

    # Check the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert "processed_at" in result[0]

    # Check the mock was called with the right input
    mock_transform_data.assert_called_once_with(input_data)


@unit_test
@workflow_test
def test_load_op():
    """Test that load_op logs the right message."""
    # Set up the context with a mock logger
    context = build_op_context()
    context.log.info = MagicMock()

    # Set up the input data
    input_data = [{"id": 1, "value": 42}]

    # Run the op
    load_op(context, input_data)

    # Check the log message
    context.log.info.assert_called_once()
    assert "Loaded 1 records" in context.log.info.call_args[0][0]


@unit_test
@workflow_test
def test_workflow_job():
    """Test that the workflow job is properly defined."""
    # Check that the job exists and has the expected name
    assert hasattr(workflow_job, "name")
    assert workflow_job.name == "workflow_job"
