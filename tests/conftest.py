"""Global test fixtures and utilities for dataflow tests."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
import requests
from minio import Minio
from retry import retry

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


def is_docker_compose_available() -> bool:
    """Check if Docker Compose is available and we should run integration tests."""
    # Check if we're in CI or if INTEGRATION_TESTS env var is set
    if os.environ.get("CI") or os.environ.get("INTEGRATION_TESTS"):
        return True

    # Skip integration tests by default when running locally
    return False


@pytest.fixture(scope="session")
def docker_services():
    """Ensure that Docker Compose services are up and responsive.

    This fixture is used for integration tests with actual services.
    """
    if not is_docker_compose_available():
        pytest.skip("Docker Compose not available or integration tests disabled")

    # Start Docker Compose services if needed
    if os.environ.get("START_DOCKER_SERVICES", "true").lower() == "true":
        os.system(f"cd {PROJECT_ROOT} && docker-compose up -d")

        # Wait for services to be ready
        wait_for_services()

    # Provide the fixture
    yield

    # Clean up if needed
    if os.environ.get("STOP_DOCKER_SERVICES", "false").lower() == "true":
        os.system(f"cd {PROJECT_ROOT} && docker-compose down")


@retry(tries=5, delay=2)
def wait_for_api():
    """Wait for the API service to be ready."""
    response = requests.get("http://localhost:8000/health/")
    assert response.status_code == 200
    return True


@retry(tries=5, delay=2)
def wait_for_minio():
    """Wait for the MinIO service to be ready."""
    client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
    # This will raise an exception if MinIO is not ready
    client.list_buckets()
    return True


def wait_for_services():
    """Wait for all required services to be ready."""
    try:
        wait_for_api()
        wait_for_minio()
        # Add more service checks as needed
    except Exception as e:
        pytest.fail(f"Services failed to start: {str(e)}")


@pytest.fixture
def minio_client(docker_services) -> Generator[Minio, None, None]:
    """Create a MinIO client for testing."""
    client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
    yield client
