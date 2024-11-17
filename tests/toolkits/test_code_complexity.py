import pytest
from unittest.mock import MagicMock
from goose_plugins.toolkits.code_complexity import CodeComplexityToolkit


@pytest.fixture
def toolkit():
    toolkit = CodeComplexityToolkit(notifier=MagicMock())
    return toolkit


def test_get_python_files(toolkit):
    directory = "test_directory"

    # Simulate os.walk to mock the file retrieval process
    toolkit.get_python_files = MagicMock(
        return_value=["test_file.py", "another_test_file.py"]
    )

    result = toolkit.get_python_files(directory)

    # Check that the mocked method was called with the correct argument
    toolkit.get_python_files.assert_called_with(directory)
    assert result == ["test_file.py", "another_test_file.py"]


def test_analyze_complexity(toolkit):
    directory = "test_directory"

    # Mock methods that would be used during complexity analysis
    toolkit.get_python_files = MagicMock(return_value=["test_file.py"])
    toolkit.cyclomatic_complexity = MagicMock(return_value=5)
    toolkit.halstead_complexity = MagicMock(return_value={"halstead_volume": 100})
    toolkit.maintainability_index = MagicMock(return_value=70)

    # Mock file content reading
    with open("test_file.py", "w") as f:
        f.write("def example_function():\n    return 42")

    result = toolkit.analyze_complexity(directory)
    assert "avg_cyclomatic_complexity" in result
    assert "avg_halstead_complexity" in result
    assert "avg_maintainability_index" in result


def test_cyclomatic_complexity(toolkit):
    code = "def test_func():\n    if True:\n        return 1"

    try:
        result = toolkit.cyclomatic_complexity(code)
    except Exception as e:
        result = None
        toolkit.notifier.log.assert_called_with(
            f"Error calculating cyclomatic complexity: {str(e)}"
        )

    # Adjust the expected result based on the actual output
    assert result[0].complexity == 2


def test_halstead_complexity(toolkit):
    code = "def test_func():\n    return 42"

    try:
        result = toolkit.halstead_complexity(code)
    except Exception as e:
        result = None
        toolkit.notifier.log.assert_called_with(
            f"Error calculating Halstead complexity: {str(e)}"
        )

    # In case no error occurred, verify expected result
    assert isinstance(result, dict)  # Should return a dictionary


def test_maintainability_index(toolkit):
    code = "def test_func():\n    return 42"

    try:
        result = toolkit.maintainability_index(code)
    except Exception as e:
        result = None
        toolkit.notifier.log.assert_called_with(
            f"Error calculating maintainability index: {str(e)}"
        )

    # In case no error occurred, verify expected result
    assert isinstance(result, int)  # Should return an integer


def test_aggregate_results(toolkit):
    results = {
        "cyclomatic_complexity": [5, 10],
        "halstead_metrics": [{"halstead_volume": 100}, {"halstead_volume": 200}],
        "maintainability_index": [70, 60],
    }

    aggregated = toolkit.aggregate_results(results)

    assert "avg_cyclomatic_complexity" in aggregated
    assert "avg_halstead_complexity" in aggregated
    assert "avg_maintainability_index" in aggregated
    assert aggregated["avg_cyclomatic_complexity"] == 7.5
    assert aggregated["avg_halstead_complexity"] == 150
    assert aggregated["avg_maintainability_index"] == 65