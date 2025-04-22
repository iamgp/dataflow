"""Tests for the health API endpoint."""

import pytest
from fastapi.testclient import TestClient

from dataflow.api import app

from ..utils import api_test, unit_test


@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    return TestClient(app)


@unit_test
@api_test
def test_health_endpoint(client):
    """Test that the health endpoint returns a 200 status code and proper JSON response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["version"], str)


@unit_test
@api_test
def test_root_endpoint(client):
    """Test that the root endpoint returns a 200 status code and welcome message."""
    # Since health_check is on root, this is redundant but we keep it for completeness
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data
