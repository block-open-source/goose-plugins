from exchange import Exchange, Message, Text
from exchange.content import Content
from exchange.providers import AnthropicProvider
from goose.toolkit.base import Toolkit, tool
from goose.utils.ask import ask_an_ai
from goose_plugins.utils.selenium_web_browser import get_web_page_content
from goose_plugins.utils.serper_search import serper_search
import queue
import time
import threading
import os
import json
from pathlib import Path
import signal
import atexit

class CriticalSystemsThinking(Toolkit):
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
        self.results_folder = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'debug_results')
        os.makedirs(self.results_folder, exist_ok=True)
        self.log_file = Path.home() / ".goose" / "session_log.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup)

    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        self.notify("Received termination signal. Cleaning up...")
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """Clean up all running tasks."""
        self.notify("Cleaning up and aborting all tasks...")
        for task_id in list(self.ongoing_tasks.keys()):
            self._abort_task(task_id)
        self.notify("All tasks aborted.")

    async def log_action(self, action: str, details: str):
        """Log an action to the session log file."""
        log_entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details
        }

    def _write_intermediate_result(self, task_id: str, iteration: int, result: str):
        """Write intermediate results to a file for debugging purposes."""
        filename = f"{task_id}_iteration_{iteration}.txt"
        filepath = os.path.join(self.results_folder, filename)
        with open(filepath, 'w') as f:
            f.write(f"Task ID: {task_id}\n")
            f.write(f"Iteration: {iteration}\n")
            f.write(f"Result:\n{result}\n")
        self.notify(f"Intermediate result written to {filepath}")

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
            self.notify(f"Task {task_id} aborted.")
        else:
            self.notify(f"Task {task_id} not found or already completed.")

    def notify_user(self, message: str):
        """Notify the user when help is needed."""
        print(f"[User Notification] {message}")

    def _parse_duration(self, duration: str) -> int:
        """Convert duration string to seconds."""
        value = int(duration[:-1])
        unit = duration[-1].lower()
        multipliers = {'s': 1, 'm': 60, 'h': 3600}
        if unit not in multipliers:
            raise ValueError("Invalid duration format. Use 's' for seconds, 'm' for minutes, or 'h' for hours.")
        return value * multipliers[unit]

    def _trigger_apple_dialog(self, title: str, message: str):
        """Trigger an Apple dialog box."""
        dialog_command = f'display dialog "{message}" buttons {{"OK"}} default button "OK" with title "{title}"'
        os.system(f"osascript -e '{dialog_command}'")

    def _call_llm(self, prompt: str) -> str:
        """
        Call the language model to refine the answer.
        
        Args:
            prompt (str): The prompt to send to the language model.
        
        Returns:
            response (str): The refined answer from the language model.
        """
        return self._ask_ai(prompt, include_history=True, system=self.system_prompt())

    def _check_stop_condition(self, task_description: str, current_answer: str, iterations: int, elapsed_time: int, total_duration: int) -> dict:
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
        # exchange.add(Message(role="user", content=[Text(prompt)]))
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

    @tool
    def autonomous_loop(self, task_description: str, duration: str = "1m") -> str:
        """
        Run a task autonomously in the background, continuously working on a problem and building a final answer.

        Args:
            task_description (str): A description of the task to be performed.
            duration (str): The total duration for the task. Format: "<number><unit>".
                            Units: 's' for seconds, 'm' for minutes, 'h' for hours.
                            Examples: "30s", "5m", "1h". Default: "1m".

        Returns:
            response (str): A message indicating the continuous background task has been started.
        """
        duration_seconds = self._parse_duration(duration)
        interval_seconds = 20  # Enforcing 20-second interval
        task_id = f"task_{int(time.time())}"
        self.pause_flags[task_id] = False
        self.latest_results[task_id] = {"current_answer": "", "iterations": 0, "status": "running"}

        def continuous_background_task():
            start_time = time.time()
            current_answer = ""
            iterations = 0

            try:
                while time.time() - start_time < duration_seconds:
                    if self.pause_flags[task_id]:
                        time.sleep(1)
                        continue

                    iterations += 1
                    elapsed_time = int(time.time() - start_time)
                    
                    prompt = f"""
                    Task: {task_description}
                    Current answer: {current_answer}
                    Iteration: {iterations}
                    Elapsed time: {elapsed_time} seconds
                    Total duration: {duration_seconds} seconds

                    Please refine the current answer using your critical thinking skills and the task description.
                    """

                    try:
                        # Call the LLM to refine the answer
                        refined_answer = self._call_llm(prompt)

                        # Check if we should stop
                        stop_check = self._check_stop_condition(task_description, refined_answer, iterations, elapsed_time, duration_seconds)
                        
                        if stop_check["should_stop"]:
                            self.notify(f"Task {task_id} stopping. Reason: {stop_check['reasoning']}")
                            break

                        current_answer = refined_answer
                        self.latest_results[task_id] = {
                            "current_answer": current_answer, 
                            "iterations": iterations,
                            "status": "running",
                            "elapsed_time": elapsed_time
                        }

                        # Write intermediate result
                        self._write_intermediate_result(task_id, iterations, current_answer)

                    except Exception as e:
                        error_message = f"Error in iteration {iterations}: {str(e)}"
                        self.notify(error_message)
                        self._write_intermediate_result(task_id, iterations, f"ERROR: {error_message}")
                        # Continue to the next iteration instead of breaking the loop
                        continue

                    time.sleep(interval_seconds)

                self.complete_task(task_id, f"Continuous task '{task_description}' completed. Final answer: {current_answer}")
                self.latest_results[task_id]["status"] = "completed"
                self._trigger_apple_dialog("Task Completed", f"Continuous task completed after {iterations} iterations.")

            except Exception as e:
                error_message = f"Critical error in task {task_id}: {str(e)}"
                self.notify(error_message)
                self._write_intermediate_result(task_id, iterations, f"CRITICAL ERROR: {error_message}")
                self.complete_task(task_id, f"Continuous task '{task_description}' failed. Error: {error_message}")
                self.latest_results[task_id]["status"] = "failed"
                self._trigger_apple_dialog("Task Failed", f"Continuous task failed after {iterations} iterations.")

        self.autonomous_mode = True
        self.notify(f"Starting continuous background task: {task_description}")
        self.add_task(task_id, task_description, duration_seconds)
        
        thread = threading.Thread(target=continuous_background_task)
        self.loop_threads[task_id] = thread
        thread.start()
        return f"Continuous background task '{task_description}' (ID: {task_id}) has been started with a duration of {duration}."

    def _perform_analysis(self, task_description: str, current_answer: str) -> str:
        """
        Perform analysis for a single iteration of the continuous background task.
        This method can invoke other tools as needed.
        """
        prompt = f"""
        Task description: {task_description}
        Current progress: {current_answer}

        Analyze the current progress and provide the next step or insight for solving the problem.
        You can use any of the available tools to gather more information or perform specific analyses.
        Return your analysis and any tool results in a concise manner.
        """
        
        analysis = self._ask_ai(prompt, include_history=True)
        
        # Example of invoking other tools within the analysis
        if "need more information" in analysis.lower():
            search_query = f"latest information about {task_description}"
            search_results = self.search(search_query)
            analysis += f"\n\nAdditional information from search:\n{search_results}"
        
        if "stakeholder analysis needed" in analysis.lower():
            stakeholder_analysis = self.stakeholder_analysis(task_description)
            analysis += f"\n\nStakeholder analysis results:\n{stakeholder_analysis}"
        
        return analysis

    def _format_task_status(self, task_id: str, task: dict, current_time: float) -> str:
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

    @tool
    def get_background_job_status(self) -> str:
        """Get the status of all background jobs (ongoing, completed, and failed)."""
        current_time = time.time()
        status = ["Background Job Status:\n"]
        
        if self.ongoing_tasks:
            status.append("\nOngoing Tasks:")
            for task_id, task in self.ongoing_tasks.items():
                status.append(self._format_task_status(task_id, task, current_time))
        
        if self.completed_tasks:
            status.append("\nCompleted Tasks:")
            for task in self.completed_tasks:
                status.append(self._format_task_status(task["description"], task, current_time))
        
        if self.failed_tasks:
            status.append("\nFailed Tasks:")
            for task in self.failed_tasks:
                status.append(self._format_task_status(task["description"], task, current_time))
        
        return "\n".join(status)

    def _create_analysis_prompt(self, analysis_type: str, **kwargs) -> str:
        """Create a prompt for various types of analysis."""
        prompts = {
            "structured": lambda p: f"""
                Perform a structured analysis of the following problem using the MECE principle:
                {p}
                Return the results as a JSON string with the following structure:
                {{
                    "problem": "Brief restatement of the problem",
                    "categories": [
                        {{
                            "name": "Category Name",
                            "elements": ["Element 1", "Element 2", ...],
                            "analysis": "Brief analysis of this category"
                        }},
                        ...
                    ],
                    "conclusion": "Overall conclusion based on the structured analysis"
                }}
            """,
            "request": lambda s: f"""
                Analyze the user statement: {s}
                If you need to immediately clarify something and it's something
                short and simple, respond with your question(s).
                If you need multiple questions, you can ask multiple questions.
                Please bullet point your questions.
                Limit your response to 5 questions.
            """,
            "solutions": lambda s: f"""
                Analyze the user statement: {s}
                Consider the existing message history and provide a well thought out response.
                Provide one or more potential solutions to the problem.
                Limit your response to 5 solutions.
            """,
            "stakeholder": lambda p: f"""
                Analyze the following problem statement and identify key stakeholders:
                {p}
                For each stakeholder, determine their interests and potential impacts.
            """,
            "future_scenarios": lambda p, t: f"""
                Based on the following problem statement and time horizon, generate potential future scenarios:
                Problem: {p}
                Time Horizon: {t}
                
                Consider various factors such as technological advancements, societal changes, 
                environmental impacts, and potential policy shifts.
                
                Return the results as a JSON string with scenarios including name, description,
                key factors, and potential outcomes.
                Generate at least 3 distinct scenarios.
            """,
            "system_mapping": lambda p: f"""
                Based on the following problem statement, create a high-level system map:
                {p}
                
                Identify key components, their relationships, and potential feedback loops.
                Return results as JSON with components and feedback loops.
            """,
            "risk": lambda p, s: f"""
                Perform a risk assessment for the following problem and proposed solution:
                Problem: {p}
                Proposed Solution: {s}
                
                Identify potential risks, their likelihood, impact, and possible mitigation strategies.
                Return results as JSON with detailed risk assessments.
            """,
            "ethical": lambda p, s: f"""
                Perform an ethical analysis for the following problem and proposed solution:
                Problem: {p}
                Proposed Solution: {s}
                
                Consider various ethical frameworks and principles, potential ethical dilemmas,
                and the impact on different stakeholders.
                Return results as JSON with ethical considerations and overall assessment.
            """
        }
        return prompts[analysis_type](**kwargs)

    @tool
    def structured_analysis(self, problem: str) -> str:
        """
        Perform a structured analysis of the given problem using the MECE principle.

        Args:
            problem (str): A description of the problem to analyze.

        Returns:
            response (str): A JSON string containing the structured analysis.
        """
        self.notify("Performing structured analysis")
        return self._ask_ai(self._create_analysis_prompt("structured", p=problem))

    @tool
    def search(self, query: str) -> str:
        """
        Search the web for information using the Serper API.

        Args:
            query (str): query to search for.

        Returns:
            response (str): A JSON response containing search results.
        """
        self.notifier.status("searching...")
        return serper_search(query)

    @tool
    def analyze_request(self, statement: str) -> str:
        """
        When a request is unclear, high-level or ambiguous use this tool to
        analyze the response and provide a well thought out response.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """
        self.notifier.status("analyzing request...")
        return self._ask_ai(
            self._create_analysis_prompt("request", s=statement),
            include_history=True,
            system=self.system_prompt()
        )

    @tool
    def review_web_page(self, url: str) -> str:
        """
        Review the content of a web page by providing a summary of the content.

        Args:
            url (str): URL of the web page to review.

        Returns:
            response (str): A summary of the content of the web page.
        """
        self.notifier.status(f"fetching content from {url}")
        try:
            web_content = get_web_page_content(url)
            self.notifier.status(f"reviewing content: {web_content[:50]}...")
            return self._ask_ai(f"summarize the following content: {web_content}")
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def consider_solutions(self, statement: str) -> str:
        """
        Provide a well thought out response to the statement summarize the
        problem and provide a solution or a set of solutions.

        Args:
            statement (str): description of problem or errors seen.

        Returns:
            response (str): A well thought out response to the statement or question.
        """
        self.notifier.status("considering solutions...")
        return self._ask_ai(
            self._create_analysis_prompt("solutions", s=statement),
            include_history=True
        )

    @tool
    def stakeholder_analysis(self, problem_statement: str) -> str:
        """
        Identify and analyze key stakeholders related to the given problem.

        Args:
            problem_statement (str): A description of the problem or situation.

        Returns:
            response (str): A JSON string containing a list of stakeholders, their interests, and potential impacts.
        """
        self.notifier.status("Analyzing stakeholders...")
        return self._ask_ai(
            self._create_analysis_prompt("stakeholder", p=problem_statement),
            include_history=True
        )

    @tool
    def generate_future_scenarios(self, problem_statement: str, time_horizon: str) -> str:
        """
        Generate potential future scenarios based on the given problem statement and time horizon.

        Args:
            problem_statement (str): A description of the current problem or situation.
            time_horizon (str): The future time frame to consider (e.g., "5 years", "10 years", "50 years").

        Returns:
            response (str): A JSON string containing a list of potential future scenarios.
        """
        self.notifier.status("Generating future scenarios...")
        return self._ask_ai(
            self._create_analysis_prompt("future_scenarios", p=problem_statement, t=time_horizon)
        )

    @tool
    def system_mapping(self, problem_statement: str) -> str:
        """
        Create a high-level system map based on the given problem statement.

        Args:
            problem_statement (str): A description of the problem or situation.

        Returns:
            response (str): A JSON string representing a high-level system map.
        """
        self.notifier.status("Creating system map...")
        return self._ask_ai(self._create_analysis_prompt("system_mapping", p=problem_statement))

    @tool
    def risk_assessment(self, problem_statement: str, proposed_solution: str) -> str:
        """
        Perform a risk assessment for the given problem and proposed solution.

        Args:
            problem_statement (str): A description of the problem or situation.
            proposed_solution (str): A description of the proposed solution.

        Returns:
            response (str): A JSON string containing a list of potential risks and their assessments.
        """
        self.notifier.status("Performing risk assessment...")
        return self._ask_ai(
            self._create_analysis_prompt("risk", p=problem_statement, s=proposed_solution)
        )

    @tool
    def ethical_analysis(self, problem_statement: str, proposed_solution: str) -> str:
        """
        Perform an ethical analysis of the given problem and proposed solution.

        Args:
            problem_statement (str): A description of the problem or situation.
            proposed_solution (str): A description of the proposed solution.

        Returns:
            response (str): A JSON string containing an ethical analysis of the problem and solution.
        """
        self.notifier.status("Performing ethical analysis...")
        return self._ask_ai(
            self._create_analysis_prompt("ethical", p=problem_statement, s=proposed_solution)
        )

    def system_prompt(self) -> str:
        """Retrieve instructions on how to use this reasoning tool."""
        return Message.load("prompts/critical_systems_thinking.jinja").text

    @tool
    def pause_autonomous_loop(self, task_id: str) -> str:
        """
        Pause the autonomous loop for a given task.

        Args:
            task_id (str): The ID of the task to pause.

        Returns:
            response (str): A message indicating whether the task was successfully paused.
        """
        if task_id in self.pause_flags:
            self.pause_flags[task_id] = True
            return f"Task {task_id} has been paused."
        else:
            return f"Task {task_id} not found."

    @tool
    def resume_autonomous_loop(self, task_id: str) -> str:
        """
        Resume the autonomous loop for a given task.

        Args:
            task_id (str): The ID of the task to resume.

        Returns:
            response (str): A message indicating whether the task was successfully resumed.
        """
        if task_id in self.pause_flags:
            self.pause_flags[task_id] = False
            return f"Task {task_id} has been resumed."
        else:
            return f"Task {task_id} not found."

    @tool
    def get_latest_results(self, task_id: str) -> str:
        """
        Get the latest results for a given task.

        Args:
            task_id (str): The ID of the task to get results for.

        Returns:
            response (str): A string containing the latest results and iteration count,
                            or the final result if the task is completed.
        """
        if task_id in self.final_results:
            return f"Final result for completed task {task_id}:\n{self.final_results[task_id]}"
        elif task_id in self.latest_results:
            result = self.latest_results[task_id]
            return f"Latest results for ongoing task {task_id}:\nIterations: {result['iterations']}\nCurrent answer: {result['current_answer']}"
        else:
            return f"No results found for task {task_id}."

    @tool
    def list_task_ids(self) -> str:
        """
        List all task IDs, including ongoing and completed tasks.

        Returns:
            response (str): A string containing all task IDs.
        """
        all_tasks = list(self.ongoing_tasks.keys()) + [task["description"] for task in self.completed_tasks]
        return f"Task IDs:\n" + "\n".join(all_tasks)

    @tool
    def get_task_info(self, task_id: str) -> str:
        """
        Get detailed information about a specific task.

        Args:
            task_id (str): The ID of the task to get information for.

        Returns:
            response (str): A string containing detailed information about the task.
        """
        if task_id in self.ongoing_tasks:
            task = self.ongoing_tasks[task_id]
            latest_result = self.latest_results.get(task_id, {})
            return f"""
Task ID: {task_id}
Description: {task['description']}
Status: Ongoing
Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['start_time']))}
Elapsed Time: {int(time.time() - task['start_time'])} seconds
Iterations: {latest_result.get('iterations', 'N/A')}
Current Answer: {latest_result.get('current_answer', 'N/A')}
"""
        elif task_id in [task["description"] for task in self.completed_tasks]:
            task = next(task for task in self.completed_tasks if task["description"] == task_id)
            return f"""
Task ID: {task_id}
Description: {task['description']}
Status: Completed
Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['start_time']))}
End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['end_time']))}
Duration: {int(task['end_time'] - task['start_time'])} seconds
Result: {task['result']}
"""
        else:
            return f"No task found with ID: {task_id}"

    @tool
    def interpret_task_query(self, query: str) -> str:
        """
        Interpret a natural language query about tasks and provide relevant information.

        Args:
            query (str): A natural language query about tasks.

        Returns:
            response (str): The interpreted response to the query.
        """
        prompt = f"""
        Given the following natural language query about tasks, interpret the request and provide the most relevant information:

        Query: {query}

        Consider the following context:
        - There may be ongoing, completed, and failed tasks.
        - Task IDs are usually in the format "task_timestamp".
        - The query might refer to the "last task" or use other relative terms.
        - The user might use shorthand or informal language.
        - The user might be specifically asking about failed tasks.

        Based on this query, determine:
        1. What specific task(s) is the user asking about?
        2. What information does the user want to know?
        3. Is the user specifically asking about failed tasks?
        4. How should I respond to this query using the available task information?

        Provide your response in the following JSON format:
        {{
            "interpreted_task_ids": ["list", "of", "relevant", "task", "ids"],
            "requested_info": "brief description of the information requested",
            "response_method": "name of the method to use for responding (e.g., 'get_task_info', 'get_latest_results', 'list_task_ids', 'get_background_job_status')",
            "additional_context": "any additional context or instructions for formulating the response",
            "include_failed_tasks": boolean
        }}
        """

        interpretation = self._ask_ai(prompt, include_history=True, system=self.system_prompt())
        
        try:
            result = json.loads(interpretation)
            response = self._generate_task_response(result)
            return response
        except json.JSONDecodeError:
            return f"Error: Unable to interpret the query. Please try rephrasing your question about the tasks."

    def _generate_task_response(self, interpretation: dict) -> str:
        """
        Generate a response based on the interpreted task query.

        Args:
            interpretation (dict): The interpreted query information.

        Returns:
            response (str): The generated response to the query.
        """
        response = f"Interpreted request: {interpretation['requested_info']}\n\n"

        if interpretation['response_method'] == 'list_task_ids':
            response += self.list_task_ids()
        elif interpretation['response_method'] == 'get_background_job_status':
            response += self.get_background_job_status()
        elif interpretation['response_method'] in ['get_task_info', 'get_latest_results']:
            for task_id in interpretation['interpreted_task_ids']:
                if interpretation['response_method'] == 'get_task_info':
                    response += self.get_task_info(task_id) + "\n"
                else:
                    response += self.get_latest_results(task_id) + "\n"
        else:
            response += f"Unable to process the request using method: {interpretation['response_method']}"

        if interpretation.get('include_failed_tasks', False):
            failed_tasks = [task for task in self.failed_tasks]
            if failed_tasks:
                response += "\nFailed Tasks:\n"
                for task in failed_tasks:
                    response += f"- Task ID: {task['description']}\n  Result: {task['result']}\n"
            else:
                response += "\nNo failed tasks found."

        if interpretation['additional_context']:
            response += f"\nAdditional context: {interpretation['additional_context']}"

        return response
