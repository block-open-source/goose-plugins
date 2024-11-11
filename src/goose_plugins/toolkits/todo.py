from goose.toolkit.base import tool, Toolkit

class TodoToolkit(Toolkit):
    """A simple to-do list toolkit for managing tasks."""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        # Initialize tasks as a list of dictionaries with 'description' and 'completed' fields
        self.tasks = []

    @tool
    def add_task(self, task: str) -> str:
        """Add a new task to the to-do list.

        Args:
            task (str): The task description to add to the list.
        """
        # Store task as dictionary with description and completion status
        self.tasks.append({"description": task, "completed": False})
        self.notifier.log(f"Added task: '{task}'")
        return f"Added task: '{task}'"

    @tool
    def list_tasks(self) -> str:
        """List all tasks in the to-do list."""
        if not self.tasks:
            self.notifier.log("No tasks in the to-do list.")
            return "No tasks in the to-do list. Give user instructions on how to add tasks."

        task_list = []
        for index, task in enumerate(self.tasks, start=1):
            status = "✓" if task["completed"] else " "
            task_list.append(f"{index}. [{status}] {task['description']}")
        self.notifier.log("\n".join(task_list))
        return f"Tasks listed successfully: {task_list}"

    @tool
    def remove_task(self, task_number: int) -> str:
        """Remove a task from the to-do list by its number.

        Args:
            task_number (int): The index number of the task to remove (starting from 1).
        """
        try:
            removed_task = self.tasks.pop(task_number - 1)
            self.notifier.log(f"Removed task: '{removed_task['description']}'")
            return f"Removed task: '{removed_task['description']}'"
        except IndexError:
            self.notifier.log("Invalid task number. Please try again.")
            return "User input invalid task number and needs to try again."

    @tool
    def mark_as_complete(self, task_number: int) -> str:
        """Mark a task as complete by its number.

        Args:
            task_number (int): The index number of the task to mark as complete (starting from 1).

        Raises:
            IndexError: If the task number is invalid.
        """
        try:
            self.tasks[task_number - 1]["completed"] = True
            self.notifier.log(
                f"Marked task {task_number} as complete: '{self.tasks[task_number - 1]['description']}'"
            )
            return f"Marked task {task_number} as complete: '{self.tasks[task_number - 1]['description']}'"
        except IndexError:
            self.notifier.log("Invalid task number. Please try again.")
            return "User input invalid task number and needs to try again."

    @tool
    def list_completed_tasks(self) -> str:
        """List all completed tasks."""
        completed_tasks = [task for task in self.tasks if task['completed']]
        if not completed_tasks:
            self.notifier.log("No completed tasks.")
            return "No completed tasks. Provide instructions for marking tasks as complete."

        task_list = []
        for index, task in enumerate(completed_tasks, start=1):
            task_list.append(f"{index}. [✓] {task['description']}")

        self.notifier.log("\n".join(task_list))
        return f"Tasks listed successfully: {task_list}"

    @tool
    def update_task(self, task_number: int, new_description: str) -> str:
        """Update the description of a task by its number.

        Args:
            task_number (int): The index number of the task to update (starting from 1).
            new_description (str): The new description for the task.

        Raises:
            IndexError: If the task number is invalid.
        """
        try:
            old_description = self.tasks[task_number - 1]['description']
            self.tasks[task_number - 1]['description'] = new_description
            self.notifier.log(
                f"Updated task {task_number} from '{old_description}' to '{new_description}'"
            )
            return f"Updated task {task_number} successfully."
        except IndexError:
            self.notifier.log("Invalid task number. Unable to update.")
            return "Invalid task number. Unable to update."

            