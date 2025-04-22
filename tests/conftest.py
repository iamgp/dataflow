"""Global test fixtures and utilities for dataflow tests."""

import os
import subprocess
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
    if os.environ.get("CI") == "true" or os.environ.get("INTEGRATION_TESTS") == "true":
        print("Running in CI or INTEGRATION_TESTS=true, enabling integration tests")
        return True

    # Skip integration tests by default when running locally
    print("Not running in CI and INTEGRATION_TESTS not set to true, skipping integration tests")
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
        # Check if services are already running
        try:
            response = requests.get("http://localhost:8000/health/", timeout=2)
            if response.status_code == 200:
                # Services are already running
                yield
                return
        except requests.exceptions.RequestException:
            # Services are not running, start them
            pass

        # Start services
        result = subprocess.run(
            "docker-compose up -d", shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to start Docker Compose services: {result.stderr}")

        try:
            # Wait for services to be ready
            wait_for_services()
        except Exception as e:
            # Stop services if they failed to start properly
            subprocess.run(
                "docker-compose down", shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            pytest.skip(f"Services failed to start: {str(e)}")

    # Provide the fixture
    yield

    # Clean up if needed
    if os.environ.get("STOP_DOCKER_SERVICES", "false").lower() == "true":
        subprocess.run(
            "docker-compose down", shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT
        )


@retry(tries=10, delay=3)
def wait_for_api():
    """Wait for the API service to be ready."""
    try:
        response = requests.get("http://localhost:8000/health/", timeout=5)
        assert response.status_code == 200
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"API not ready yet: {str(e)}")
        raise


@retry(tries=10, delay=3)
def wait_for_minio():
    """Wait for the MinIO service to be ready."""
    try:
        client = Minio(
            "localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
        )
        # This will raise an exception if MinIO is not ready
        client.list_buckets()
        return True
    except Exception as e:
        print(f"MinIO not ready yet: {str(e)}")
        raise


def wait_for_services():
    """Wait for all required services to be ready."""
    try:
        wait_for_api()
        wait_for_minio()
        # Add more service checks as needed
    except Exception as e:
        raise Exception(f"Services failed to start: {str(e)}") from e


@pytest.fixture
def minio_client(docker_services) -> Generator[Minio, None, None]:
    """Create a MinIO client for testing."""
    client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)
    yield client
