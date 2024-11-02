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

class CriticalSystemsThinking(Toolkit):
    """Critical systems thinking toolkit for understanding and solving complex problems."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue = queue.Queue()
        self.autonomous_mode = False
        self.ongoing_tasks = {}
        self.completed_tasks = []

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

    def complete_task(self, task_id: str, result: str):
        """Move a task from ongoing to completed and record result."""
        if task_id in self.ongoing_tasks:
            task = self.ongoing_tasks.pop(task_id)
            task.update({"result": result, "end_time": time.time()})
            self.completed_tasks.append(task)

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

    @tool
    def autonomous_loop(self, task_description: str, interval: str = "30s", max_iterations: int = 10) -> str:
        """
        Run a task autonomously in the background, continuously working on a problem and building a final answer.

        Args:
            task_description (str): A description of the task to be performed.
            interval (str): The interval between each iteration. Format: "<number><unit>".
                            Units: 's' for seconds, 'm' for minutes, 'h' for hours.
                            Examples: "30s", "5m", "1h". Default: "30s".
            max_iterations (int): The maximum number of iterations to perform. Default: 10.

        Returns:
            str: A message indicating the continuous background task has been started.
        """
        interval_seconds = self._parse_duration(interval)
        task_id = f"task_{int(time.time())}"

        def continuous_background_task():
            iteration = 0
            final_answer = ""
            while iteration < max_iterations:
                iteration += 1
                self.notify(f"Starting iteration {iteration} of {max_iterations}")
                
                # Perform analysis and build upon the final answer
                analysis = self._perform_analysis(task_description, final_answer)
                final_answer += f"\n\nIteration {iteration} result:\n{analysis}"
                
                self.notify(f"Iteration {iteration} completed. Waiting for {interval} before next iteration.")
                time.sleep(interval_seconds)
            
            self._trigger_apple_dialog("Task Completed", f"Continuous task completed after {max_iterations} iterations.")
            self.complete_task(task_id, f"Continuous task '{task_description}' completed. Final answer: {final_answer}")

        self.autonomous_mode = True
        self.notify(f"Starting continuous background task: {task_description}")
        self.add_task(task_id, task_description, interval_seconds * max_iterations)
        
        threading.Thread(target=continuous_background_task).start()
        return f"Continuous background task '{task_description}' (ID: {task_id}) has been started with {max_iterations} iterations and {interval} interval."

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
        """Get the status of all background jobs (ongoing and completed)."""
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
            self.notifier.status(f"reviewing content...")
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
