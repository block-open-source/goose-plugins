"""Integration tests for the Data toolkit."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path
from goose_plugins.toolkits.data import Data


@pytest.fixture
def data_toolkit():
    """Create a Data toolkit instance for testing."""
    notifier = MagicMock()
    return Data(notifier=notifier)


@pytest.fixture
def sample_csv_path():
    """Get the path to the sample CSV file."""
    current_dir = Path(__file__).parent
    return str(current_dir / "test_data" / "sample.csv")


def test_system_instructions(data_toolkit):
    """Test that system instructions are returned."""
    instructions = data_toolkit.system()
    assert isinstance(instructions, str)
    assert "DuckDB" in instructions


def test_load_csv(data_toolkit, sample_csv_path):
    """Test loading a CSV file."""
    result = data_toolkit.load(sample_csv_path, "test_table")
    assert "Successfully loaded" in result
    assert "Schema" in result
    assert "name: VARCHAR" in result
    assert "age: BIGINT" in result  # DuckDB infers this as BIGINT
    assert "city: VARCHAR" in result


def test_query_loaded_data(data_toolkit, sample_csv_path):
    """Test querying loaded data."""
    # First load the data
    data_toolkit.load(sample_csv_path, "test_table")

    # Test a simple query
    result = data_toolkit.query("SELECT * FROM test_table ORDER BY age")
    assert "John" in result
    assert "25" in result
    assert "New York" in result

    # Test an aggregation query
    result = data_toolkit.query("SELECT AVG(age) as avg_age FROM test_table")
    assert "30" in result


def test_visualize(data_toolkit, sample_csv_path):
    """Test creating a visualization."""
    # First load the data
    data_toolkit.load(sample_csv_path, "test_table")

    # Test creating a simple bar plot of ages
    result = data_toolkit.visualize("SELECT name, age FROM test_table ORDER BY age", "barplot", "-t 'Age Distribution'")
    # The exact output will depend on terminal size, but should contain some output
    assert len(result) > 0


def test_error_handling(data_toolkit):
    """Test error handling for invalid operations."""
    # Test loading non-existent file
    result = data_toolkit.load("nonexistent.csv", "test_table")
    assert "Error" in result

    # Test invalid SQL query
    result = data_toolkit.query("SELECT * FROM nonexistent_table")
    assert "Error" in result
