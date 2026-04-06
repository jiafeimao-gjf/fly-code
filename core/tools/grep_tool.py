"""Grep tool for searching file contents."""

import re
from pathlib import Path

from core.tools.base import BaseTool, ToolResult


class GrepTool(BaseTool):
    """Tool for searching file contents."""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return """Search for text pattern in files.
- pattern: Regular expression pattern to search
- path: File or directory to search in
- file_pattern: Only search in files matching this glob (e.g., "*.py")
- context: Number of context lines around match (default: 0)"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Only search in files matching this glob pattern",
                },
                "context": {
                    "type": "integer",
                    "description": "Number of context lines around match (default: 0)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                },
            },
            "required": ["pattern", "path"],
        }

    def execute(
        self,
        pattern: str,
        path: str,
        file_pattern: str = "*",
        context: int = 0,
        max_results: int = 50,
        **kwargs,
    ) -> ToolResult:
        """Execute grep search."""
        try:
            search_path = Path(path)
            if not search_path.exists():
                return ToolResult(False, "", f"Path not found: {path}")

            results = []
            regex = re.compile(pattern)

            files_to_search = [search_path] if search_path.is_file() else []
            if search_path.is_dir():
                files_to_search.extend(search_path.rglob(file_pattern))

            for f in files_to_search:
                if "__pycache__" in str(f) or ".git" in str(f):
                    continue

                try:
                    lines = f.read_text(encoding="utf-8").split("\n")
                    for i, line in enumerate(lines, 1):
                        if regex.search(line):
                            if context > 0:
                                start = max(0, i - context - 1)
                                end = min(len(lines), i + context)
                                snippet = "\n".join(f"{j}: {lines[j-1]}" for j in range(start + 1, end + 1))
                            else:
                                snippet = f"{i}: {line}"

                            results.append(f"{f}:{snippet}")
                            if len(results) >= max_results:
                                break
                except (UnicodeDecodeError, PermissionError):
                    continue

                if len(results) >= max_results:
                    break

            if not results:
                return ToolResult(True, f"No matches found for: {pattern}")

            return ToolResult(
                True,
                "\n---\n".join(results),
                metadata={"count": len(results), "pattern": pattern},
            )

        except re.error as e:
            return ToolResult(False, "", f"Invalid regex pattern: {e}")
        except Exception as e:
            return ToolResult(False, "", f"Error: {str(e)}")
