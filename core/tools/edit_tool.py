"""Edit tool for modifying files with diff/patch."""

import re
from pathlib import Path

from core.tools.base import BaseTool, ToolResult


class EditTool(BaseTool):
    """Tool for editing files with precise modifications."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return """Edit an existing file with precise modifications.
Supports three modes:
- replace: Replace old_content with new_content (first occurrence)
- insert_after: Insert new_content after the line containing search_line
- insert_before: Insert new_content before the line containing search_line"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["replace", "insert_after", "insert_before", "delete"],
                    "description": "The edit operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_content": {
                    "type": "string",
                    "description": "Content to replace (for replace operation)",
                },
                "new_content": {
                    "type": "string",
                    "description": "New content (for replace, insert_after, insert_before)",
                },
                "search_line": {
                    "type": "string",
                    "description": "Line to search for (for insert_after, insert_before)",
                },
            },
            "required": ["operation", "path"],
        }

    def execute(
        self,
        operation: str,
        path: str,
        old_content: str = "",
        new_content: str = "",
        search_line: str = "",
        **kwargs,
    ) -> ToolResult:
        """Execute edit operation."""
        p = Path(path)

        if not p.exists():
            return ToolResult(False, "", f"File not found: {path}")

        try:
            content = p.read_text(encoding="utf-8")
            original_content = content

            if operation == "replace":
                if old_content not in content:
                    return ToolResult(
                        False,
                        "",
                        f"Content to replace not found in file. Ensure exact match.",
                    )
                content = content.replace(old_content, new_content, 1)

            elif operation == "insert_after":
                if search_line not in content:
                    return ToolResult(False, "", f"Search line not found: {search_line}")
                idx = content.index(search_line) + len(search_line)
                content = content[:idx] + "\n" + new_content + content[idx:]

            elif operation == "insert_before":
                if search_line not in content:
                    return ToolResult(False, "", f"Search line not found: {search_line}")
                idx = content.index(search_line)
                content = content[:idx] + new_content + "\n" + content[idx:]

            elif operation == "delete":
                if old_content not in content:
                    return ToolResult(False, "", f"Content to delete not found")
                content = content.replace(old_content, "", 1)

            else:
                return ToolResult(False, "", f"Unknown operation: {operation}")

            # Write changes
            p.write_text(content, encoding="utf-8")

            return ToolResult(
                True,
                f"Successfully edited {path}",
                metadata={
                    "path": str(p.absolute()),
                    "original_size": len(original_content),
                    "new_size": len(content),
                },
            )

        except PermissionError:
            return ToolResult(False, "", f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(False, "", f"Error: {str(e)}")
