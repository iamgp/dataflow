import click


@click.group("workflow")
def workflow_group():
    """Manage data workflows."""
    pass


@workflow_group.command("list")
def list_workflows():
    """List available workflows."""
    # TODO: Integrate with workflow registry
    click.echo("Listing workflows... (placeholder)")
    click.echo("- workflow1")
    click.echo("- workflow2")


# TODO: Add commands for run, status, etc.
