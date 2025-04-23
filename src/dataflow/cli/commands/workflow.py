import os

import click

from dataflow.shared.logging import log
from dataflow.workflows.registry import get_workflow_path, workflow_registry


@click.group("workflow")
def workflow_group():
    """Manage data workflows."""
    log.debug("Workflow command group invoked.")
    pass


@workflow_group.command("list")
def list_workflows():
    """List available workflows."""
    log.info("Listing workflows...")
    if not workflow_registry:
        click.echo("No workflows registered.")
        return

    click.echo("Available workflows:")
    for workflow_name in workflow_registry:
        click.echo(f"- {workflow_name}")
    log.debug("Finished listing workflows.")


@workflow_group.command("run")
@click.argument("workflow_name")
@click.option("--dbt-only", is_flag=True, help="Run only DBT models for this workflow")
@click.option(
    "--evidence-only", is_flag=True, help="Build only Evidence dashboards for this workflow"
)
def run_workflow(workflow_name: str, dbt_only: bool, evidence_only: bool):
    """Run a workflow."""
    if workflow_name not in workflow_registry:
        log.error(f"Workflow '{workflow_name}' not found.")
        click.echo(
            f"Workflow '{workflow_name}' not found. Run 'dataflow workflow list' to see available workflows."
        )
        return

    if dbt_only:
        build_dbt_models(workflow_name)
    elif evidence_only:
        build_evidence_dashboards(workflow_name)
    else:
        log.info(f"Running workflow: {workflow_name}")
        # TODO: Implement full workflow run
        click.echo(f"Running workflow: {workflow_name} (placeholder)")


@workflow_group.command("dbt")
@click.argument("workflow_name")
@click.option("--validate", is_flag=True, help="Validate DBT models without running them")
def dbt_command(workflow_name: str, validate: bool):
    """Build or validate DBT models for a workflow."""
    if validate:
        validate_dbt_models(workflow_name)
    else:
        build_dbt_models(workflow_name)


@workflow_group.command("evidence")
@click.argument("workflow_name", required=False)
def evidence_command(workflow_name: str | None = None):
    """Build Evidence dashboards for a workflow or all workflows."""
    build_evidence_dashboards(workflow_name)


def build_dbt_models(workflow_name: str):
    """Build DBT models for a specific workflow."""
    workflow_path = get_workflow_path(workflow_name)
    if not workflow_path:
        log.error(f"Workflow path not found for '{workflow_name}'")
        click.echo(
            f"Workflow '{workflow_name}' not found. Run 'dataflow workflow list' to see available workflows."
        )
        return

    dbt_path = os.path.join(workflow_path, "dbt")
    if not os.path.exists(dbt_path):
        log.error(f"No DBT models found for workflow '{workflow_name}'")
        click.echo(f"No DBT models found for workflow '{workflow_name}'")
        return

    log.info(f"Building DBT models for workflow: {workflow_name}")
    click.echo(f"Building DBT models for workflow: {workflow_name}")

    # TODO: Replace with actual DBT execution
    click.echo(f"DBT models for {workflow_name} built successfully (placeholder)")


def validate_dbt_models(workflow_name: str):
    """Validate DBT models for a specific workflow."""
    workflow_path = get_workflow_path(workflow_name)
    if not workflow_path:
        log.error(f"Workflow path not found for '{workflow_name}'")
        click.echo(
            f"Workflow '{workflow_name}' not found. Run 'dataflow workflow list' to see available workflows."
        )
        return

    dbt_path = os.path.join(workflow_path, "dbt")
    if not os.path.exists(dbt_path):
        log.error(f"No DBT models found for workflow '{workflow_name}'")
        click.echo(f"No DBT models found for workflow '{workflow_name}'")
        return

    log.info(f"Validating DBT models for workflow: {workflow_name}")
    click.echo(f"Validating DBT models for workflow: {workflow_name}")

    # TODO: Replace with actual DBT validation
    click.echo(f"DBT models for {workflow_name} validated successfully (placeholder)")


def build_evidence_dashboards(workflow_name: str | None = None):
    """Build Evidence dashboards for a specific workflow or all workflows."""
    if workflow_name:
        workflow_path = get_workflow_path(workflow_name)
        if not workflow_path:
            log.error(f"Workflow path not found for '{workflow_name}'")
            click.echo(
                f"Workflow '{workflow_name}' not found. Run 'dataflow workflow list' to see available workflows."
            )
            return

        evidence_path = os.path.join(workflow_path, "evidence")
        if not os.path.exists(evidence_path):
            log.error(f"No Evidence dashboards found for workflow '{workflow_name}'")
            click.echo(f"No Evidence dashboards found for workflow '{workflow_name}'")
            return

        log.info(f"Building Evidence dashboards for workflow: {workflow_name}")
        click.echo(f"Building Evidence dashboards for workflow: {workflow_name}")
    else:
        log.info("Building all Evidence dashboards")
        click.echo("Building all Evidence dashboards")

    # TODO: Replace with actual Evidence build
    evidence_cmd = "cd integrations/evidence && npm run build"

    # Just display the command for now rather than executing
    click.echo(f"Would execute: {evidence_cmd}")
    click.echo("Evidence dashboards built successfully (placeholder)")
