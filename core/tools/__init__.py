"""Tools for the programming agent."""

from core.tools.base import BaseTool, ToolResult
from core.tools.file_tool import FileTool
from core.tools.edit_tool import EditTool
from core.tools.bash_tool import BashTool
from core.tools.glob_tool import GlobTool
from core.tools.grep_tool import GrepTool
from core.tools.git_tool import GitTool

# Registry of all available tools
TOOL_REGISTRY: dict[str, type[BaseTool]] = {
    "file_operations": FileTool,
    "edit_file": EditTool,
    "bash": BashTool,
    "glob": GlobTool,
    "grep": GrepTool,
    "git": GitTool,
}


def get_tool(name: str) -> BaseTool | None:
    """Get a tool instance by name."""
    tool_class = TOOL_REGISTRY.get(name)
    if tool_class:
        return tool_class()
    return None


def get_all_tools() -> list[dict]:
    """Get all tools formatted for AI consumption."""
    tools = []
    for name, tool_class in TOOL_REGISTRY.items():
        tool_instance = tool_class()
        tools.append(tool_instance.get_schema())
    return tools
