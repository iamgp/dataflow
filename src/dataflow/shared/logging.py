import logging
import os
import sys
from typing import Any

import structlog
import structlog.types

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
        "error": "ERROR",
        "critical": "CRITICAL",
    }
    event_dict["severity"] = severity_map.get(method_name.lower(), "INFO")
    return event_dict


shared_processors: list[structlog.types.Processor] = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    add_log_level_as_severity,
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.dict_tracebacks,
    # Note: We add the final renderer here
]


# --- Logging Configuration --- #
def setup_logging(level: str = "INFO", json_logs: bool = True):
    """Configures structlog for structured logging (JSON or Console).

    Redirects standard library logging to structlog.
    Loguru can optionally intercept stdlib logs if needed elsewhere,
    but is not strictly required for this setup to function.

    Args:
        level: The minimum logging level (e.g., "INFO", "DEBUG").
        json_logs: Whether to output logs in JSON format.
    """
    log_level_str = os.environ.get("LOG_LEVEL", level).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
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
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,  # Needed for stdlib integration
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the stdlib root logger to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=final_processor,
        # foreign_pre_chain=shared_processors, # Optional: Add if needed for context propagation
    )

    handler = logging.StreamHandler(sys.stdout)  # Log to stdout for containers
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplication
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Optional: Configure Loguru to simply intercept stdlib logs
    # This might be useful if other parts of the system rely on loguru features,
    # but it's not needed for structlog's output.
    # from loguru import logger
    # logger.remove()
    # logger.add(sys.stderr, level=log_level, diagnose=False, intercept=True)

    print(f"Structlog logging setup complete. Level: {log_level_str}, JSON: {use_json}")


# Make the configured logger easily accessible
log = structlog.get_logger()

# --- Example Usage --- #
# from dataflow.shared.logging import setup_logging, log
# setup_logging()
# log.info("User logged in", action="login", user_id=123)
