"""Code generation and modification module."""

from pathlib import Path
from typing import Protocol
from utils.logger import logger


class CodeGenerator(Protocol):
    """Protocol for code generation strategies."""

    def generate(self, context: dict) -> str:
        """Generate code based on context."""
        ...


class Developer:
    """Handles code generation and modification."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def create_module(self, module_name: str, content: str) -> Path:
        """Create a new Python module with content."""
        module_path = self.project_root / f"{module_name}.py"
        module_path.write_text(content)
        logger.info(f"Created module: {module_path}")
        return module_path

    def create_package(self, package_name: str, modules: dict[str, str]) -> Path:
        """Create a Python package with multiple modules."""
        package_dir = self.project_root / package_name
        package_dir.mkdir(exist_ok=True)

        (package_dir / "__init__.py").write_text('"""Package {}."""\n'.format(package_name))

        for module_name, content in modules.items():
            (package_dir / f"{module_name}.py").write_text(content)
            logger.info(f"Created module: {package_dir / module_name}.py")

        return package_dir

    def modify_file(self, file_path: Path, old_content: str, new_content: str) -> None:
        """Replace old_content with new_content in file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text()
        if old_content not in content:
            raise ValueError(f"Content to replace not found in {file_path}")

        file_path.write_text(content.replace(old_content, new_content))
        logger.info(f"Modified: {file_path}")

    def append_to_file(self, file_path: Path, content: str) -> None:
        """Append content to a file."""
        file_path.write_text(file_path.read_text() + content)
        logger.info(f"Appended to: {file_path}")

    def generate_from_template(self, template: str, context: dict) -> str:
        """Generate code from a template string with variable substitution."""
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def create_test(self, module_name: str, test_content: str) -> Path:
        """Create a test file for a module."""
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir(exist_ok=True)

        test_path = tests_dir / f"test_{module_name}.py"
        test_path.write_text(test_content)
        logger.info(f"Created test: {test_path}")
        return test_path
