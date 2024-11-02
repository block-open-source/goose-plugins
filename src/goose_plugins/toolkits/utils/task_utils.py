import time
import os

def parse_duration(duration: str) -> int:
    """Convert duration string to seconds."""
    value = int(duration[:-1])
    unit = duration[-1].lower()
    multipliers = {'s': 1, 'm': 60, 'h': 3600}
    if unit not in multipliers:
        raise ValueError("Invalid duration format. Use 's' for seconds, 'm' for minutes, or 'h' for hours.")
    return value * multipliers[unit]

def format_task_status(task_id: str, task: dict, current_time: float) -> str:
    """Format a single task's status."""
    elapsed_time = current_time - task["start_time"]
    remaining_time = max(0, task.get("duration", 0) - elapsed_time)
    status = f"- Task ID: {task_id}\n"
    status += f"  Description: {task['description']}\n"
    if "end_time" in task:
        status += f"  Duration: {task['end_time'] - task['start_time']:.2f} seconds\n"
        status += f"  Result: {task['result']}\n"
    else:
        status += f"  Elapsed Time: {elapsed_time:.2f} seconds\n"
        status += f"  Remaining Time: {remaining_time:.2f} seconds\n"
    return status

def write_intermediate_result(results_folder: str, task_id: str, iteration: int, result: str):
    """Write intermediate results to a file for debugging purposes."""
    filename = f"{task_id}_iteration_{iteration}.txt"
    filepath = os.path.join(results_folder, filename)
    with open(filepath, 'w') as f:
        f.write(f"Task ID: {task_id}\n")
        f.write(f"Iteration: {iteration}\n")
        f.write(f"Result:\n{result}\n")
    return filepath

def trigger_apple_dialog(title: str, message: str):
    """Trigger an Apple dialog box without logging the result."""
    import subprocess
    dialog_command = f'display dialog "{message}" buttons {{"OK"}} default button "OK" with title "{title}"'
    subprocess.run(["osascript", "-e", dialog_command], capture_output=True, text=True)
    # The result is captured but not used, effectively discarding it