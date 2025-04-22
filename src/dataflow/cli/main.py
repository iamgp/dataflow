import os

import click

# Import command groups
from dataflow.cli.commands import docs, service, workflow
from dataflow.shared.logging import get_logger, setup_logging


# Define the Click application object first
@click.group()
@click.option(
    "--log-level", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
)
@click.option("--log-json", is_flag=True, default=True, help="Output logs in JSON format.")
@click.option("--log-file", default="logs/cli.log", help="Path to log file")
def cli(log_level, log_json, log_file):
    """DATAFLOW Command Line Interface"""
    # Ensure logs directory exists
    logs_dir = os.path.dirname(log_file)
    if logs_dir:
        os.makedirs(logs_dir, exist_ok=True)

    # Configure logging here, only when a command is about to run
    setup_logging(level=log_level, json_logs=log_json, log_file=log_file, component="cli")

    # Get a logger with CLI context
    log = get_logger("dataflow.cli")
    log.debug("CLI invoked", log_level=log_level, log_json=log_json, log_file=log_file)


# Add command groups
cli.add_command(workflow.workflow_group)
cli.add_command(service.service_group)
cli.add_command(docs.docs_group)


# Define the main entry point function required by pyproject.toml
def main():
    """Entry point that calls the Click application."""
    try:
        cli()
    except Exception as e:
        # Get logger for this context specifically
        log = get_logger("dataflow.cli.main")
        log.error("Error in CLI", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    # This allows running with python -m dataflow.cli
    main()
