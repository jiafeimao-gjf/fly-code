"""Git operations tool."""

import subprocess
from pathlib import Path
from typing import Optional

from core.tools.base import BaseTool, ToolResult


class GitTool(BaseTool):
    """Tool for git operations."""

    def __init__(self, cwd: Optional[str] = None):
        self._cwd = cwd

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Execute git commands for version control"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "log", "diff", "add", "commit", "branch", "checkout", "push", "pull"],
                    "description": "Git operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "Repository path (defaults to current directory)",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files for add/commit operations",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name for checkout/branch operations",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
            },
            "required": ["operation"],
        }

    def execute(
        self,
        operation: str,
        path: Optional[str] = None,
        files: Optional[list[str]] = None,
        message: Optional[str] = None,
        branch: Optional[str] = None,
        remote: str = "origin",
        **kwargs,
    ) -> ToolResult:
        """Execute git operation."""
        cwd = Path(path) if path else (Path(self._cwd) if self._cwd else Path.cwd())

        if not (cwd / ".git").exists():
            return ToolResult(
                success=False,
                content="",
                error=f"Not a git repository: {cwd}",
                metadata={},
            )

        try:
            if operation == "status":
                return self._git_status(cwd)
            elif operation == "log":
                return self._git_log(cwd)
            elif operation == "diff":
                return self._git_diff(cwd, files)
            elif operation == "add":
                return self._git_add(cwd, files)
            elif operation == "commit":
                return self._git_commit(cwd, message or "")
            elif operation == "branch":
                return self._git_branch(cwd, branch)
            elif operation == "checkout":
                return self._git_checkout(cwd, branch)
            elif operation == "push":
                return self._git_push(cwd, remote)
            elif operation == "pull":
                return self._git_pull(cwd, remote)
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Unknown operation: {operation}",
                    metadata={},
                )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
                metadata={},
            )

    def _git_status(self, cwd: Path) -> ToolResult:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip() or "No changes"
        return ToolResult(
            success=result.returncode == 0,
            content=output,
            error="" if result.returncode == 0 else result.stderr,
            metadata={"returncode": result.returncode},
        )

    def _git_log(self, cwd: Path, limit: int = 10) -> ToolResult:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--oneline", "--decorate"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            success=result.returncode == 0,
            content=result.stdout.strip(),
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_diff(self, cwd: Path, files: Optional[list[str]] = None) -> ToolResult:
        cmd = ["git", "diff", "--staged"] if not files else ["git", "diff"] + files
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return ToolResult(
            success=result.returncode == 0,
            content=result.stdout.strip() or "No changes",
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_add(self, cwd: Path, files: Optional[list[str]] = None) -> ToolResult:
        cmd = ["git", "add", "-A"] if not files else ["git", "add"] + files
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return ToolResult(
            success=result.returncode == 0,
            content="Added files" if result.returncode == 0 else "",
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_commit(self, cwd: Path, message: str) -> ToolResult:
        if not message:
            return ToolResult(
                success=False,
                content="",
                error="Commit message required",
                metadata={},
            )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            success=result.returncode == 0,
            content=result.stdout.strip(),
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_branch(self, cwd: Path, name: Optional[str] = None) -> ToolResult:
        if name:
            result = subprocess.run(
                ["git", "branch", name],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            action = f"Created branch: {name}"
        else:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            action = result.stdout.strip()
        return ToolResult(
            success=result.returncode == 0,
            content=action,
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_checkout(self, cwd: Path, branch: Optional[str] = None) -> ToolResult:
        if not branch:
            return ToolResult(
                success=False,
                content="",
                error="Branch name required",
                metadata={},
            )
        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            success=result.returncode == 0,
            content=f"Switched to branch: {branch}",
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_push(self, cwd: Path, remote: str) -> ToolResult:
        result = subprocess.run(
            ["git", "push", remote],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            success=result.returncode == 0,
            content=result.stdout.strip() or "Pushed to origin",
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def _git_pull(self, cwd: Path, remote: str) -> ToolResult:
        result = subprocess.run(
            ["git", "pull", remote],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return ToolResult(
            success=result.returncode == 0,
            content=result.stdout.strip() or "Pulled from origin",
            error=result.stderr if result.returncode != 0 else "",
            metadata={"returncode": result.returncode},
        )

    def get_schema(self) -> dict:
        """Get JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
