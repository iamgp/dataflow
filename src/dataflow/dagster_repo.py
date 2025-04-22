import importlib
import os
import pkgutil

from dagster import Definitions, JobDefinition, repository

from dataflow.shared.logging import get_logger

# Import the registry - ensuring workflows are registered when this module is loaded
# We need to dynamically discover and import modules within the 'workflows' package
# to trigger the @register_workflow decorators.
from dataflow.workflows.registry import discover_workflows

log = get_logger("dataflow.dagster_repo")

# --- Dynamic Workflow Module Loading ---
# Define the package path and prefix explicitly
# workspace.yaml specifies 'src' as the working directory
workflows_package_path = "dataflow/workflows"
workflows_package_prefix = "dataflow.workflows."

log.info(
    f"Attempting to discover workflow modules in: {workflows_package_path}",
    component="dagster_repo",
)

# Check if the directory exists to prevent pkgutil errors
if os.path.isdir(workflows_package_path):
    # Dynamically import all modules in the 'workflows' package
    # This ensures that any @register_workflow decorators are executed.
    for _, module_name, _ in pkgutil.walk_packages(
        [workflows_package_path], workflows_package_prefix
    ):
        try:
            log.debug(
                f"Importing workflow module: {module_name}",
                component="dagster_repo",
            )
            importlib.import_module(module_name)
        except Exception as e:
            log.error(
                f"Failed to import module {module_name}: {e}",
                component="dagster_repo",
                exc_info=True,
            )
else:
    log.warning(
        f"Workflows directory not found at '{workflows_package_path}'. No workflow modules loaded.",
        component="dagster_repo",
    )
# --- End Dynamic Loading ---


# Define the Dagster repository
@repository
def dataflow_repo():
    """Main repository for all DATAFLOW workflows."""
    # Discover workflows that were registered and ensure they're JobDefinitions
    discovered_jobs: list[JobDefinition] = discover_workflows()

    # The @repository decorator expects a list/dict of definitions
    # TODO: Add resources, schedules, sensors as needed
    return discovered_jobs  # Return the list of discovered jobs directly


# Keep the Definitions object for potential non-repo deployment contexts
# or for loading assets/resources/schedules/sensors centrally
definitions = Definitions(
    jobs=discover_workflows(),  # This should now properly type check
    # resources={},
    # schedules={},
    # sensors={},
)
