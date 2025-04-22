"""Utilities for tests."""

from collections.abc import Callable
from typing import TypeVar

import pytest

T = TypeVar("T", bound=Callable)


def unit_test(func: T) -> T:
    """Mark a test as a unit test.

    Unit tests don't require external services.
    """
    return pytest.mark.unit(func)


def integration_test(func: T) -> T:
    """Mark a test as an integration test.

    Integration tests require Docker Compose services.
    """
    return pytest.mark.integration(func)


def api_test(func: T) -> T:
    """Mark a test as an API test."""
    return pytest.mark.api(func)


def workflow_test(func: T) -> T:
    """Mark a test as a workflow test."""
    return pytest.mark.workflow(func)


def cli_test(func: T) -> T:
    """Mark a test as a CLI test."""
    return pytest.mark.cli(func)


def slow_test(func: T) -> T:
    """Mark a test as a slow test."""
    return pytest.mark.slow(func)


def mark_as(
    *,
    unit: bool = False,
    integration: bool = False,
    api: bool = False,
    workflow: bool = False,
    cli: bool = False,
    slow: bool = False,
) -> Callable[[T], T]:
    """Mark a test with multiple markers.

    Args:
        unit: If True, mark as a unit test
        integration: If True, mark as an integration test
        api: If True, mark as an API test
        workflow: If True, mark as a workflow test
        cli: If True, mark as a CLI test
        slow: If True, mark as a slow test

    Returns:
        A decorator that applies all the selected markers
    """

    def decorator(func: T) -> T:
        result = func

        if unit:
            result = unit_test(result)
        if integration:
            result = integration_test(result)
        if api:
            result = api_test(result)
        if workflow:
            result = workflow_test(result)
        if cli:
            result = cli_test(result)
        if slow:
            result = slow_test(result)

        return result

    return decorator
