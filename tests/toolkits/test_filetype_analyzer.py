import pytest
from unittest.mock import MagicMock
from goose_plugins.toolkits.filetype_analyzer import FileTypeAnalyzerToolkit


@pytest.fixture
def toolkit():
    return FileTypeAnalyzerToolkit(notifier=MagicMock())


@pytest.fixture
def mock_directory(tmp_path):
    """Fixture to create a temporary directory structure for testing."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").touch()
    (tmp_path / ".git" / "objects").mkdir()
    (tmp_path / ".git" / "objects" / "file1").touch()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "doc1.txt").touch()
    (tmp_path / "file1.py").touch()
    (tmp_path / "file2.js").touch()

    return str(tmp_path)


def test_analyze_with_exclusions(toolkit, mock_directory):
    exclude_paths = [".git"]
    results = toolkit.analyze_file_types(mock_directory, exclude_paths=exclude_paths)

    assert results["total_files"] == 3
    assert results["file_counts"] == {".py": 1, ".js": 1, ".txt": 1}
    assert ".git/config" not in results


def test_analyze_without_exclusions(toolkit, mock_directory):
    results = toolkit.analyze_file_types(mock_directory)

    assert results["total_files"] == 5
    assert results["file_counts"] == {
        ".py": 1,
        ".js": 1,
        ".txt": 1,
        "": 2,
    }


def test_empty_directory(toolkit, tmp_path):
    results = toolkit.analyze_file_types(str(tmp_path))

    assert results["total_files"] == 0
    assert results["file_counts"] == {}


def test_non_recursive_analysis(toolkit, mock_directory):
    results = toolkit.analyze_file_types(mock_directory, include_subdirectories=False)

    assert results["total_files"] == 2
    assert results["file_counts"] == {".py": 1, ".js": 1}


def test_invalid_directory(toolkit):
    result = toolkit.analyze_file_types("/nonexistent/path")
    assert result["status"] == "error"
