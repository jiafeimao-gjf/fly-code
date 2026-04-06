"""Agent that orchestrates tools and AI model."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

from core.tools import get_all_tools, get_tool, ToolResult
from core.models.base import AIModel, AIResponse
from core.models import get_model
from utils.logger import logger


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    model_name: str = "ollama"
    model_kwargs: dict = field(default_factory=dict)
    max_iterations: int = 10
    tool_timeout: int = 30


class Agent:
    """Agent that uses tools and AI model for coding tasks."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: AgentConfig | None = None,
    ):
        self.project_root = project_root or Path.cwd()
        self.config = config or AgentConfig()
        self.model: Optional[AIModel] = None
        self.conversation: list[Message] = []
        self.tools = get_all_tools()

        # Initialize model
        self._init_model()

    def _init_model(self) -> None:
        """Initialize the AI model based on config."""
        if self.config.model_name == "ollama":
            self.model = get_model("ollama")
        elif self.config.model_name == "minimax":
            self.model = get_model("minimax")
        else:
            # Try to get by name
            self.model = get_model(self.config.model_name)

        if self.model is None:
            logger.warning(f"Could not initialize model: {self.config.model_name}")

    def set_model(self, model_name: str) -> bool:
        """Switch to a different model provider (ollama/minimax)."""
        model = get_model(model_name)
        if model:
            self.model = model
            self.config.model_name = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        return False

    def switch_model(self, model_name: str) -> tuple[bool, str]:
        """Switch to a different Ollama model.

        For Ollama models, switches to a specific model (e.g., 'deepseek-coder-v2:16b').
        For other providers, delegates to set_model.

        Returns:
            (success, message)
        """
        if not self.model:
            return False, "No model loaded"

        # If it's an OllamaModel, try to switch
        if hasattr(self.model, 'switch_model'):
            return self.model.switch_model(model_name)

        # For other models, just return the current model info
        return True, f"Current model: {self.model.name}"

    def get_system_prompt(self) -> str:
        """Generate system prompt for the agent."""
        tools_json = json.dumps(self.tools, indent=2)
        return """You are an expert programming agent that ACTUALLY CREATES files.

CRITICAL RULES:
1. When asked to create a project/code/game, you MUST use file_operations tool to CREATE actual files
2. NEVER just describe - you MUST write the actual code using tools
3. Output ONLY JSON when using a tool: {"tool": "tool_name", "parameters": {...}}
4. After each tool result, CONTINUE immediately with the next file

WORKFLOW - Follow this EXACTLY:
1. directory_create - create the project folder
2. file_write - write each source file with REAL code (not placeholders!)
3. Continue until ALL files are created

EXAMPLE - Creating a tank game:
Step 1: {"tool": "file_operations", "parameters": {"operation": "directory_create", "path": "tank-game"}}
Step 2: {"tool": "file_operations", "parameters": {"operation": "file_write", "path": "tank-game/index.html", "content": "<!DOCTYPE html>..."}}
Step 3: {"tool": "file_operations", "parameters": {"operation": "file_write", "path": "tank-game/game.js", "content": "// Tank game code..."}}
(continue until complete)

Available tools:
""" + tools_json + """

NEVER stop until ALL files are created. If the task requires 5 files, create all 5.
If you stop early, the user will have incomplete code.
"""

    def get_project_context(self) -> str:
        """Get current project context."""
        context = []

        # Check for SPEC.md
        spec_path = self.project_root / "SPEC.md"
        if spec_path.exists():
            context.append(f"\n{'='*60}\nSPEC.md:\n{'='*60}\n")
            context.append(spec_path.read_text()[:3000])

        # List relevant files
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)][:20]
        if py_files:
            context.append(f"\n\nProject Python files ({len(py_files)}):")
            for f in py_files:
                context.append(f"  {f.relative_to(self.project_root)}")

        return "\n".join(context)

    def run(self, user_input: str, verbose: bool = True, stream: bool = False) -> str:
        """Run the agent with user input. Returns the final response.

        Args:
            user_input: The user request
            verbose: Whether to show verbose output
            stream: Whether to stream the response
        """
        if not self.model:
            return "Error: No AI model configured"

        # Build the prompt with system and context
        system = self.get_system_prompt()
        system += f"\n\nCurrent project: {self.project_root}"
        system += self.get_project_context()

        # Track iterations to prevent infinite loops
        iterations = 0
        max_iterations = self.config.max_iterations

        # Build messages for chat
        messages = [{"role": "system", "content": system}]
        messages.append({"role": "user", "content": user_input})

        last_response = ""
        tool_call_count = 0

        logger.section("Agent 开始处理")
        if verbose:
            logger.debug(f"Model: {self.model.name}")
            logger.debug(f"Max iterations: {max_iterations}")
            logger.debug(f"User input: {user_input[:100]}...")

        # Start without tools, enable tools only after we verify they work
        use_tools = True

        while iterations < max_iterations:
            iterations += 1
            logger.info(f"[{iterations}/{max_iterations}] 正在思考...")

            try:
                response = self.model.chat(messages, tools=self.tools if use_tools else None)
            except Exception as e:
                # If tools cause error, retry without tools and disable them
                if use_tools and ("400" in str(e) or "404" in str(e) or "error" in str(e).lower()):
                    logger.warning(f"工具调用出错，切换到无工具模式: {str(e)[:80]}...")
                    use_tools = False
                    try:
                        response = self.model.chat(messages, tools=None)
                    except Exception as e2:
                        return f"AI Error: {str(e2)}"
                else:
                    return f"AI Error: {str(e)}"

            last_response = response.content.strip()

            # Always show raw response for debugging when no tool call found
            logger.debug(f"Raw response: {last_response[:500]}")

            # If empty response, retry with continuation prompt
            if not last_response:
                logger.warning("模型返回空响应，发送继续提示...")
                messages.append({
                    "role": "assistant",
                    "content": "",
                })
                messages.append({
                    "role": "user",
                    "content": "You returned an empty response. Continue creating the project files using file_operations tool. Write the actual source code files now.",
                })
                continue

            # Check if response contains a tool call
            tool_call = self._extract_tool_call(last_response)
            if not tool_call:
                # No tool call, model returned text instead of JSON
                logger.warning("未检测到工具调用，模型返回了文本而非 JSON")
                if stream and hasattr(self.model, 'chat_stream'):
                    return self._stream_response(messages, system)
                logger.success("Agent 完成")
                return last_response

            # Execute tool
            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("parameters", {})
            tool_call_count += 1

            # Mask sensitive params
            display_params = self._mask_sensitive(tool_params)
            logger.info(f"[工具调用 #{tool_call_count}] {tool_name}")
            if verbose:
                logger.debug(f"参数: {display_params}")

            # Execute the tool
            tool = get_tool(tool_name)
            if not tool:
                logger.error(f"未知工具 '{tool_name}'")
                messages.append({
                    "role": "assistant",
                    "content": last_response,
                })
                messages.append({
                    "role": "tool",
                    "content": f"Error: Unknown tool '{tool_name}'",
                    "name": tool_name,
                })
                continue

            result = tool.execute(**tool_params)

            # Add tool result as a simple text message (Ollama doesn't support proper tool calling format)
            messages.append({
                "role": "assistant",
                "content": last_response,
            })
            messages.append({
                "role": "tool",
                "content": str(result.to_dict()),
                "name": tool_name,
            })
            # Remind the model to continue with next step
            if result.success:
                continuation_prompt = "\n\nContinue creating the project files. Use file_operations to write the actual source code files."
            else:
                continuation_prompt = f"\n\nError: {result.error}. Fix the issue and continue."
            messages.append({
                "role": "user",
                "content": continuation_prompt,
            })

            # Show result
            if result.success:
                content_preview = result.content[:200].replace('\n', ' ')
                if len(result.content) > 200:
                    content_preview += "..."
                logger.success(f"结果: {content_preview}")
                if verbose:
                    logger.debug(f"Full result: {result.content}")
            else:
                logger.error(f"错误: {result.error or result.content}")

        logger.warning(f"达到最大迭代次数 ({max_iterations})")
        return f"Max iterations ({max_iterations}) reached. Last response:\n{last_response}"

    def _stream_response(self, messages: list[dict], system: str) -> str:
        """Stream the response to stdout and return complete response."""
        from utils.logger import Colors, USE_COLOR

        logger.success("Agent 完成\n")

        full_response = []
        try:
            for chunk in self.model.chat_stream(messages, system=system):
                full_response.append(chunk)
                if USE_COLOR:
                    print(f"{Colors.GREEN}{chunk}{Colors.RESET}", end="", flush=True)
                else:
                    print(chunk, end="", flush=True)
            print()  # Newline after streaming
        except Exception as e:
            return f"Streaming error: {str(e)}\n" + "".join(full_response)

        return "".join(full_response)

    def _mask_sensitive(self, params: dict) -> dict:
        """Mask sensitive parameters like passwords or keys."""
        sensitive_keys = {"password", "api_key", "token", "secret", "key"}
        masked = {}
        for k, v in params.items():
            if k.lower() in sensitive_keys:
                masked[k] = "***"
            elif isinstance(v, str) and len(v) > 100:
                masked[k] = v[:50] + "..."
            else:
                masked[k] = v
        return masked

    def _extract_tool_call(self, text: str) -> dict | None:
        """Extract tool call from response text."""
        # Try to find JSON in the response
        # Look for ```json blocks first
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                if "tool" in result and "parameters" in result:
                    return result
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object with tool and parameters
        json_pattern = r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{.*\}\s*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if "tool" in result and "parameters" in result:
                    return result
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object with "tool" key
        try:
            # Look for {"tool": ... pattern anywhere in text
            simple_pattern = r'"\s*tool\s*"\s*:\s*"([^"]+)"'
            match = re.search(simple_pattern, text)
            if match:
                tool_name = match.group(1)
                # Try to extract parameters
                param_pattern = r'"parameters"\s*:\s*(\{[^}]*\})'
                param_match = re.search(param_pattern, text, re.DOTALL)
                if param_match:
                    try:
                        params = json.loads(param_match.group(1))
                        return {"tool": tool_name, "parameters": params}
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

        return None

    def reset(self) -> None:
        """Reset conversation history."""
        self.conversation = []

    def chat(self, message: str, verbose: bool = False) -> str:
        """Simple chat interface without tool use."""
        if not self.model:
            return "Error: No AI model configured"

        system = self.get_system_prompt()
        system += f"\n\nCurrent project: {self.project_root}"
        system += self.get_project_context()

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ]

        try:
            response = self.model.chat(messages)
            return response.content
        except Exception as e:
            return f"AI Error: {str(e)}"
