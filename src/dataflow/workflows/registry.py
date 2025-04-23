import inspect
import os
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

# Expose the registry for CLI use (read-only)
workflow_registry = _WORKFLOW_REGISTRY


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


def get_workflow_path(name: str) -> str | None:
    """Get the file system path to a workflow's directory.

    Args:
        name: The name of the workflow.

    Returns:
        The path to the workflow directory, or None if not found.
    """
    with _registry_lock:
        if name not in _WORKFLOW_REGISTRY:
            return None

        func = _WORKFLOW_REGISTRY[name]["function"]
        # Get the module file path
        try:
            module = inspect.getmodule(func)
            if not module:
                return None

            module_file = inspect.getfile(module)
            # Get the directory containing the module
            module_dir = os.path.dirname(os.path.abspath(module_file))

            # For workflow modules, this should be the workflow directory
            # If the directory name doesn't match the workflow name, search for it
            dir_name = os.path.basename(module_dir)
            if dir_name == name:
                return module_dir

            # If not, try to find a workflow directory with the matching name
            workflows_dir = os.path.dirname(module_dir)
            potential_path = os.path.join(workflows_dir, name)
            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                return potential_path

            # Still not found, default to the module directory
            return module_dir
        except (TypeError, ValueError, AttributeError):
            log.error(f"Could not determine path for workflow '{name}'")
            return None
