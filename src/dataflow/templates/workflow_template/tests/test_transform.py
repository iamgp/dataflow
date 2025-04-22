"""Tests for the transform module."""

from unittest.mock import patch

import pytest

from dataflow.templates.workflow_template.transform import transform_data

# Import shared test utilities
from tests.utils import unit_test, workflow_test


@unit_test
@workflow_test
def test_transform_data_returns_list():
    """Test that transform_data returns a list."""
    input_data = [{"id": 1, "value": 42}]

    result = transform_data(input_data)

    assert isinstance(result, list)


@unit_test
@workflow_test
def test_transform_data_preserves_original_fields():
    """Test that transform_data preserves original fields."""
    input_data = [{"id": 1, "value": 42}]

    result = transform_data(input_data)

    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["value"] == 42


@unit_test
@workflow_test
def test_transform_data_adds_processed_at():
    """Test that transform_data adds processed_at field."""
    input_data = [{"id": 1, "value": 42}]

    result = transform_data(input_data)

    assert len(result) == 1
    assert "processed_at" in result[0]


@unit_test
@workflow_test
@patch("dataflow.templates.workflow_template.transform.log")
def test_transform_data_logs_info(mock_log):
    """Test that transform_data logs info about the transformation."""
    input_data = [{"id": 1, "value": 42}]

    transform_data(input_data)

    mock_log.info.assert_called_once()


@unit_test
@workflow_test
def test_transform_data_handles_empty_input():
    """Test that transform_data handles empty input without errors."""
    input_data = []

    result = transform_data(input_data)

    assert isinstance(result, list)
    assert len(result) == 0


@unit_test
@workflow_test
@pytest.mark.parametrize(
    "input_data,expected_error",
    [
        (None, TypeError),  # None is not a list
        (123, TypeError),  # Integer is not a list
        ({}, TypeError),  # Dict is not a list
    ],
)
def test_transform_data_invalid_input(input_data, expected_error):
    """Test that transform_data raises appropriate errors for invalid inputs."""
    with pytest.raises(expected_error):
        transform_data(input_data)
