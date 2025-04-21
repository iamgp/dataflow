import click

# Import command groups
from dataflow.cli.commands import service, workflow
from dataflow.shared.logging import log, setup_logging


# Define the Click application object first
@click.group()
@click.option(
    "--log-level", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
)
@click.option("--log-json", is_flag=True, default=True, help="Output logs in JSON format.")
def cli(log_level, log_json):
    """DATAFLOW Command Line Interface"""
    # Configure logging here, only when a command is about to run
    # Avoid calling setup_logging at module import time
    setup_logging(level=log_level, json_logs=log_json)
    log.debug(f"CLI invoked with log_level={log_level}, log_json={log_json}")
    pass


# Add command groups
cli.add_command(workflow.workflow_group)
cli.add_command(service.service_group)


# Define the main entry point function required by pyproject.toml
def main():
    """Entry point that calls the Click application."""
    # Logging is now configured inside the cli() group function when it runs
    cli()


if __name__ == "__main__":
    # This allows running with python -m dataflow.cli
    main()
