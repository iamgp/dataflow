"""Tests for the workflow registry."""

from unittest.mock import MagicMock, patch

from dagster import JobDefinition

from dataflow.workflows.registry import (
    discover_workflows,
    get_workflow_metadata,
    register_workflow,
)

from ..utils import unit_test, workflow_test


@unit_test
@workflow_test
def test_register_workflow():
    """Test workflow registration."""
    # Clear the registry for testing
    from dataflow.workflows.registry import _WORKFLOW_REGISTRY

    _WORKFLOW_REGISTRY.clear()

    # Define a test workflow
    @register_workflow(name="test_workflow", metadata={"description": "Test workflow"})
    def test_workflow():
        return "Test workflow"

    # Check the function is returned unmodified
    assert test_workflow() == "Test workflow"

    # Check the workflow was added to the registry
    assert "test_workflow" in _WORKFLOW_REGISTRY
    assert _WORKFLOW_REGISTRY["test_workflow"]["name"] == "test_workflow"
    assert _WORKFLOW_REGISTRY["test_workflow"]["function"] == test_workflow
    assert _WORKFLOW_REGISTRY["test_workflow"]["metadata"]["description"] == "Test workflow"


@unit_test
@workflow_test
@patch("dataflow.workflows.registry.job")
def test_discover_workflows(mock_job):
    """Test workflow discovery."""
    # Clear the registry for testing
    from dataflow.workflows.registry import _WORKFLOW_REGISTRY

    _WORKFLOW_REGISTRY.clear()

    # Set up mock job
    mock_job_def = MagicMock(spec=JobDefinition)
    mock_job.return_value = mock_job_def

    # Register a workflow
    @register_workflow(name="test_workflow")
    def test_workflow():
        return "Test workflow"

    # Register another workflow
    @register_workflow(name="test_workflow_2")
    def test_workflow_2():
        return "Test workflow 2"

    # Discover workflows
    workflows = discover_workflows()

    # Check the result type
    assert isinstance(workflows, list)
    assert len(workflows) == 2
    # In our mock setup, all workflows should be the mock job definition
    assert workflows[0] is mock_job_def
    assert workflows[1] is mock_job_def
    # Make sure our job decorator was called with the functions
    assert mock_job.call_count == 2


@unit_test
@workflow_test
def test_get_workflow_metadata():
    """Test getting workflow metadata."""
    # Clear the registry for testing
    from dataflow.workflows.registry import _WORKFLOW_REGISTRY

    _WORKFLOW_REGISTRY.clear()

    # Register a workflow with metadata
    @register_workflow(name="test_workflow", metadata={"description": "Test workflow"})
    def test_workflow():
        return "Test workflow"

    # Check metadata retrieval
    metadata = get_workflow_metadata("test_workflow")
    assert metadata is not None
    assert metadata["description"] == "Test workflow"

    # Check non-existent workflow
    assert get_workflow_metadata("non_existent_workflow") is None


@unit_test
@workflow_test
def test_duplicate_registration():
    """Test registering duplicate workflows."""
    # Clear the registry for testing
    from dataflow.workflows.registry import _WORKFLOW_REGISTRY

    _WORKFLOW_REGISTRY.clear()

    # Register a workflow
    @register_workflow(name="duplicate_workflow")
    def test_workflow_1():
        return "Original workflow"

    # Register another workflow with the same name
    @register_workflow(name="duplicate_workflow")
    def test_workflow_2():
        return "Overwritten workflow"

    # Check the registry contains the second function
    assert "duplicate_workflow" in _WORKFLOW_REGISTRY
    assert _WORKFLOW_REGISTRY["duplicate_workflow"]["function"] == test_workflow_2
