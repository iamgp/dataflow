"""Workflow configuration manager.

This module provides utilities for loading and validating workflow configurations.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from dataflow.shared.logging import get_logger

log = get_logger("dataflow.config")


class WorkflowConfigError(Exception):
    """Exception raised when a workflow configuration is invalid."""

    pass


def load_workflow_config(workflow_name: str) -> dict[str, Any]:
    """Load workflow configuration from YAML file.

    Args:
        workflow_name: Name of the workflow

    Returns:
        Dict containing workflow configuration

    Raises:
        WorkflowConfigError: If the configuration file is not found or is invalid
    """
    # Determine the path to the workflow config
    workflow_dir = Path("src") / "dataflow" / "workflows" / workflow_name
    config_path = workflow_dir / "config.yaml"

    if not config_path.exists():
        raise WorkflowConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Process environment variables in the config
        config = _process_env_vars(config)

        log.info(f"Loaded configuration for workflow: {workflow_name}")
        return config
    except yaml.YAMLError as e:
        raise WorkflowConfigError(f"Error parsing YAML configuration: {e}") from e
    except Exception as e:
        raise WorkflowConfigError(f"Error loading workflow configuration: {e}") from e


def validate_workflow_config(config: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
    """Validate workflow configuration against a Pydantic model.

    Args:
        config: Workflow configuration dictionary
        model: Pydantic model class for validation

    Returns:
        Validated configuration as a dictionary

    Raises:
        WorkflowConfigError: If the configuration is invalid
    """
    try:
        # Validate using the provided model
        validated = model.model_validate(config)
        return validated.model_dump()
    except ValidationError as e:
        raise WorkflowConfigError(f"Invalid workflow configuration: {e}") from e


def _process_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Process environment variables in configuration.

    Replaces ${ENV_VAR} patterns with values from environment variables.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment variables resolved
    """
    if isinstance(config, dict):
        return {k: _process_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_process_env_vars(v) for v in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        # Extract environment variable name
        env_var = config[2:-1]
        # Get value from environment, or return empty string if not set
        return os.environ.get(env_var, "")
    else:
        return config


class ConfigManager:
    """Manager class for workflow configurations.

    This class provides methods for loading, validating, and accessing workflow
    configurations.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self._configs: dict[str, dict[str, Any]] = {}

    def load_config(self, workflow_name: str) -> dict[str, Any]:
        """Load and cache workflow configuration.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dict containing workflow configuration

        Raises:
            WorkflowConfigError: If the configuration is invalid
        """
        if workflow_name in self._configs:
            return self._configs[workflow_name]

        config = load_workflow_config(workflow_name)
        self._configs[workflow_name] = config
        return config

    def get_config(self, workflow_name: str) -> dict[str, Any] | None:
        """Get cached workflow configuration.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dict containing workflow configuration, or None if not loaded
        """
        return self._configs.get(workflow_name)

    def validate_config(self, workflow_name: str, model: type[BaseModel]) -> dict[str, Any]:
        """Load and validate workflow configuration.

        Args:
            workflow_name: Name of the workflow
            model: Pydantic model class for validation

        Returns:
            Validated configuration as a dictionary

        Raises:
            WorkflowConfigError: If the configuration is invalid
        """
        config = self.load_config(workflow_name)
        validated = validate_workflow_config(config, model)
        self._configs[workflow_name] = validated  # Update with validated config
        return validated

    def clear_cache(self, workflow_name: str | None = None) -> None:
        """Clear configuration cache.

        Args:
            workflow_name: Name of the workflow to clear, or None to clear all
        """
        if workflow_name:
            self._configs.pop(workflow_name, None)
        else:
            self._configs.clear()


# Global instance of the configuration manager
config_manager = ConfigManager()
