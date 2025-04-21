from fastapi import APIRouter

# TODO: Import workflow registry/functions
# from dataflow.workflows.registry import discover_workflows

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@router.get("/")
def list_workflows():
    """List all available workflows."""
    # discovered = discover_workflows()
    # names = [getattr(wf, 'name', 'unknown') for wf in discovered] # Example
    return {"workflows": ["workflow1", "workflow2"]}  # Placeholder


# TODO: Add endpoints for running workflows, checking status, etc.
