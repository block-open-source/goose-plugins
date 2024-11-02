from goose.toolkit.base import tool
import json
import time
import threading
from ..utils.task_utils import format_task_status, parse_duration, write_intermediate_result, trigger_apple_dialog

class TaskManagementTools:
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
        duration_seconds = parse_duration(duration)
        interval_seconds = 20  # Enforcing 20-second interval
        task_id = f"task_{int(time.time())}"
        self.pause_flags[task_id] = False
        self.latest_results[task_id] = {"current_answer": "", "iterations": 0, "status": "running"}
        self.notifier.status(f"Starting autonomous loop for task {task_id}: {task_description}")

        def continuous_background_task():
            start_time = time.time()
            current_answer = ""
            iterations = 0

            # Initialize the task in latest_results
            self.latest_results[task_id] = {
                "current_answer": current_answer,
                "iterations": iterations,
                "status": "running",
                "elapsed_time": 0
            }

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
                            break

                        current_answer = refined_answer
                        self.latest_results[task_id].update({
                            "current_answer": current_answer, 
                            "iterations": iterations,
                            "status": "running",
                            "elapsed_time": elapsed_time
                        })

                        # Write intermediate result
                        write_intermediate_result(self.results_folder, task_id, iterations, current_answer)

                    except Exception as e:
                        error_message = f"Error in iteration {iterations}: {str(e)}"
                        # self.logger.error(f"Task {task_id}: {error_message}")
                        write_intermediate_result(self.results_folder, task_id, iterations, f"ERROR: {error_message}")
                        # Continue to the next iteration instead of breaking the loop
                        continue

                    time.sleep(interval_seconds)

                self.complete_task(task_id, f"Continuous task '{task_description}' completed. Final answer: {current_answer}")
                if task_id in self.latest_results:
                    self.latest_results[task_id]["status"] = "completed"
                trigger_apple_dialog("Task Completed", f"Continuous task completed after {iterations} iterations.")

            except Exception as e:
                error_message = f"Critical error in task {task_id}: {str(e)}"
                self.notify(error_message)
                write_intermediate_result(self.results_folder, task_id, iterations, f"CRITICAL ERROR: {error_message}")
                self.complete_task(task_id, f"Continuous task '{task_description}' failed. Error: {error_message}")
                if task_id in self.latest_results:
                    self.latest_results[task_id]["status"] = "failed"
                trigger_apple_dialog("Task Failed", f"Continuous task failed after {iterations} iterations.")

        self.autonomous_mode = True
        self.notify(f"Starting continuous background task: {task_description}")
        self.add_task(task_id, task_description, duration_seconds)
        
        thread = threading.Thread(target=continuous_background_task)
        self.loop_threads[task_id] = thread
        thread.start()
        return f"Continuous background task '{task_description}' (ID: {task_id}) has been started with a duration of {duration}."

    @tool
    def get_background_job_status(self) -> str:
        """Get the status of all background jobs (ongoing, completed, and failed)."""
        current_time = time.time()
        status = ["Background Job Status:\n"]
        
        if self.ongoing_tasks:
            status.append("\nOngoing Tasks:")
            for task_id, task in self.ongoing_tasks.items():
                status.append(format_task_status(task_id, task, current_time))
        
        if self.completed_tasks:
            status.append("\nCompleted Tasks:")
            for task in self.completed_tasks:
                status.append(format_task_status(task["description"], task, current_time))
        
        if self.failed_tasks:
            status.append("\nFailed Tasks:")
            for task in self.failed_tasks:
                status.append(format_task_status(task["description"], task, current_time))
        
        return "\n".join(status)

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