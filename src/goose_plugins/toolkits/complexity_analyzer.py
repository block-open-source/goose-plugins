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
            complexity_list = rc.cc_visit(ast.parse(code))
            total_complexity = 0

            # Iterate over each item in the complexity list
            for item in complexity_list:
                if hasattr(item, "complexity"):
                    # Add complexity of the function or class's top-level complexity
                    total_complexity += item.complexity

                # For classes, add complexity of methods if any
                if hasattr(item, "methods"):
                    for method in item.methods:
                        total_complexity += method.complexity
            return total_complexity
        except Exception as e:
            print(e)
            self.notifier.log(f"Error calculating cyclomatic complexity: {str(e)}")
            return 0

    @tool
    def halstead_complexity(self, code: str) -> dict:
        """Calculate Halstead Complexity metrics of the given Python code.

        Args:
            code (str): The Python code as a string to analyze.

        Returns:
            dict: A dictionary containing the Halstead metrics, including 'halstead_volume'.
        """
        from radon.metrics import h_visit

        try:
            halstead_report = h_visit(code)
            return {
                "halstead_volume": halstead_report.total.volume,
                "details": {
                    "vocabulary": halstead_report.total.vocabulary,
                    "length": halstead_report.total.length,
                    "calculated_length": halstead_report.total.calculated_length,
                    "difficulty": halstead_report.total.difficulty,
                    "effort": halstead_report.total.effort,
                    "time": halstead_report.total.time,
                    "bugs": halstead_report.total.bugs,
                },
            }
        except Exception as e:
            print(e)
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
            mi_score = rm.mi_visit(code, multi=True)
            return mi_score
        except Exception as e:
            print(e)
            self.notifier.log(f"Error calculating maintainability index: {str(e)}")
            return 0
