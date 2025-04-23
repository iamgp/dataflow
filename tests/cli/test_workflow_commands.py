"""Tests for CLI workflow commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dataflow.cli.commands.workflow import workflow_group


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


def test_list_workflows(cli_runner):
    """Test the list-workflows command."""
    with patch("dataflow.workflows.registry.workflow_registry") as mock_registry:
        mock_registry.return_value = {
            "nightscout": {
                "name": "nightscout",
                "description": "Nightscout data pipeline",
                "config_schema": {},
            }
        }

        result = cli_runner.invoke(workflow_group, ["list"])
        assert result.exit_code == 0
        assert "nightscout" in result.output


def test_run_workflow(cli_runner):
    """Test the run-workflow command."""
    with patch("dataflow.workflows.registry.workflow_registry") as mock_registry:
        mock_registry.return_value = {
            "nightscout": {
                "name": "nightscout",
                "description": "Nightscout data pipeline",
                "config_schema": {},
            }
        }

        result = cli_runner.invoke(workflow_group, ["run", "nightscout"])
        assert result.exit_code == 0
        assert "Running workflow: nightscout" in result.output


def test_run_workflow_error(cli_runner):
    """Test error handling in run-workflow command."""
    with patch("dataflow.workflows.registry.workflow_registry") as mock_registry:
        mock_registry.return_value = {}

        result = cli_runner.invoke(workflow_group, ["run", "invalid-workflow"])
        assert result.exit_code == 0  # The command handles errors gracefully
        assert "not found" in result.output


def test_dbt_command(cli_runner):
    """Test the dbt command."""
    with patch("dataflow.workflows.registry.get_workflow_path") as mock_path:
        mock_path.return_value = "/tmp/workflows/nightscout"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            result = cli_runner.invoke(workflow_group, ["dbt", "nightscout"])
            assert result.exit_code == 0
            assert "Building DBT models" in result.output


def test_evidence_command(cli_runner):
    """Test the evidence command."""
    with patch("dataflow.workflows.registry.get_workflow_path") as mock_path:
        mock_path.return_value = "/tmp/workflows/nightscout"
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            result = cli_runner.invoke(workflow_group, ["evidence", "nightscout"])
            assert result.exit_code == 0
            assert "Building Evidence dashboards" in result.output
