import click

# Import command groups
from dataflow.cli.commands import service, workflow


@click.group()
def cli():
    """DATAFLOW Command Line Interface"""
    pass


# Add command groups
cli.add_command(workflow.workflow_group)
cli.add_command(service.service_group)


if __name__ == "__main__":
    cli()
