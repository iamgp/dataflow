"""Tests for the workflow configuration manager."""

import os
from unittest.mock import mock_open, patch

import pytest
import yaml
from pydantic import BaseModel, Field

from dataflow.shared.config import (
    WorkflowConfigError,
    _process_env_vars,
    config_manager,
    load_workflow_config,
    validate_workflow_config,
)

from ..utils import unit_test


class TestConfigModel(BaseModel):
    """Test configuration model."""

    name: str
    value: int = Field(gt=0)
    nested: dict = {}


@unit_test
@patch(
    "dataflow.shared.config.open",
    new_callable=mock_open,
    read_data="""
source:
  name: test
  value: 42
""",
)
@patch("dataflow.shared.config.Path.exists")
def test_load_workflow_config(mock_exists, mock_file):
    """Test loading workflow configuration."""
    mock_exists.return_value = True

    config = load_workflow_config("test_workflow")

    assert config is not None
    assert config["source"]["name"] == "test"
    assert config["source"]["value"] == 42


@unit_test
@patch("dataflow.shared.config.Path.exists")
def test_load_workflow_config_not_found(mock_exists):
    """Test error when configuration file is not found."""
    mock_exists.return_value = False

    with pytest.raises(WorkflowConfigError) as exc:
        load_workflow_config("test_workflow")

    assert "not found" in str(exc.value)


@unit_test
@patch("dataflow.shared.config.open", new_callable=mock_open, read_data="invalid: yaml: - missing")
@patch("dataflow.shared.config.Path.exists")
def test_load_workflow_config_invalid_yaml(mock_exists, mock_file):
    """Test error when configuration file contains invalid YAML."""
    mock_exists.return_value = True

    # Patch yaml.safe_load to raise YAMLError
    with patch("yaml.safe_load") as mock_yaml:
        mock_yaml.side_effect = yaml.YAMLError("Invalid YAML")

        with pytest.raises(WorkflowConfigError) as exc:
            load_workflow_config("test_workflow")

        assert "Error parsing YAML" in str(exc.value)


@unit_test
def test_validate_workflow_config_valid():
    """Test validating a valid configuration."""
    config = {
        "name": "test",
        "value": 42,
        "nested": {"key": "value"},
    }

    validated = validate_workflow_config(config, TestConfigModel)

    assert validated is not None
    assert validated["name"] == "test"
    assert validated["value"] == 42
    assert validated["nested"]["key"] == "value"


@unit_test
def test_validate_workflow_config_invalid():
    """Test validating an invalid configuration."""
    # Invalid because value must be > 0
    config = {
        "name": "test",
        "value": 0,
    }

    with pytest.raises(WorkflowConfigError) as exc:
        validate_workflow_config(config, TestConfigModel)

    assert "Invalid workflow configuration" in str(exc.value)


@unit_test
def test_process_env_vars():
    """Test environment variable processing."""
    # Set test environment variable
    os.environ["TEST_VAR"] = "test_value"

    config = {
        "name": "${TEST_VAR}",
        "nested": {
            "value": "${TEST_VAR}_suffix",
            "list": ["${TEST_VAR}", "static"],
        },
        "unprocessed": "normal_value",
    }

    processed = _process_env_vars(config)

    assert processed["name"] == "test_value"
    assert processed["nested"]["value"] == "${TEST_VAR}_suffix"  # Only exact matches are processed
    assert processed["nested"]["list"][0] == "test_value"
    assert processed["nested"]["list"][1] == "static"
    assert processed["unprocessed"] == "normal_value"


@unit_test
def test_config_manager():
    """Test the ConfigManager class."""
    # Clear any existing configs
    config_manager.clear_cache()

    # Mock load_workflow_config to return a test config
    with patch("dataflow.shared.config.load_workflow_config") as mock_load:
        mock_load.return_value = {"name": "test", "value": 42}

        # Test loading a config
        config = config_manager.load_config("test_workflow")
        assert config is not None
        assert config["name"] == "test"
        assert config["value"] == 42

        # Test caching (load_workflow_config should be called only once)
        config_manager.load_config("test_workflow")
        assert mock_load.call_count == 1

        # Test get_config
        cached_config = config_manager.get_config("test_workflow")
        assert cached_config is not None
        assert cached_config["name"] == "test"

        # Test get_config for non-existent workflow
        assert config_manager.get_config("non_existent") is None

        # Test clear_cache for specific workflow
        config_manager.clear_cache("test_workflow")
        assert config_manager.get_config("test_workflow") is None

        # Test validation
        mock_load.return_value = {"name": "test", "value": 42}
        with patch("dataflow.shared.config.validate_workflow_config") as mock_validate:
            mock_validate.return_value = {"name": "test", "value": 42, "validated": True}

            validated = config_manager.validate_config("test_workflow", TestConfigModel)
            assert validated is not None
            assert validated["validated"] is True

            # Test that the config is updated with the validated version
            cached = config_manager.get_config("test_workflow")
            assert cached is not None
            assert cached["validated"] is True
