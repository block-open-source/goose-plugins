import os
from goose.toolkit.base import Toolkit, tool


class DockerizationToolkit(Toolkit):
    """Dockerizes an application based
    on its project type (Node.js, Python, Java)."""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)

    @tool
    def dockerize(self, project_dir: str, output_dir: str | None = None) -> dict:
        """
        Dockerize a project by generating Docker-related files.

        Args:
            project_dir (str): Path to the project directory.
            output_dir (str, optional): Output directory for Docker files.
        Returns:
            dict: Status of the operation and output details.
        """
        try:
            dockerizer = Dockerizer()
            result = dockerizer.generate(project_dir, output_dir)
            return {"status": "success", "details": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class Dockerizer:
    def detect_project_type(self, project_dir: str) -> str:
        """Detect the project type based on common configuration files."""
        if os.path.exists(os.path.join(project_dir, "package.json")):
            return "nodejs"
        elif os.path.exists(os.path.join(project_dir, "requirements.txt")):
            return "python"
        elif os.path.exists(os.path.join(project_dir, "pom.xml")):
            return "java"
        else:
            raise ValueError("Unsupported project type or no recognizable files found.")

    def generate(self, project_dir: str, output_dir: str | None = None) -> dict:
        """Generate Docker-related files."""
        project_type = self.detect_project_type(project_dir)
        output_dir = output_dir or project_dir
        os.makedirs(output_dir, exist_ok=True)

        # Generate files based on the project type
        if project_type == "nodejs":
            self._generate_nodejs_files(output_dir)
        elif project_type == "python":
            self._generate_python_files(output_dir)
        elif project_type == "java":
            self._generate_java_files(output_dir)

        return {"project_type": project_type, "output_dir": output_dir}

    def _generate_python_files(self, output_dir: str) -> None:
        dockerfile_content = """\
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
        """
        self._write_file(output_dir, "Dockerfile", dockerfile_content)

        dockerignore_content = """\
__pycache__/
*.pyc
.env
.git/
        """
        self._write_file(output_dir, ".dockerignore", dockerignore_content)

    def _generate_nodejs_files(self, output_dir: str) -> None:
        dockerfile_content = """\
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]
        """
        self._write_file(output_dir, "Dockerfile", dockerfile_content)

        dockerignore_content = """\
node_modules/
npm-debug.log
.git/
        """
        self._write_file(output_dir, ".dockerignore", dockerignore_content)

    def _generate_java_files(self, output_dir: str) -> None:
        dockerfile_content = """\
FROM openjdk:17-slim
WORKDIR /app
COPY . .
RUN ./mvnw clean package
CMD ["java", "-jar", "target/app.jar"]
        """
        self._write_file(output_dir, "Dockerfile", dockerfile_content)

        dockerignore_content = """\
target/
.git/
        """
        self._write_file(output_dir, ".dockerignore", dockerignore_content)

    def _write_file(self, directory: str, filename: str, content: str) -> None:
        with open(os.path.join(directory, filename), "w") as f:
            f.write(content)
