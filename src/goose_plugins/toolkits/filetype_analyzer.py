import os
import json
from goose.toolkit.base import Toolkit, tool


class FileTypeAnalyzerToolkit(Toolkit):
    """Analyzes the percentage distribution of file types in a project."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @tool
    def analyze_file_types(
        self,
        project_dir: str,
        include_subdirectories: bool = True,
        exclude_paths: list[str] = [],
        output_format: str = "json",
        output_file: str | None = None,
        visualize: bool = True,
    ) -> dict:
        """
        Analyze file types in a directory with explicit path exclusions.

        Args:
            project_dir (str): Path to the project directory.
            include_subdirectories (bool): Include subdirectories in the analysis.
            exclude_paths (list[str]): List of file or directory paths to exclude.
            output_format (str): Output format, either "json" or "txt".
            output_file (str, optional): Output file for results.
            visualize (bool): Whether to visualize results in CLI.

        Returns:
            dict: Analysis results.
        """
        try:
            analyzer = FileTypeAnalyzer()
            result = analyzer.analyze(
                project_dir, include_subdirectories, exclude_paths
            )

            if output_file:
                reporter = ReportGenerator()
                reporter.generate_report(result, output_format, output_file)

            if visualize:
                visualizer = Visualizer()
                visualizer.display_summary(result)
                visualizer.display_bar_chart(result)
                visualizer.display_pie_chart(result)

            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


class FileTypeAnalyzer:
    """Performs file type analysis with explicit path exclusions."""

    def analyze(self, directory, recursive=True, exclude_paths=None):
        """
        Analyze file types in a directory.

        Args:
            directory (str): Path to the directory to analyze.
            recursive (bool): Whether to include subdirectories.
            exclude_paths (list, optional): List of file or directory paths to exclude.

        Returns:
            dict: Analysis results including file counts, percentages, and total files.
        """

        if not os.path.exists(directory):
            raise FileNotFoundError(f"The directory '{directory}' does not exist.")

        file_counts = {}
        total_files = 0

        exclude_paths = [
            os.path.abspath(os.path.join(directory, path))
            for path in (exclude_paths or [])
        ]

        for root, _, files in os.walk(directory):
            # Skip excluded directories and their subdirectories
            if any(root.startswith(excluded) for excluded in exclude_paths):
                continue

            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))

                # Skip excluded files
                if any(file_path.startswith(excluded) for excluded in exclude_paths):
                    continue

                # Get the file extension and count it
                ext = os.path.splitext(file)[1].lower()
                file_counts[ext] = file_counts.get(ext, 0) + 1
                total_files += 1

            if not recursive:
                break

        # Calculate percentages
        percentages = {
            ext: (count / total_files) * 100 for ext, count in file_counts.items()
        }

        return {
            "file_counts": file_counts,
            "percentages": percentages,
            "total_files": total_files,
        }


class ReportGenerator:
    """Generates analysis reports."""

    def generate_report(self, data, format, output_file):
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(data, f, indent=4)
        elif format == "txt":
            with open(output_file, "w") as f:
                for ext, percent in data["percentages"].items():
                    f.write(f"{ext}: {percent:.2f}%\n")


class Visualizer:
    """Creates visual CLI representations for file type analysis."""

    def display_bar_chart(self, data: dict):
        """
        Display a bar chart showing the percentage of file types.

        Args:
            data (dict): Analysis results containing percentages of file types.
        """
        print("\nFile Type Distribution (Bar Chart):\n")
        for ext, percent in sorted(data["percentages"].items(), key=lambda x: -x[1]):
            bar = "█" * int(percent / 2)
            print(f"{ext or 'Other':<10}: {bar} {percent:.2f}%")

    def display_pie_chart(self, data: dict):
        """
        Display a pie chart-like visualization for file type percentages.d

        Args:
            data (dict): Analysis results containing percentages of file types.
        """
        print("\nFile Type Distribution (Pie Chart):\n")
        total = sum(data["percentages"].values())
        for ext, percent in sorted(data["percentages"].items(), key=lambda x: -x[1]):
            segment = "○" * int((percent / total) * 20)
            print(f"{ext or 'Other':<10}: {segment} {percent:.2f}%")

    def display_summary(self, data: dict):
        """
        Display a summary of the analysis.

        Args:
            data (dict): Analysis results containing total files and counts.
        """
        print("\nFile Type Analysis Summary:\n")
        print(f"Total Files Analyzed: {data['total_files']}")
        print("File Counts by Type:")
        for ext, count in sorted(data["file_counts"].items(), key=lambda x: -x[1]):
            print(f"  {ext or 'Other':<10}: {count}")
