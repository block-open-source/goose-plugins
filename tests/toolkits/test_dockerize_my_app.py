import os
import pytest
from unittest.mock import MagicMock
from goose_plugins.toolkits.dockerize_my_app import DockerizationToolkit


@pytest.fixture
def toolkit():
    return DockerizationToolkit(notifier=MagicMock())


def test_dockerize_nodejs(toolkit, tmp_path):
    project_dir = tmp_path / "node_project"
    project_dir.mkdir()
    print(project_dir)
    (project_dir / "package.json").write_text("{}")

    result = toolkit.dockerize(str(project_dir))
    assert result["status"] == "success"
    assert os.path.exists(project_dir / "Dockerfile")


def test_dockerize_python(toolkit, tmp_path):
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("flask")

    result = toolkit.dockerize(str(project_dir))
    assert result["status"] == "success"
    assert os.path.exists(project_dir / "Dockerfile")
