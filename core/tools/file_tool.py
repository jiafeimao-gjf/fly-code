"""File operations tool."""

import os
from pathlib import Path
from typing import Any

from core.tools.base import BaseTool, ToolResult


class FileTool(BaseTool):
    """Tool for file operations: read, write, create directories."""

    @property
    def name(self) -> str:
        return "file_operations"

    @property
    def description(self) -> str:
        return """File operations tool for reading and writing files.
- file_read: Read contents of a file
- file_write: Write content to a file (creates or overwrites)
- directory_create: Create a directory"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["file_read", "file_write", "directory_create"],
                    "description": "The file operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for file_write operation)",
                },
            },
            "required": ["operation", "path"],
        }

    def execute(self, operation: str, path: str, content: str = "", **kwargs) -> ToolResult:
        """Execute file operation."""
        p = Path(path)

        try:
            if operation == "file_read":
                if not p.exists():
                    return ToolResult(False, "", f"File not found: {path}")
                if not p.is_file():
                    return ToolResult(False, "", f"Not a file: {path}")
                content = p.read_text(encoding="utf-8")
                return ToolResult(True, content, metadata={"path": str(p.absolute())})

            elif operation == "file_write":
                # Create parent directories if needed
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return ToolResult(
                    True,
                    f"Successfully wrote to {path}",
                    metadata={"path": str(p.absolute()), "bytes": len(content)},
                )

            elif operation == "directory_create":
                p.mkdir(parents=True, exist_ok=True)
                return ToolResult(True, f"Directory created: {path}")

            else:
                return ToolResult(False, "", f"Unknown operation: {operation}")

        except PermissionError:
            return ToolResult(False, "", f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, "", f"Error: {str(e)}")
