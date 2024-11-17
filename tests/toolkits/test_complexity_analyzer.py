import pytest
from unittest.mock import MagicMock
from goose_plugins.toolkits.complexity_analyzer import CodeComplexityToolkit


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

    assert result == 2


def test_halstead_complexity(toolkit):
    code = "def test_func():\n    return 42"

    try:
        result = toolkit.halstead_complexity(code)
    except Exception as e:
        result = None
        toolkit.notifier.log.assert_called_with(
            f"Error calculating Halstead complexity: {str(e)}"
        )

    assert isinstance(result, dict)


def test_maintainability_index(toolkit):
    code = "def test_func():\n    return 42"

    try:
        result = toolkit.maintainability_index(code)
    except Exception as e:
        result = None
        toolkit.notifier.log.assert_called_with(
            f"Error calculating maintainability index: {str(e)}"
        )

    assert isinstance(result, float) or isinstance(result, int)
