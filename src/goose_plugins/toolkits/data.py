"""A toolkit for working with data using DuckDB."""

import duckdb
from goose.toolkit.base import tool, Toolkit
from typing import Optional
from pathlib import Path


class Data(Toolkit):
    """A toolkit for loading, querying and visualizing data using DuckDB."""

    def __init__(self, **kwargs: dict) -> None:
        super().__init__(**kwargs)
        self.conn = duckdb.connect(":memory:")  # In-memory DuckDB connection
        self._tables = {}  # Keep track of loaded tables and their schemas

    def system(self) -> str:
        return """Work with data using DuckDB. You can:
        1. Load data from CSV or Parquet files
        2. Run SQL queries against the loaded data
        3. Create visualizations of the query results

        The visualiztions are powered by youplot, if you get errors that it is not installed,
        let the user know to install it from instructions at https://github.com/red-data-tools/YouPlot
        """

    @tool
    def load(self, path: str, table_name: str, file_type: Optional[str] = None) -> str:
        """
        Load a dataset from a CSV or Parquet file into DuckDB.

        Args:
            path (str): Path to the data file
            table_name (str): Name to give the table in DuckDB
            file_type (Optional[str]): Type of file ('csv' or 'parquet'). If None, will be inferred from extension.
        """
        try:
            # Infer file type if not provided
            if file_type is None:
                file_type = Path(path).suffix.lstrip(".")

            file_type = file_type.lower()
            if file_type not in ["csv", "parquet"]:
                raise ValueError(f"Unsupported file type: {file_type}. Must be 'csv' or 'parquet'")

            # Load the data using DuckDB's native read functions
            if file_type == "csv":
                self.conn.sql(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{path}')")
            else:  # parquet
                self.conn.sql(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{path}')")

            # Get the schema information
            schema_info = self.conn.sql(f"DESCRIBE {table_name}").fetchall()
            schema_str = "\n".join([f"{col[0]}: {col[1]}" for col in schema_info])

            # Store table info
            self._tables[table_name] = {"path": path, "type": file_type, "schema": schema_str}
            self.notifier.log(
                "\n\n" + f"Successfully loaded {path} as table '{table_name}'\nSchema:\n{schema_str}" + "\n"
            )
            return f"Successfully loaded {path} as table '{table_name}'\nSchema:\n{schema_str}"
        except Exception as e:
            return f"Error loading file: {str(e)}"

    @tool
    def query(self, sql: str) -> str:
        """
        Execute a SQL query against the loaded datasets.

        Args:
            sql (str): SQL query to execute
        """
        try:
            # Execute the query
            result = self.conn.sql(sql)

            # Convert to a formatted string
            rows = result.fetchall()
            if not rows:
                return "Query returned no results"

            # Column names already fetched above with rows
            columns = [col[0] for col in result.description]

            # Calculate column widths
            widths = [len(col) for col in columns]
            for row in rows:
                for i, val in enumerate(row):
                    widths[i] = max(widths[i], len(str(val)))

            # Format header
            header = " | ".join(f"{col:<{width}}" for col, width in zip(columns, widths))
            separator = "-" * len(header)

            # Format rows
            formatted_rows = []
            for row in rows:
                formatted_row = " | ".join(f"{str(val):<{width}}" for val, width in zip(row, widths))
                formatted_rows.append(formatted_row)

            # Combine everything
            result_str = f"{header}\n{separator}\n" + "\n".join(formatted_rows)

            self.notifier.log("\n" + result_str + "\n")
            return result_str
        except Exception as e:
            return f"Error executing query: {str(e)}"

    @tool
    def visualize(
        self,
        sql: str,
        chart_type: str,
        args: str,
    ) -> str:
        """
        Create a visualization using YouPlot (uplot).

        Args:
            sql (str): SQL query to get the data to visualize
            chart_type (str): Type of chart
              (barplot, histogram, lineplot, lineplots, scatter, density, boxplot, count, colors)
            args (str): Additional arguments to pass to youplot
        """
        import tempfile
        import subprocess
        import shlex

        try:
            # First execute the query and save to a temporary CSV
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
                # Execute query and write directly to CSV
                self.conn.sql(sql).write_csv(tmp.name)
                tmp_path = tmp.name

            # Construct the uplot command
            cmd = ["uplot", chart_type, "-d", ",", "-H"]
            if args:  # Add any additional arguments
                cmd.extend(shlex.split(args))
            cmd.extend([tmp_path])

            # Run uplot command and capture output
            # We use shell=True because we need shell redirection with <
            cmd_str = shlex.join(cmd)
            result = subprocess.run(cmd_str, shell=True, text=True, capture_output=True, check=True)

            # Store the output before cleanup
            output = result.stdout + result.stderr

            # Clean up the temporary file after we're done with it
            Path(tmp_path).unlink()

            self.notifier.log("\n" + output + "\n")
            return output
        except subprocess.CalledProcessError as e:
            return f"Error running visualization: {e.stderr}"
        except Exception as e:
            return f"Error creating visualization: {str(e)}"

    def __del__(self) -> None:
        """Cleanup the database connection when the toolkit is destroyed."""
        if hasattr(self, "conn"):
            self.conn.close()
