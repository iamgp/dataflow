import os
from typing import Any

from fastapi import APIRouter, HTTPException

# Import workflow registry
from dataflow.workflows.registry import discover_workflows, get_workflow_path, workflow_registry

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@router.get("/")
def list_workflows():
    """List all available workflows."""
    discovered = discover_workflows()
    names = [getattr(wf, "name", "unknown") for wf in discovered]
    return {"workflows": names}


@router.get("/{workflow_name}")
def get_workflow_details(workflow_name: str):
    """Get details about a specific workflow."""
    if workflow_name not in workflow_registry:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    workflow_path = get_workflow_path(workflow_name)

    # Check if the workflow has DBT models
    has_dbt = False
    dbt_models = []
    if workflow_path:
        dbt_dir = os.path.join(workflow_path, "dbt")
        if os.path.exists(dbt_dir) and os.path.isdir(dbt_dir):
            has_dbt = True
            # List SQL files in the dbt directory
            dbt_models = [f for f in os.listdir(dbt_dir) if f.endswith(".sql")]

    # Check if the workflow has Evidence dashboards
    has_evidence = False
    evidence_dashboards = []
    if workflow_path:
        evidence_dir = os.path.join(workflow_path, "evidence")
        if os.path.exists(evidence_dir) and os.path.isdir(evidence_dir):
            has_evidence = True
            # List markdown files in the evidence directory
            evidence_dashboards = [f for f in os.listdir(evidence_dir) if f.endswith(".md")]

    return {
        "name": workflow_name,
        "path": workflow_path,
        "dbt": {"enabled": has_dbt, "models": dbt_models},
        "evidence": {"enabled": has_evidence, "dashboards": evidence_dashboards},
    }


@router.post("/{workflow_name}/run")
def run_workflow(workflow_name: str, options: dict[str, Any] | None = None):
    """Run a workflow."""
    if workflow_name not in workflow_registry:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    # TODO: Implement actual workflow execution
    return {"status": "scheduled", "workflow": workflow_name}


@router.post("/{workflow_name}/dbt/build")
def build_dbt_models(workflow_name: str):
    """Build DBT models for a workflow."""
    if workflow_name not in workflow_registry:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    workflow_path = get_workflow_path(workflow_name)
    if not workflow_path:
        raise HTTPException(
            status_code=404, detail=f"Workflow path not found for '{workflow_name}'"
        )

    dbt_path = os.path.join(workflow_path, "dbt")
    if not os.path.exists(dbt_path):
        raise HTTPException(
            status_code=404, detail=f"No DBT models found for workflow '{workflow_name}'"
        )

    # TODO: Implement actual DBT build
    return {
        "status": "success",
        "message": f"DBT models for workflow '{workflow_name}' built (placeholder)",
    }


@router.post("/{workflow_name}/evidence/build")
def build_evidence_dashboards(workflow_name: str):
    """Build Evidence dashboards for a workflow."""
    if workflow_name not in workflow_registry:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    workflow_path = get_workflow_path(workflow_name)
    if not workflow_path:
        raise HTTPException(
            status_code=404, detail=f"Workflow path not found for '{workflow_name}'"
        )

    evidence_path = os.path.join(workflow_path, "evidence")
    if not os.path.exists(evidence_path):
        raise HTTPException(
            status_code=404, detail=f"No Evidence dashboards found for workflow '{workflow_name}'"
        )

    # TODO: Implement actual Evidence build
    return {
        "status": "success",
        "message": f"Evidence dashboards for workflow '{workflow_name}' built (placeholder)",
    }
