import os
import ast
from goose.toolkit.base import Toolkit, tool
import radon.complexity as rc
import radon.metrics as rm


class CodeComplexityToolkit(Toolkit):
    """A toolkit for analyzing the complexity of Python code in a given directory."""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)

    @tool
    def get_python_files(self, directory: str) -> list:
        """Retrieve all Python files from the specified directory.

        Args:
            directory (str): The directory to search for Python files.

        Returns:
            list: A list of paths to all Python files in the directory.
        """
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(directory)
            for file in files
            if file.endswith(".py")
        ]

    @tool
    def analyze_complexity(self, directory: str) -> dict:
        """Analyze the complexity of Python code in a directory.

        Args:
            directory (str): The path to the directory containing Python files to analyze.

        Returns:
            dict: A dictionary containing the average complexity metrics (Cyclomatic Complexity, Halstead Metrics,
                  and Maintainability Index) for all Python files in the directory, or an error message if no
                  valid Python files are found.
        """
        python_files = self.get_python_files(directory)
        if not python_files:
            return {"error": f"No Python files found in the directory: {directory}"}

        complexity_results = {
            "cyclomatic_complexity": 0,
            "halstead_metrics": 0,
            "maintainability_index": 0,
            "file_count": 0,
        }

        for file in python_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    code = f.read()

                # Process each complexity metric and update the results
                complexity_results[
                    "cyclomatic_complexity"
                ] += self.cyclomatic_complexity(code)
                halstead_result = self.halstead_complexity(code)
                complexity_results["halstead_metrics"] += (
                    halstead_result["halstead_volume"] if halstead_result else 0
                )
                complexity_results[
                    "maintainability_index"
                ] += self.maintainability_index(code)
                complexity_results["file_count"] += 1

            except Exception as e:
                complexity_results["error"] = f"Error processing {file}: {str(e)}"
                continue

        if complexity_results["file_count"] > 0:
            # Average the results
            return {
                "avg_cyclomatic_complexity": complexity_results["cyclomatic_complexity"]
                / complexity_results["file_count"],
                "avg_halstead_complexity": complexity_results["halstead_metrics"]
                / complexity_results["file_count"],
                "avg_maintainability_index": complexity_results["maintainability_index"]
                / complexity_results["file_count"],
            }
        else:
            return {"error": "No valid Python files to analyze."}

    @tool
    def cyclomatic_complexity(self, code: str) -> int:
        """Calculate the Cyclomatic Complexity of a given Python code.

        Args:
            code (str): The Python code as a string to analyze.

        Returns:
            int: The Cyclomatic Complexity of the code.
        """
        try:
            complexity = rc.cc_visit(ast.parse(code))
            return complexity
        except Exception as e:
            self.notifier.log(f"Error calculating cyclomatic complexity: {str(e)}")
            return 0

    @tool
    def halstead_complexity(self, code: str) -> dict:
        """Calculate Halstead Complexity metrics of the given Python code.

        Args:
            code (str): The Python code as a string to analyze.

        Returns:
            dict: A dictionary of Halstead metrics (e.g., volume, difficulty, effort).
        """
        try:
            return rm.halstead_metrics(code)
        except Exception as e:
            self.notifier.log(f"Error calculating Halstead complexity: {str(e)}")
            return {}

    @tool
    def maintainability_index(self, code: str) -> int:
        """Calculate the Maintainability Index of the given Python code.

        Args:
            code (str): The Python code as a string to analyze.

        Returns:
            int: The Maintainability Index of the code.
        """
        try:
            return rm.maintainability_index(code)
        except Exception as e:
            self.notifier.log(f"Error calculating maintainability index: {str(e)}")
            return 0

    @tool
    def aggregate_results(self, results: dict) -> dict:
        """Aggregate the complexity results from all analyzed files.

        Args:
            results (dict): A dictionary containing lists of complexity metrics across multiple files,
                            including Cyclomatic Complexity, Halstead Metrics, and Maintainability Index.

        Returns:
            dict: A dictionary containing the aggregated averages for each complexity metric.
        """
        try:
            aggregated_results = {
                "avg_cyclomatic_complexity": sum(results["cyclomatic_complexity"])
                / len(results["cyclomatic_complexity"]),
                "avg_halstead_complexity": sum(
                    [h["halstead_volume"] for h in results["halstead_metrics"]]
                )
                / len(results["halstead_metrics"]),
                "avg_maintainability_index": sum(results["maintainability_index"])
                / len(results["maintainability_index"]),
            }
            return aggregated_results
        except ZeroDivisionError:
            return {"error": "No valid results to aggregate."}
