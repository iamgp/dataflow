from collections.abc import Callable
from typing import Any

# Global registry for Dagster jobs/workflows
# Each entry could be a JobDefinition or potentially more complex metadata
WORKFLOW_REGISTRY: list[Any] = []  # TODO: Define a type hint for registered items


def register_workflow(name: str, metadata: dict | None = None) -> Callable:
    """Decorator to register a Dagster job/workflow.

    Args:
        name: The name of the workflow.
        metadata: Optional dictionary for additional workflow metadata.

    Returns:
        The decorator function.
    """

    def decorator(func: Callable) -> Callable:
        print(f"Registering workflow: {name}")  # Basic logging
        # TODO: Add more robust registration logic, potentially storing metadata
        WORKFLOW_REGISTRY.append(func)  # For now, just store the function/job
        return func

    return decorator


def discover_workflows() -> list[Any]:
    """Returns the list of registered workflows."""
    # In the future, this could involve dynamic discovery (e.g., scanning folders)
    # For now, it just returns the populated registry.
    return WORKFLOW_REGISTRY
