import logging
import os
import sys
import threading
from typing import Any

import structlog
import structlog.types
from structlog.stdlib import BoundLogger

# Lock for thread-safe logging configuration
_logging_lock = threading.Lock()

# Track if logging has been configured
_LOGGING_CONFIGURED = False

# --- Structlog Processors --- #
# These processors format the log record before it gets rendered.


def add_log_level_as_severity(
    logger: Any, method_name: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    """Adds Google Cloud Logging severity based on log level."""
    severity_map = {
        "trace": "DEBUG",
        "debug": "DEBUG",
        "info": "INFO",
        "success": "INFO",
        "warning": "WARNING",
        "warn": "WARNING",
        "error": "ERROR",
        "exception": "ERROR",
        "critical": "CRITICAL",
        "fatal": "CRITICAL",
        "notice": "INFO",
    }
    # Get severity from map, defaulting to INFO for unknown levels
    level = method_name.lower()
    event_dict["severity"] = severity_map.get(level, "INFO")
    return event_dict


def add_component_context(
    logger: Any, method_name: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    """Adds component name to logs based on logger name."""
    if "component" not in event_dict:
        logger_name = event_dict.get("logger", "")
        if logger_name.startswith("dataflow."):
            parts = logger_name.split(".")
            if len(parts) > 1:
                event_dict["component"] = parts[1]  # e.g., cli, service, etc.
    return event_dict


shared_processors: list[structlog.types.Processor] = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    add_log_level_as_severity,
    add_component_context,
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.dict_tracebacks,
]


# --- Logging Configuration --- #
def setup_logging(
    level: str = "INFO",
    json_logs: bool = True,
    log_file: str | None = None,
    component: str = "general",
):
    """Configures structlog for structured logging (JSON or Console).

    Redirects standard library logging to structlog.

    Args:
        level: The minimum logging level (e.g., "INFO", "DEBUG").
        json_logs: Whether to output logs in JSON format.
        log_file: Optional path to log file.
        component: Component name to add to log context.

    Returns:
        A structured logger instance
    """
    global _LOGGING_CONFIGURED
    with _logging_lock:
        # Track if logging has been configured
        if _LOGGING_CONFIGURED:
            return get_logger(f"dataflow.{component}")
        _LOGGING_CONFIGURED = True

        log_level_str = os.environ.get("LOG_LEVEL", level).upper()
        # Validate log level
        valid_levels = {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
        }
        log_level = valid_levels.get(log_level_str, logging.INFO)
        if log_level_str not in valid_levels:
            print(f"WARNING: Invalid log level '{log_level_str}', defaulting to INFO")

        use_json = os.environ.get("LOG_JSON_FORMAT", str(json_logs)).lower() == "true"

        # Determine the final renderer
        final_processor = (
            structlog.processors.JSONRenderer()
            if use_json
            else structlog.dev.ConsoleRenderer(colors=True)
        )

        # Configure structlog
        structlog.configure(
            processors=shared_processors
            + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure the stdlib root logger to use structlog
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=final_processor,
        )

        # Add stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        handlers = [stdout_handler]

        # Add file handler if specified
        if log_file:
            try:
                # Create logs directory if it doesn't exist
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                from logging.handlers import RotatingFileHandler

                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10 * 1024 * 1024,  # rotate when file >10 MB
                    backupCount=5,  # keep 5 archived logs
                )
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)
            except (PermissionError, OSError) as e:
                print(f"WARNING: Could not set up log file at '{log_file}': {e}")
                # Continue without file logging

        # Configure root logger
        root_logger = logging.getLogger()
        # Remove existing handlers to avoid duplication
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

        for handler in handlers:
            root_logger.addHandler(handler)

        root_logger.setLevel(log_level)

        # Configure structlog default context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(component=component)

        # Return a logger instance
        return get_logger(f"dataflow.{component}")


# Create a convenience function to get a logger with context
def get_logger(name: str | None = None, **context) -> BoundLogger:
    """Get a structured logger with context.

    Args:
        name: Optional logger name
        **context: Additional context keys to bind

    Returns:
        A structured logger
    """
    logger = structlog.get_logger(name=name)
    if context:
        return logger.bind(**context)
    return logger


# Make the configured logger easily accessible
log = get_logger()

# --- Example Usage --- #
# from dataflow.shared.logging import setup_logging, get_logger
# setup_logging(log_file="logs/cli.log", component="cli")
# log = get_logger("dataflow.cli.commands")
# log.info("Command executed", command="workflow list")
