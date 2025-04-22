# Testing Guide for DATAFLOW

This guide explains how to run tests in the DATAFLOW project and how to write your own tests.

## Prerequisites

- Python 3.11+
- Dependencies installed (via `uv sync --all-extras --dev`)
- Docker and Docker Compose (for integration tests)

## Running Tests

### Unit Tests

Unit tests don't require external services to run. They're the fastest type of test and should be run frequently during development.

```bash
# Run all unit tests
pytest tests/ -m "not integration"

# Run tests for a specific component
pytest tests/shared/

# Run a specific test file
pytest tests/shared/test_minio.py
```

### Integration Tests

Integration tests require Docker Compose services to be running. They test the interaction between different components of the system.

```bash
# Start Docker Compose services
docker-compose up -d

# Run integration tests
INTEGRATION_TESTS=true pytest tests/integration/

# Stop Docker Compose services
docker-compose down
```

### Running All Tests

To run all tests (both unit and integration):

```bash
# Make sure Docker Compose services are running
docker-compose up -d

# Run all tests
INTEGRATION_TESTS=true pytest
```

## Test Categories

Tests are organized using pytest markers:

- `unit`: Tests that don't require external services
- `integration`: Tests that require Docker Compose services
- `slow`: Tests that take a long time to run
- `api`: Tests for the API endpoints
- `cli`: Tests for the CLI commands
- `workflow`: Tests for workflow functionality

You can run tests with specific markers:

```bash
# Run only API tests
pytest -m api

# Run workflow tests that are not integration tests
pytest -m "workflow and not integration"
```

## Writing Tests

### Test Structure

Tests are organized in the `tests/` directory with the following structure:

- `tests/api/`: Tests for the API
- `tests/cli/`: Tests for the CLI
- `tests/shared/`: Tests for shared utilities
- `tests/workflows/`: Tests for workflow components
- `tests/integration/`: Integration tests that require Docker Compose

### Adding New Tests

1. Create test files in the appropriate directory
2. Use appropriate markers for the test type
3. Follow the existing test patterns for consistency

Example test:

```python
import pytest

@pytest.mark.unit
def test_my_function():
    """Test description."""
    result = my_function()
    assert result == expected_result

@pytest.mark.integration
def test_integration_feature(docker_services):
    """Test that requires Docker services."""
    # The docker_services fixture ensures services are running
    result = call_service_api()
    assert result.status_code == 200
```

## CI/CD Integration

Tests are automatically run in GitHub Actions:

- Unit tests run on every push and pull request
- Integration tests run on pushes to main/master and can be triggered manually

See the workflows in `.github/workflows/` for details.

## Troubleshooting

### Integration Tests Failing

If integration tests are failing, check:

1. Docker Compose services are running: `docker-compose ps`
2. Service logs for errors: `docker-compose logs`
3. The test fixtures in `tests/conftest.py` for connection issues
