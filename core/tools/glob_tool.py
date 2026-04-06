"""Glob tool for finding files."""

import fnmatch
from pathlib import Path

from core.tools.base import BaseTool, ToolResult


class GlobTool(BaseTool):
    """Tool for finding files by pattern."""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return """Find files matching a glob pattern.
- pattern: Glob pattern (e.g., "*.py", "**/*.md", "src/**/*.py")
- cwd: Working directory to search in (defaults to project root)"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory to search in",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                },
            },
            "required": ["pattern"],
        }

    def execute(self, pattern: str, cwd: str = "", max_results: int = 100, **kwargs) -> ToolResult:
        """Execute glob search."""
        try:
            workdir = Path(cwd) if cwd else Path.cwd()

            if not workdir.exists():
                return ToolResult(False, "", f"Directory not found: {cwd}")

            results = []
            for p in workdir.rglob(pattern):
                if "__pycache__" not in str(p) and ".git" not in str(p):
                    results.append(str(p.relative_to(workdir)))
                    if len(results) >= max_results:
                        break

            if not results:
                return ToolResult(True, "No files matched the pattern")

            return ToolResult(
                True,
                "\n".join(results),
                metadata={"count": len(results), "pattern": pattern},
            )

        except Exception as e:
            return ToolResult(False, "", f"Error: {str(e)}")
