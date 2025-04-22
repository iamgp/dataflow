"""Tests for the ingestion module."""

from unittest.mock import patch

import pytest

from dataflow.templates.workflow_template.ingestion import extract_data

# Import shared test utilities
from tests.utils import unit_test, workflow_test


@unit_test
@workflow_test
def test_extract_data_returns_list():
    """Test that extract_data returns a list."""
    source_config = {"name": "test_source"}

    result = extract_data(source_config)

    assert isinstance(result, list)


@unit_test
@workflow_test
@patch("dataflow.templates.workflow_template.ingestion.log")
def test_extract_data_logs_info(mock_log):
    """Test that extract_data logs info about the extraction."""
    source_config = {"name": "test_source"}

    extract_data(source_config)

    mock_log.info.assert_called_once()
    assert "test_source" in mock_log.info.call_args[1]["source"]


@unit_test
@workflow_test
def test_extract_data_handles_empty_config():
    """Test that extract_data handles an empty config without errors."""
    source_config = {}

    result = extract_data(source_config)

    assert isinstance(result, list)


@unit_test
@workflow_test
@pytest.mark.parametrize(
    "source_config,expected_error",
    [
        (None, TypeError),  # None is not a dict
        (123, TypeError),  # Integer is not a dict
    ],
)
def test_extract_data_invalid_config(source_config, expected_error):
    """Test that extract_data raises appropriate errors for invalid configs."""
    with pytest.raises(expected_error):
        extract_data(source_config)
