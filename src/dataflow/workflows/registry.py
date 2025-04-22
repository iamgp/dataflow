from collections.abc import Callable
from threading import Lock
from typing import Any

from dagster import JobDefinition, job

from dataflow.shared.logging import get_logger

log = get_logger("dataflow.workflows.registry")

# Define a type for registry entries
WorkflowRegistryEntry = dict[str, Any]  # name, function, metadata

# Use a dictionary to prevent duplicates and allow lookup by name
_WORKFLOW_REGISTRY: dict[str, WorkflowRegistryEntry] = {}
_registry_lock = Lock()  # For thread safety


def register_workflow(name: str, metadata: dict | None = None) -> Callable:
    """Decorator to register a Dagster job/workflow.

    Args:
        name: The name of the workflow.
        metadata: Optional dictionary for additional workflow metadata.

    Returns:
        The decorator function.
    """

    def decorator(func: Callable) -> Callable:
        log.info(f"Registering workflow: {name}")
        with _registry_lock:
            if name in _WORKFLOW_REGISTRY:
                log.warning(f"Workflow with name '{name}' already registered. Overwriting.")
            _WORKFLOW_REGISTRY[name] = {"name": name, "function": func, "metadata": metadata or {}}
        return func

    return decorator


def discover_workflows() -> list[JobDefinition]:
    """Returns the list of registered workflows.

    Returns:
        List[JobDefinition]: A list of Dagster job definitions.
    """
    # In the future, this could involve dynamic discovery (e.g., scanning folders)
    # For now, it just returns the populated registry.
    with _registry_lock:
        # Convert functions to JobDefinition objects if they aren't already
        workflows = []
        for entry in _WORKFLOW_REGISTRY.values():
            func = entry["function"]
            # Check if the function is already a JobDefinition or has the _is_job attribute
            if isinstance(func, JobDefinition) or hasattr(func, "_is_job"):
                workflows.append(func)
            else:
                # Wrap the function with a Dagster job decorator
                workflows.append(job(func))

        return workflows


def get_workflow_metadata(name: str) -> dict | None:
    """Returns metadata for a specific workflow."""
    with _registry_lock:
        if name in _WORKFLOW_REGISTRY:
            return _WORKFLOW_REGISTRY[name]["metadata"]
    return None
