"""Tests for workflow plugins."""

import os
import sys
from unittest.mock import patch

# Import the test utilities - need to handle module imports in tests properly
# This is a workaround - in a real project, we would make tests a proper installed package
TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)

from utils import mark_as


class MockPlugin:
    """A mock plugin for testing."""

    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.initialized = False

    def initialize(self):
        """Initialize the plugin."""
        self.initialized = True
        return True

    def execute(self, data):
        """Execute the plugin on some data."""
        return f"Processed {data} with {self.name}"


@mark_as(unit=True, workflow=True)
def test_plugin_initialization():
    """Test plugin initialization."""
    plugin = MockPlugin("test_plugin", {"option1": "value1"})
    assert plugin.name == "test_plugin"
    assert plugin.config == {"option1": "value1"}
    assert not plugin.initialized

    result = plugin.initialize()
    assert result is True
    assert plugin.initialized


@mark_as(unit=True, workflow=True)
def test_plugin_execution():
    """Test plugin execution."""
    plugin = MockPlugin("test_plugin")
    plugin.initialize()

    result = plugin.execute("test_data")
    assert result == "Processed test_data with test_plugin"


@mark_as(unit=True, workflow=True)
@patch("builtins.print")
def test_plugin_with_mock(mock_print):
    """Test plugin with mocking."""
    plugin = MockPlugin("test_plugin")
    plugin.initialize()

    # Use the mock
    print(f"Using plugin: {plugin.name}")
    mock_print.assert_called_once_with("Using plugin: test_plugin")
