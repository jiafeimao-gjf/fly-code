"""Code problem analysis and resolution module."""

import ast
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class Issue:
    """Represents a code issue."""
    severity: str  # error, warning, info
    line: Optional[int]
    message: str
    code: Optional[str] = None


class Analyzer:
    """Analyzes code for problems and provides solutions."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def analyze_file(self, file_path: Path) -> list[Issue]:
        """Analyze a single Python file for issues."""
        issues = []

        if not file_path.exists():
            issues.append(Issue("error", None, f"File not found: {file_path}"))
            return issues

        try:
            content = file_path.read_text()
            tree = ast.parse(content)

            # Check for syntax errors already handled by ast.parse
            for node in ast.walk(tree):
                issues.extend(self._check_node(node, file_path))

        except SyntaxError as e:
            issues.append(Issue("error", e.lineno, f"Syntax error: {e.msg}", e.text))
        except Exception as e:
            issues.append(Issue("error", None, f"Analysis error: {e}"))

        return issues

    def _check_node(self, node: ast.AST, file_path: Path) -> list[Issue]:
        """Check an AST node for issues."""
        issues = []

        if isinstance(node, ast.FunctionDef) and len(node.args.args) > 10:
            issues.append(Issue(
                "warning",
                node.lineno,
                f"Function '{node.name}' has too many parameters ({len(node.args.args)}). Consider refactoring.",
            ))

        if isinstance(node, ast.FunctionDef) and node.name.isupper():
            issues.append(Issue(
                "info",
                node.lineno,
                f"Function '{node.name}' uses CAPS naming. PEP8 recommends PascalCase for classes, snake_case for functions.",
            ))

        if isinstance(node, ast.Try):
            if len(node.handlers) == 0:
                issues.append(Issue(
                    "warning",
                    node.lineno,
                    "Empty try-except block.",
                ))

        return issues

    def analyze_directory(self, dir_path: Path, pattern: str = "*.py") -> list[tuple[Path, list[Issue]]]:
        """Analyze all Python files in a directory."""
        results = []
        for py_file in dir_path.rglob(pattern):
            if "__pycache__" not in str(py_file):
                issues = self.analyze_file(py_file)
                if issues:
                    results.append((py_file, issues))
        return results

    def check_documentation(self, file_path: Path) -> list[Issue]:
        """Check if Python file has proper documentation."""
        issues = []

        if not file_path.exists():
            return [Issue("error", None, f"File not found: {file_path}")]

        content = file_path.read_text()
        tree = ast.parse(content)

        # Check module docstring
        if (not ast.get_docstring(tree) and
            file_path.name not in ("__init__.py", "setup.py") and
            file_path.name != "__main__.py"):
            issues.append(Issue(
                "info",
                1,
                f"Module '{file_path.name}' lacks a docstring.",
            ))

        # Check function docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append(Issue(
                        "info",
                        node.lineno,
                        f"{'Class' if isinstance(node, ast.ClassDef) else 'Function'} '{node.name}' lacks a docstring.",
                    ))

        return issues

    def suggest_fixes(self, issue: Issue) -> str:
        """Suggest a fix for a given issue."""
        suggestions = {
            "too_many_parameters": "Consider using a data class or dictionary to group parameters.",
            "missing_docstring": "Add a docstring to document the purpose and usage.",
            "empty_except": "Add exception handling logic or remove the empty try-except block.",
            "naming_convention": "Follow PEP8 naming conventions: PascalCase for classes, snake_case for functions.",
        }

        if "too many parameters" in issue.message:
            return suggestions["too_many_parameters"]
        elif "lacks a docstring" in issue.message:
            return suggestions["missing_docstring"]
        elif "Empty try-except" in issue.message:
            return suggestions["empty_except"]
        elif "CAPS naming" in issue.message:
            return suggestions["naming_convention"]

        return "Review the code and fix according to best practices."

    def print_report(self, results: list[tuple[Path, list[Issue]]]) -> None:
        """Print analysis report."""
        if not results:
            logger.info("No issues found.")
            return

        for file_path, issues in results:
            logger.info(f"\n{'='*60}")
            logger.info(f"File: {file_path}")
            logger.info(f"{'='*60}")

            for issue in issues:
                line_info = f"Line {issue.line}: " if issue.line else ""
                logger.info(f"[{issue.severity.upper()}] {line_info}{issue.message}")
                logger.info(f"  Suggestion: {self.suggest_fixes(issue)}")
