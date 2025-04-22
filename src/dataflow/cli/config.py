"""CLI commands for workflow configuration management."""

import json

import click
import yaml

from dataflow.shared.config import WorkflowConfigError, config_manager
from dataflow.shared.logging import get_logger

log = get_logger("dataflow.cli.config")


@click.group(name="config", help="Workflow configuration management commands.")
def config_group():
    """Workflow configuration management commands."""
    pass


@config_group.command(name="show", help="Show workflow configuration.")
@click.argument("workflow_name", type=str)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Output format (yaml or json).",
)
@click.option(
    "--raw / --processed",
    default=False,
    help="Show raw config (without environment variable processing).",
)
def show_config(workflow_name: str, output_format: str, raw: bool):
    """Show workflow configuration.

    Args:
        workflow_name: Name of the workflow
        output_format: Output format (yaml or json)
        raw: Show raw config (without environment variable processing)
    """
    try:
        if raw:
            from pathlib import Path

            # Load the raw config directly from the file
            workflow_dir = Path("src") / "dataflow" / "workflows" / workflow_name
            config_path = workflow_dir / "config.yaml"

            if not config_path.exists():
                click.echo(f"Configuration file not found: {config_path}", err=True)
                return

            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            # Load processed config
            config = config_manager.load_config(workflow_name)

        # Format and display the config
        if output_format.lower() == "json":
            click.echo(json.dumps(config, indent=2))
        else:
            click.echo(yaml.dump(config, default_flow_style=False))

    except WorkflowConfigError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        log.error("Unexpected error", error=str(e), exc_info=True)
        click.echo(f"Unexpected error: {e}", err=True)


@config_group.command(name="validate", help="Validate workflow configuration.")
@click.argument("workflow_name", type=str)
def validate_config(workflow_name: str):
    """Validate workflow configuration.

    Args:
        workflow_name: Name of the workflow
    """
    try:
        # Try to load the config which does basic validation
        config_manager.load_config(workflow_name)
        click.echo(f"Configuration for '{workflow_name}' is valid.")

    except WorkflowConfigError as e:
        click.echo(f"Configuration is invalid: {e}", err=True)
    except Exception as e:
        log.error("Unexpected error", error=str(e), exc_info=True)
        click.echo(f"Unexpected error: {e}", err=True)


@config_group.command(name="list", help="List workflows with available configurations.")
def list_configs():
    """List workflows with available configurations."""
    from pathlib import Path

    # Scan the workflows directory
    workflows_dir = Path("src") / "dataflow" / "workflows"

    if not workflows_dir.exists():
        click.echo("Workflows directory not found.", err=True)
        return

    # Find all subdirectories with a config.yaml file
    workflows = []
    for path in workflows_dir.iterdir():
        if path.is_dir() and (path / "config.yaml").exists():
            workflows.append(path.name)

    if not workflows:
        click.echo("No workflow configurations found.")
        return

    click.echo("Available workflow configurations:")
    for workflow in sorted(workflows):
        click.echo(f"  - {workflow}")
