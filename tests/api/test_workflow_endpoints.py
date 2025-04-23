"""Tests for API workflow endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dataflow.api.main import app


@pytest.fixture
def api_client():
    """Create a FastAPI test client."""
    return TestClient(app)


def test_list_workflows(api_client):
    """Test GET /workflows/ endpoint."""
    with patch("dataflow.workflows.registry.discover_workflows") as mock_discover:
        mock_discover.return_value = [type("Workflow", (), {"name": "nightscout_job"})()]

        response = api_client.get("/workflows/")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "nightscout_job" in data["workflows"]


def test_get_workflow_details(api_client):
    """Test GET /workflows/{workflow_name} endpoint."""
    with (
        patch("dataflow.workflows.registry.workflow_registry", {"nightscout": {}}),
        patch("dataflow.workflows.registry.get_workflow_path") as mock_path,
        patch("os.path.exists") as mock_exists,
        patch("os.path.isdir") as mock_isdir,
        patch("os.listdir") as mock_listdir,
    ):
        mock_path.return_value = "/tmp/workflows/nightscout"
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["model.sql"]

        response = api_client.get("/workflows/nightscout")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "nightscout"
        assert data["dbt"]["enabled"] is True
        assert "model.sql" in data["dbt"]["models"]


def test_run_workflow(api_client):
    """Test POST /workflows/{workflow_name}/run endpoint."""
    with patch("dataflow.workflows.registry.workflow_registry", {"nightscout": {}}):
        response = api_client.post("/workflows/nightscout/run", json={"start_date": "2024-01-01"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["workflow"] == "nightscout"


def test_build_dbt_models(api_client):
    """Test POST /workflows/{workflow_name}/dbt/build endpoint."""
    with (
        patch("dataflow.workflows.registry.workflow_registry", {"nightscout": {}}),
        patch("dataflow.workflows.registry.get_workflow_path") as mock_path,
        patch("os.path.exists") as mock_exists,
    ):
        mock_path.return_value = "/tmp/workflows/nightscout"
        mock_exists.return_value = True

        response = api_client.post("/workflows/nightscout/dbt/build")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "DBT models" in data["message"]


def test_build_evidence_dashboards(api_client):
    """Test POST /workflows/{workflow_name}/evidence/build endpoint."""
    with (
        patch("dataflow.workflows.registry.workflow_registry", {"nightscout": {}}),
        patch("dataflow.workflows.registry.get_workflow_path") as mock_path,
        patch("os.path.exists") as mock_exists,
    ):
        mock_path.return_value = "/tmp/workflows/nightscout"
        mock_exists.return_value = True

        response = api_client.post("/workflows/nightscout/evidence/build")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Evidence dashboards" in data["message"]


def test_workflow_not_found(api_client):
    """Test 404 response for non-existent workflow."""
    with patch("dataflow.workflows.registry.workflow_registry", {}):
        response = api_client.get("/workflows/invalid-workflow")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
