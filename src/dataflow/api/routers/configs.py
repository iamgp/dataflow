"""API endpoints for workflow configuration management."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from dataflow.shared.config import (
    WorkflowConfigError,
    config_manager,
    get_workflow_config_path,
    get_workflows_directory,
)
from dataflow.shared.logging import get_logger

log = get_logger("dataflow.api.configs")

router = APIRouter(
    prefix="/configs",
    tags=["Configurations"],
)


class ConfigResponse(BaseModel):
    """Response model for configuration data."""

    workflow_name: str
    config: dict[str, Any]


class ConfigListResponse(BaseModel):
    """Response model for listing available configurations."""

    workflows: list[str]


@router.get("/", response_model=ConfigListResponse)
def list_configs():
    """List workflows with available configurations.

    Returns:
        Dict with list of workflow names
    """
    # Scan the workflows directory
    workflows_dir = get_workflows_directory()

    if not workflows_dir.exists():
        raise HTTPException(status_code=500, detail="Workflows directory not found")

    # Find all subdirectories with a config.yaml file
    workflows = []
    for path in workflows_dir.iterdir():
        if path.is_dir() and (path / "config.yaml").exists():
            workflows.append(path.name)

    return {"workflows": sorted(workflows)}


@router.get("/{workflow_name}", response_model=ConfigResponse)
def get_config(
    workflow_name: str,
    raw: bool = Query(
        False, description="Return raw config without processing environment variables"
    ),
):
    """Get workflow configuration.

    Args:
        workflow_name: Name of the workflow
        raw: Return raw config without processing environment variables

    Returns:
        Dict with workflow name and configuration

    Raises:
        HTTPException: If the configuration cannot be loaded
    """
    try:
        if raw:
            # Load the raw config directly from the file
            config_path = get_workflow_config_path(workflow_name)

            if not config_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Configuration for workflow '{workflow_name}' not found",
                )

            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            # Load processed config
            config = config_manager.load_config(workflow_name)

        return {"workflow_name": workflow_name, "config": config}

    except WorkflowConfigError as e:
        log.error(f"Failed to load config for {workflow_name}", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e


@router.post("/{workflow_name}/validate")
def validate_config(workflow_name: str):
    """Validate workflow configuration.

    Args:
        workflow_name: Name of the workflow

    Returns:
        Dict with validation status

    Raises:
        HTTPException: If the configuration is invalid
    """
    try:
        # Try to load the config which does basic validation
        config_manager.load_config(workflow_name)

        return {
            "workflow_name": workflow_name,
            "valid": True,
            "message": "Configuration is valid",
        }

    except WorkflowConfigError as e:
        log.error(f"Invalid config for {workflow_name}", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e
