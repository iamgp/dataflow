import importlib
import os
import pkgutil

from dagster import AssetsDefinition, Definitions, JobDefinition, repository

from dataflow.shared.dagster_io import minio_io_manager
from dataflow.shared.logging import get_logger
from dataflow.workflows.nightscout.assets import (
    nightscout_raw_data,
    nightscout_statistics,
    nightscout_transformed_data,
)

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


# Collect assets from all workflows
def collect_assets() -> list[AssetsDefinition]:
    """Collect assets from all workflows."""
    # Currently manually adding assets, but could be dynamic in the future
    return [
        nightscout_raw_data,
        nightscout_transformed_data,
        nightscout_statistics,
    ]


# Define common resources for all jobs and assets
def get_resource_defs():
    """Get resource definitions for the repository."""
    return {
        "minio_io_manager": minio_io_manager,
    }


# Define the Dagster repository
@repository
def dataflow_repo():
    """Main repository for all DATAFLOW workflows."""
    # Discover workflows that were registered and ensure they're JobDefinitions
    discovered_jobs: list[JobDefinition] = discover_workflows()

    # Collect assets from all workflows
    workflow_assets = collect_assets()

    # The @repository decorator expects a list/dict of definitions
    return discovered_jobs + workflow_assets


# Keep the Definitions object for potential non-repo deployment contexts
# or for loading assets/resources/schedules/sensors centrally
definitions = Definitions(
    jobs=discover_workflows(),
    assets=collect_assets(),
    resources=get_resource_defs(),
    # schedules={},
    # sensors={},
)
