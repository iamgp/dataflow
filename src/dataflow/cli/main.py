import click


@click.group()
def cli():
    """DATAFLOW Command Line Interface"""
    pass


# Add subcommands here later
# Example:
# from .commands import workflow
# cli.add_command(workflow.workflow_group)

if __name__ == "__main__":
    cli()
