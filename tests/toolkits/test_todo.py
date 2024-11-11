import pytest
from goose_plugins.toolkits.todo import TodoToolkit
from unittest.mock import MagicMock

@pytest.fixture
def toolkit():
    toolkit = TodoToolkit(notifier=MagicMock())
    return toolkit


def test_add_task(toolkit):
    task_description = "Write unit tests"
    toolkit.add_task(task_description)
    assert toolkit.tasks[0]["description"] == task_description
    toolkit.notifier.log.assert_called_with(f"Added task: '{task_description}'")


def test_list_tasks(toolkit):
    toolkit.add_task("Write unit tests")
    toolkit.add_task("Review PRs")
    result = toolkit.list_tasks()
    toolkit.notifier.log.assert_called()
    expected_output = "Tasks listed successfully: ['1. [ ] Write unit tests', '2. [ ] Review PRs']"
    assert result.strip() == expected_output


def test_update_task(toolkit):
    toolkit.add_task("Old Task")
    toolkit.update_task(1, "Updated Task")
    assert toolkit.tasks[0]["description"] == "Updated Task"
    toolkit.notifier.log.assert_called_with("Updated task 1 from 'Old Task' to 'Updated Task'")


def test_remove_task(toolkit):
    toolkit.add_task("Temporary Task")
    toolkit.remove_task(1)
    assert len(toolkit.tasks) == 0
    toolkit.notifier.log.assert_called_with("Removed task: 'Temporary Task'")


def test_mark_as_complete(toolkit):
    toolkit.add_task("Complete this task")
    toolkit.mark_as_complete(1)
    assert toolkit.tasks[0]["completed"] is True
    toolkit.notifier.log.assert_called_with("Marked task 1 as complete: 'Complete this task'")
