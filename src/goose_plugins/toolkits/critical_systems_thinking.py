from exchange import Exchange, Message, Text
from exchange.content import Content
from exchange.providers import AnthropicProvider
from goose.toolkit.base import Toolkit
from goose.utils.ask import ask_an_ai
import queue
import time
import threading
import os
import signal
import atexit
import sys
from pathlib import Path
import json

from .utils.task_utils import parse_duration, format_task_status, write_intermediate_result, trigger_apple_dialog
from .utils.analysis_utils import create_analysis_prompt
from .tools.search_tools import SearchTools
from .tools.analysis_tools import AnalysisTools
from .tools.task_management_tools import TaskManagementTools

class CriticalSystemsThinking(Toolkit, SearchTools, AnalysisTools, TaskManagementTools):
    """Critical systems thinking toolkit for understanding and solving complex problems."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue = queue.Queue()
        self.autonomous_mode = False
        self.ongoing_tasks = {}
        self.completed_tasks = []
        self.latest_results = {}
        self.pause_flags = {}
        self.loop_threads = {}
        self.final_results = {}  # New attribute to store final results of completed tasks
        self.failed_tasks = []  # New attribute to store failed tasks
        self.results_folder = Path.home() / ".goose" / "results"
        os.makedirs(self.results_folder, exist_ok=True)
        self.log_file = Path.home() / ".goose" / "session_log.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.tool_log_file = Path.home() / ".goose" / "tool_calls.log"
        self.tool_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup)

    def log_tool_call(self, tool_name: str, parameters: dict):
        """Log a tool call to the tool_calls.log file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_entry = f"{timestamp} - Tool: {tool_name}, Parameters: {json.dumps(parameters)}\n"
        with open(self.tool_log_file, "a") as log:
            log.write(log_entry)

    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        self.notify("Received termination signal. Cleaning up...")
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """Clean up all running tasks and terminate threads."""
        self.notify("Cleaning up and aborting all tasks...")
        for task_id in list(self.ongoing_tasks.keys()):
            self._abort_task(task_id)
        
        # Terminate all threads
        for thread in self.loop_threads.values():
            if thread.is_alive():
                thread.join(timeout=1)  # Give threads 1 second to finish
        
        # Force terminate any remaining threads
        for thread in threading.enumerate():
            if thread != threading.main_thread():
                try:
                    thread._stop()
                except:
                    pass
        
        self.notify("All tasks aborted and threads terminated.")

    def _create_exchange(self, include_history=False, system=None) -> Exchange:
        """Create a new Exchange instance with optional message history."""
        provider = AnthropicProvider.from_env()
        messages = []
        if include_history:
            messages = [
                Message(role=msg.role, content=[self.message_content(content) for content in msg.content])
                for msg in self.exchange_view.processor.messages
            ]
        return Exchange(
            provider=provider,
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            system=system
        )

    def _ask_ai(self, prompt: str, include_history=False, system=None) -> str:
        """Helper method to handle AI requests."""
        exchange = self._create_exchange(include_history, system)
        response = ask_an_ai(input=prompt, exchange=exchange, no_history=not include_history)
        return response.content[0].text

    def message_content(self, content: Content) -> Text:
        return Text(str(content)) if not isinstance(content, Text) else content

    def notify(self, message: str):
        """Standardized notification method for concise status updates."""
        self.notifier.status(f"[CST] {message[:50]}...")

    def add_task(self, task_id: str, task_description: str, duration: int):
        """Add a task to the ongoing tasks dictionary."""
        self.log_tool_call("add_task", {
            "task_id": task_id,
            "task_description": task_description[:50] + "...",
            "duration": duration
        })
        self.ongoing_tasks[task_id] = {
            "description": task_description,
            "start_time": time.time(),
            "duration": duration
        }

    def complete_task(self, task_id: str, result: str, success: bool = True):
        """Move a task from ongoing to completed or failed and record result."""
        if task_id in self.ongoing_tasks:
            task = self.ongoing_tasks.pop(task_id)
            task.update({"result": result, "end_time": time.time()})
            if success:
                self.completed_tasks.append(task)
                self.final_results[task_id] = result  # Store the final result
            else:
                self.failed_tasks.append(task)
            if task_id in self.latest_results:
                del self.latest_results[task_id]  # Remove from latest_results as it's now completed or failed

    def _abort_task(self, task_id: str):
        """Abort a running task."""
        if task_id in self.ongoing_tasks:
            self.pause_flags[task_id] = True
            if task_id in self.loop_threads:
                self.loop_threads[task_id].join(timeout=1)  # Wait for the thread to finish
            self.complete_task(task_id, "Task aborted", success=False)

    def _call_llm(self, prompt: str) -> str:
        """
        Call the language model to refine the answer.
        
        Args:
            prompt (str): The prompt to send to the language model.
        
        Returns:
            response (str): The refined answer from the language model.
        """
        self.log_tool_call("_call_llm", {"prompt": prompt[:50] + "..."})  # Log first 50 chars of prompt
        return self._ask_ai(prompt, include_history=True, system=self.system_prompt())

    def _check_stop_condition(self, task_description: str, current_answer: str, 
                            iterations: int, elapsed_time: int, total_duration: int) -> dict:
        """
        Check if the autonomous loop should stop based on the current state of the task.

        Args:
            task_description (str): The description of the task being performed.
            current_answer (str): The current refined answer.
            iterations (int): The number of iterations completed.
            elapsed_time (int): The time elapsed since the task started (in seconds).
            total_duration (int): The total allowed duration for the task (in seconds).

        Returns:
            dict: A dictionary containing the stop decision and reasoning.
        """
        self.log_tool_call("_check_stop_condition", {
            "task_description": task_description[:50] + "...",
            "current_answer": current_answer[:50] + "...",
            "iterations": iterations,
            "elapsed_time": elapsed_time,
            "total_duration": total_duration
        })

        prompt = f"""
        Task: {task_description}
        Current answer: {current_answer}
        Iterations completed: {iterations}
        Elapsed time: {elapsed_time} seconds
        Total allowed duration: {total_duration} seconds

        Based on the current state of the task, determine if the autonomous loop should stop.
        Consider the quality and completeness of the current answer, the number of iterations,
        and the time constraints.

        Provide your response in the following JSON format:
        {{
            "should_stop": boolean,
            "reasoning": "A brief explanation of why the task should or should not stop."
        }}
        """

        exchange = self._create_exchange(include_history=True, system=self.system_prompt())
        response = ask_an_ai(input=prompt, exchange=exchange)
        
        try:
            result = json.loads(response.content[0].text)
            if not isinstance(result, dict) or "should_stop" not in result or "reasoning" not in result:
                raise ValueError("Invalid JSON structure")
            return result
        except json.JSONDecodeError:
            self.notify("Error: Invalid JSON response from LLM for stop condition check.")
            return {"should_stop": False, "reasoning": "Error in LLM response format. Continuing task."}
        except ValueError as e:
            self.notify(f"Error: {str(e)}")
            return {"should_stop": False, "reasoning": "Error in LLM response structure. Continuing task."}

    def system_prompt(self) -> str:
        """Retrieve instructions on how to use this reasoning tool."""
        return Message.load("prompts/critical_systems_thinking.jinja").text