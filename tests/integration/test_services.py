"""Integration tests for the dataflow services."""

import os

import pytest
import requests

from tests.utils import integration_test, mark_as

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@integration_test
@pytest.mark.skipif(
    not os.environ.get("CI") and not os.environ.get("INTEGRATION_TESTS"),
    reason="Integration tests only run in CI or when explicitly enabled",
)
def test_api_health(docker_services):
    """Test that the API health endpoint is accessible."""
    max_retries = 5
    retry_delay = 2  # seconds

    response = None
    for attempt in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health/", timeout=5)
            break
        except (requests.ConnectionError, requests.Timeout):
            if attempt < max_retries - 1:
                import time

                time.sleep(retry_delay)
            else:
                pytest.fail(f"Failed to connect to API after {max_retries} attempts")

    assert response is not None, "No response received from API"
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@mark_as(integration=True)
@pytest.mark.skipif(
    not os.environ.get("CI") and not os.environ.get("INTEGRATION_TESTS"),
    reason="Integration tests only run in CI or when explicitly enabled",
)
def test_minio_connection(minio_client):
    """Test that we can connect to MinIO."""
    buckets = minio_client.list_buckets()
    # Just verify we can list buckets (even if there are none)
    assert isinstance(buckets, list)


@mark_as(integration=True, slow=True)
@pytest.mark.skipif(
    not os.environ.get("CI") and not os.environ.get("INTEGRATION_TESTS"),
    reason="Integration tests only run in CI or when explicitly enabled",
)
def test_minio_bucket_operations(minio_client):
    """Test basic MinIO bucket operations."""
    test_bucket = "test-integration-bucket"

    # Create a test bucket if it doesn't exist
    if not minio_client.bucket_exists(test_bucket):
        minio_client.make_bucket(test_bucket)

    # Verify the bucket exists
    assert minio_client.bucket_exists(test_bucket)

    # Clean up after the test
    minio_client.remove_bucket(test_bucket)
