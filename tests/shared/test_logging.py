import os
from unittest.mock import patch

from dataflow.shared.logging import get_logger, setup_logging


def test_setup_logging():
    """Test that setup_logging works without errors."""
    # Test with default parameters
    logger = setup_logging()
    assert logger is not None

    # Test with explicit parameters
    logger = setup_logging(
        level="DEBUG",
        json_logs=True,
        log_file="test_log.log",
        component="test",
    )
    assert logger is not None

    # Cleanup test log file if created
    if os.path.exists("test_log.log"):
        os.remove("test_log.log")


def test_get_logger():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test.logger")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


@patch("dataflow.shared.logging.structlog.get_logger")
def test_logger_with_context(mock_get_logger):
    """Test that context is correctly added to loggers."""
    # Setup mock
    mock_get_logger.return_value = mock_get_logger

    # Get logger with context
    _ = get_logger("test.context", workflow="test_workflow", user="test_user")

    # Verify the context was added correctly
    mock_get_logger.assert_called_once_with(name="test.context")
    mock_get_logger.bind.assert_called_once_with(workflow="test_workflow", user="test_user")
