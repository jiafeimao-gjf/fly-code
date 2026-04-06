"""Bash execution tool."""

import subprocess
import sys
from pathlib import Path

from core.tools.base import BaseTool, ToolResult


class BashTool(BaseTool):
    """Tool for executing bash commands."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """Execute bash commands.
- command: The shell command to execute
- cwd: Working directory (optional, defaults to current project root)"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for command execution",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                },
            },
            "required": ["command"],
        }

    def execute(self, command: str, cwd: str = "", timeout: int = 30, **kwargs) -> ToolResult:
        """Execute bash command."""
        try:
            workdir = Path(cwd) if cwd else Path.cwd()

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(workdir),
                timeout=timeout or self.timeout,
            )

            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")

            output_text = "\n".join(output) if output else f"Command exited with code {result.returncode}"

            return ToolResult(
                success=(result.returncode == 0),
                content=output_text,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}",
                metadata={
                    "returncode": result.returncode,
                    "command": command,
                    "cwd": str(workdir),
                },
            )

        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(False, "", f"Error executing command: {str(e)}")
