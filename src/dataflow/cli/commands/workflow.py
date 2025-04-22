import click

from dataflow.shared.logging import log


@click.group("workflow")
def workflow_group():
    """Manage data workflows."""
    log.debug("Workflow command group invoked.")
    pass


@workflow_group.command("list")
def list_workflows():
    """List available workflows."""
    log.info("Listing workflows...")
    # TODO: Integrate with workflow registry
    click.echo("Available workflows: (placeholder)")
    click.echo("- workflow1")
    click.echo("- workflow2")
    log.debug("Finished listing workflows.")


# TODO: Add commands for run, status, etc.
