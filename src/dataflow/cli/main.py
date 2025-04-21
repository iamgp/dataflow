import click

# Import command groups
from dataflow.cli.commands import service, workflow
from dataflow.shared.logging import log, setup_logging

# Configure logging as soon as the CLI module is loaded
# Set json_logs=False for more readable console output by default
setup_logging(json_logs=False)


@click.group()
@click.option(
    "--log-level", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
)
@click.option("--log-json", is_flag=True, default=False, help="Output logs in JSON format.")
def cli(log_level, log_json):
    """DATAFLOW Command Line Interface"""
    # Reconfigure logging if options are provided
    if click.get_current_context().invoked_subcommand is not None:
        setup_logging(level=log_level, json_logs=log_json)
    log.debug(f"CLI invoked with log_level={log_level}, log_json={log_json}")
    pass


# Add command groups
cli.add_command(workflow.workflow_group)
cli.add_command(service.service_group)


if __name__ == "__main__":
    cli()
