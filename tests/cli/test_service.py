import subprocess
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dataflow.cli.commands.service import (
    restart_services,
    run_docker_compose,
    service_logs,
    service_status,
    start_services,
    stop_services,
    validate_services,
)


@pytest.fixture
def runner():
    """Provides a test CLI runner."""
    return CliRunner()


def test_validate_services_all_flag():
    """Test validate_services with all flag set."""
    target_services, valid = validate_services([], True, "test")
    assert valid is True
    assert target_services == []


def test_validate_services_with_services():
    """Test validate_services with service names provided."""
    target_services, valid = validate_services(["api", "dagster"], False, "test")
    assert valid is True
    assert target_services == ["api", "dagster"]


def test_validate_services_no_services_no_all():
    """Test validate_services with neither services nor all flag."""
    target_services, valid = validate_services([], False, "test")
    assert valid is False
    assert target_services == []


@patch("dataflow.cli.commands.service.run_docker_compose")
@patch("dataflow.cli.commands.service.validate_services")
def test_start_services_all(mock_validate_services, mock_run_docker_compose, runner):
    """Test start_services with all flag."""
    mock_validate_services.return_value = ([], True)

    # Test with --all
    runner.invoke(start_services, ["--all"])
    mock_validate_services.assert_called_once_with((), True, "start")
    mock_run_docker_compose.assert_called_once_with(["up"])

    # Reset mocks for the next test
    mock_validate_services.reset_mock()
    mock_run_docker_compose.reset_mock()

    # Test with --all and --detach
    runner.invoke(start_services, ["--all", "--detach"])
    mock_validate_services.assert_called_once_with((), True, "start")
    mock_run_docker_compose.assert_called_once_with(["up", "-d"])


@patch("dataflow.cli.commands.service.run_docker_compose")
@patch("dataflow.cli.commands.service.validate_services")
def test_start_services_specific(mock_validate_services, mock_run_docker_compose, runner):
    """Test start_services with specific services."""
    mock_validate_services.return_value = (["api", "dagster"], True)

    # Test with specific services
    runner.invoke(start_services, ["api", "dagster"])
    mock_validate_services.assert_called_once_with(("api", "dagster"), False, "start")
    mock_run_docker_compose.assert_called_once_with(["up", "api", "dagster"])


@patch("dataflow.cli.commands.service.run_docker_compose")
@patch("dataflow.cli.commands.service.validate_services")
def test_stop_services(mock_validate_services, mock_run_docker_compose, runner):
    """Test stop_services command."""
    mock_validate_services.return_value = ([], True)

    # Test with --all
    runner.invoke(stop_services, ["--all"])
    mock_validate_services.assert_called_once_with((), True, "stop")
    mock_run_docker_compose.assert_called_once_with(["stop"])


@patch("dataflow.cli.commands.service.run_docker_compose")
def test_service_status(mock_run_docker_compose, runner):
    """Test service_status command."""
    runner.invoke(service_status)
    mock_run_docker_compose.assert_called_once_with(["ps"])


@patch("dataflow.cli.commands.service.run_docker_compose")
@patch("dataflow.cli.commands.service.validate_services")
def test_restart_services(mock_validate_services, mock_run_docker_compose, runner):
    """Test restart_services command."""
    mock_validate_services.return_value = (["api"], True)

    runner.invoke(restart_services, ["api"])
    mock_validate_services.assert_called_once_with(("api",), False, "restart")
    mock_run_docker_compose.assert_called_once_with(["restart", "api"])


@patch("dataflow.cli.commands.service.run_docker_compose")
@patch("dataflow.cli.commands.service.validate_services")
def test_service_logs(mock_validate_services, mock_run_docker_compose, runner):
    """Test service_logs command."""
    mock_validate_services.return_value = (["api"], True)

    # Test basic logs command
    runner.invoke(service_logs, ["api"])
    mock_validate_services.assert_called_once_with(("api",), False, "view logs for")
    mock_run_docker_compose.assert_called_once_with(["logs", "--tail", "100", "api"])

    # Reset mocks
    mock_validate_services.reset_mock()
    mock_run_docker_compose.reset_mock()

    # Test with follow flag
    runner.invoke(service_logs, ["api", "--follow"])
    mock_validate_services.assert_called_once_with(("api",), False, "view logs for")
    mock_run_docker_compose.assert_called_once_with(["logs", "--follow", "--tail", "100", "api"])


@patch("subprocess.run")
def test_run_docker_compose_success(mock_subprocess_run):
    """Test run_docker_compose with successful command."""
    mock_subprocess_run.return_value.stdout = "Success"
    mock_subprocess_run.return_value.stderr = ""

    result = run_docker_compose(["ps"])

    mock_subprocess_run.assert_called_once()
    assert result is True


@patch("subprocess.run")
def test_run_docker_compose_file_not_found(mock_subprocess_run):
    """Test run_docker_compose with FileNotFoundError."""
    mock_subprocess_run.side_effect = FileNotFoundError()

    result = run_docker_compose(["ps"])

    mock_subprocess_run.assert_called_once()
    assert result is False


@patch("subprocess.run")
def test_run_docker_compose_command_error(mock_subprocess_run):
    """Test run_docker_compose with command error."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "docker-compose ps")

    result = run_docker_compose(["ps"])

    mock_subprocess_run.assert_called_once()
    assert result is False
