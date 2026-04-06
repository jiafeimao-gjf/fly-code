"""Interactive REPL for fly-code programming agent."""

import sys
import os
import shlex
import json
import readline
from typing import Optional
from pathlib import Path

from core.agent import Agent, AgentConfig
from core.planner import Planner
from core.developer import Developer
from core.tester import Tester
from core.analyzer import Analyzer
from core.deployer import Deployer
from docs.spec_manager import SpecManager
from docs.reader import DocReader
from core.tools import get_all_tools
from core.models import get_model
from utils.logger import logger, Colors, USE_COLOR, LogLevel


# Slash commands registry
SLASH_COMMANDS: dict[str, str] = {
    # Project commands
    "init": "Initialize a new project: /init <project_name>",
    "spec": "Specification: /spec create <title> [-d desc] [-o obj1,obj2] [-c crit1,crit2]",
    "plan": "Plan from spec: /plan [spec_file]",
    "develop": "Develop from spec: /develop [spec_file]",
    "test": "Run tests: /test [test_file]",
    "analyze": "Analyze code: /analyze [target]",
    "deploy": "Deploy: /deploy [target] [-r script]",
    "status": "Check status: /status",

    # Agent commands (tools + AI)
    "agent": "Start agent mode: /agent",
    "code": "Generate code with AI: /code <description>",
    "fix": "Fix bug with AI: /fix <bug_description>",
    "explain": "Explain with AI: /explain <code_or_question>",
    "review": "AI code review: /review [file]",

    # Debug commands
    "debug": "Toggle debug mode (more verbose logging): /debug",
    "verbose": "Toggle verbose output: /verbose",
    "stream": "Toggle streaming output: /stream",

    # AI model commands
    "model": "Switch AI model: /model <model_name>",
    "models": "List available models: /models",
    "tools": "List available tools: /tools",

    # Git commands
    "git": "Git operations: /git <status|log|add|commit|branch|checkout|push|pull>",
    "git status": "Show git status: /git status",
    "git log": "Show recent commits: /git log",
    "git add": "Stage files: /git add [files...]",
    "git commit": "Commit changes: /git commit <message>",
    "git checkout": "Switch branch: /git checkout <branch>",
    "git push": "Push to remote: /git push [remote]",
    "git pull": "Pull from remote: /git pull [remote]",

    # Doc commands
    "doc": "Document: /doc <topic>",
    "help": "Show this help: /help",
    "exit": "Exit REPL: /exit",
    "quit": "Quit REPL: /quit",
}


class REPL:
    """Interactive REPL for fly-code."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.running = True

        # Initialize components
        self.agent = Agent(self.project_root)
        self.planner = Planner(self.project_root)
        self.developer = Developer(self.project_root)
        self.tester = Tester(self.project_root)
        self.analyzer = Analyzer(self.project_root)
        self.deployer = Deployer(self.project_root)
        self.spec_manager = SpecManager(self.project_root)
        self.doc_reader = DocReader()

        # REPL state
        self.verbose = False
        self.stream = False  # Streaming response toggle

        # Command history
        self._history_file = Path.home() / ".fly-code" / "history"
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Setup readline for command history and completion."""
        # Ensure history directory exists
        self._history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        if self._history_file.exists():
            try:
                readline.read_history_file(str(self._history_file))
            except Exception:
                pass

        # Set history file
        readline.set_history_length(1000)

    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            readline.write_history_file(str(self._history_file))
        except Exception:
            pass

    def print_banner(self) -> None:
        """Print welcome banner."""
        if USE_COLOR:
            print(f"\n{Colors.CYAN}{Colors.BOLD}")
            print("╔" + "═" * 58 + "╗")
            print("║" + " " * 10 + "fly-code - Documentation-driven Agent" + " " * 9 + "║")
            print("╚" + "═" * 58 + "╝")
            print(f"{Colors.RESET}")
            logger.info(f"AI Model: {self.agent.config.model_name}")
            logger.info(f"Project: {self.project_root}")
            print()
            print("  Type /help for commands")
            print("  Default mode: Agent (AI will use tools to help you)")
        else:
            print("=" * 60)
            print("  fly-code - Documentation-driven Programming Agent")
            print("=" * 60)
            logger.info(f"AI Model: {self.agent.config.model_name}")
            logger.info(f"Project: {self.project_root}")
            print()
            logger.info("Type /help for available commands")
            logger.info("Default mode: Agent (AI will use tools)")
            print("=" * 60)

    def print_help(self) -> None:
        """Print help message."""
        print()
        logger.info("Available slash commands:")
        print("-" * 40)
        for cmd, desc in SLASH_COMMANDS.items():
            print(f"  {cmd:12} {desc}")
        print()

    def handle_slash_command(self, line: str) -> bool:
        """Handle a slash command. Returns True if handled."""
        if not line.startswith("/"):
            return False

        parts = shlex.split(line)
        cmd = parts[0][1:]  # Remove leading /

        # Exit commands
        if cmd in ("exit", "quit"):
            self.running = False
            logger.success("Goodbye!")
            return True

        if cmd == "help":
            self.print_help()
            return True

        # Model commands
        if cmd == "model":
            if len(parts) < 2:
                # Show current model
                current = self.agent.model
                if current:
                    logger.info(f"Current model: {current.name}")
                else:
                    logger.warning("No model loaded")
                return True

            model_name = parts[1]
            success, msg = self.agent.switch_model(model_name)
            if success:
                logger.success(msg)
            else:
                logger.error(f"Error: {msg}")
            return True

        if cmd == "models":
            # List available Ollama models
            try:
                from core.models.ollama_model import OllamaModel
                ollama = OllamaModel()
                available = ollama.list_models()
                print()
                logger.info("Available Ollama models:")
                current = self.agent.model
                current_name = current.model if current else ""
                for m in available:
                    marker = " <=" if m == current_name else ""
                    print(f"  {m}{marker}")
                print()
                logger.info(f"Current: {current_name}")
                logger.info("Use /model <name> to switch")
            except Exception as e:
                logger.error(f"Error listing models: {e}")
            return True

        if cmd == "tools":
            tools = get_all_tools()
            print()
            logger.info(f"Available tools ({len(tools)}):")
            for tool in tools:
                print(f"  {tool['name']}: {tool['description'].split(chr(10))[0]}")
            return True

        # Git commands
        if cmd == "git":
            self._cmd_git(parts[1:])
            return True

        # Project commands
        if cmd == "init":
            if len(parts) < 2:
                logger.warning("Usage: /init <project_name>")
                return True
            self._cmd_init(parts[1])
            return True

        if cmd == "spec":
            self._cmd_spec(parts[1:])
            return True

        if cmd == "plan":
            spec_file = parts[1] if len(parts) > 1 else None
            self._cmd_plan(spec_file)
            return True

        if cmd == "develop":
            spec_file = parts[1] if len(parts) > 1 else None
            self._cmd_develop(spec_file)
            return True

        if cmd == "test":
            test_file = parts[1] if len(parts) > 1 else None
            self._cmd_test(test_file)
            return True

        if cmd == "analyze":
            target = parts[1] if len(parts) > 1 else None
            self._cmd_analyze(target)
            return True

        if cmd == "deploy":
            self._cmd_deploy(parts[1:])
            return True

        if cmd == "status":
            self._cmd_status()
            return True

        # Agent commands
        if cmd == "agent":
            self._cmd_agent(parts[1:])
            return True

        if cmd == "code":
            if len(parts) < 2:
                logger.warning("Usage: /code <description>")
                return True
            description = " ".join(parts[1:])
            self._cmd_code(description)
            return True

        if cmd == "fix":
            if len(parts) < 2:
                logger.warning("Usage: /fix <bug_description>")
                return True
            bug = " ".join(parts[1:])
            self._cmd_fix(bug)
            return True

        if cmd == "explain":
            if len(parts) < 2:
                logger.warning("Usage: /explain <code_or_question>")
                return True
            target = " ".join(parts[1:])
            self._cmd_explain(target)
            return True

        if cmd == "review":
            target = parts[1] if len(parts) > 1 else "."
            self._cmd_review(target)
            return True

        # Vibe mode
        if cmd == "stream":
            self.stream = not self.stream
            status = "开启" if self.stream else "关闭"
            logger.info(f"流式输出: {status}")
            return True

        if cmd == "debug":
            self.verbose = not self.verbose
            self.agent.config.max_iterations = 50 if self.verbose else 10
            logger.level = LogLevel.DEBUG if self.verbose else LogLevel.INFO
            status = "开启" if self.verbose else "关闭"
            logger.info(f"Debug 模式: {status} (max iterations: {self.agent.config.max_iterations}, debug日志: {'开启' if self.verbose else '关闭'})")
            return True

        if cmd == "verbose":
            self.verbose = not self.verbose
            logger.level = LogLevel.DEBUG if self.verbose else LogLevel.INFO
            status = "开启" if self.verbose else "关闭"
            logger.info(f"Verbose 模式: {status} (debug日志: {'开启' if self.verbose else '关闭'})")
            return True

        logger.warning(f"Unknown command: /{cmd}. Type /help for available commands.")
        return True

    # ========== Project Command Handlers ==========

    def _cmd_init(self, project_name: str) -> None:
        """Handle /init command."""
        project_path = Path(project_name)
        if project_path.exists() and any(project_path.iterdir()):
            logger.error(f"Directory '{project_name}' already exists and is not empty.")
            return

        project_path.mkdir(exist_ok=True)
        (project_path / "SPEC.md").write_text("""# Project Specification

## Description
TODO: Describe the project.

## Objectives
- TODO: Define objectives

## Acceptance Criteria
- [ ] TODO: Define acceptance criteria

## Implementation Plan
1. TODO: Define implementation steps
""")
        (project_path / "README.md").write_text(f"# {project_name}\n\nTODO: Add description.\n")
        logger.success(f"Initialized project: {project_name}")

    def _cmd_spec(self, args: list[str]) -> None:
        """Handle /spec command."""
        if not args or args[0] == "create":
            logger.warning("Usage: /spec create <title> [-d description] [-o obj1,obj2] [-c crit1,crit2]")
            return

        subcmd = args[0]
        if subcmd == "create":
            title = args[1] if len(args) > 1 else "New Feature"
            description = ""
            objectives = []
            criteria = []

            i = 2
            while i < len(args):
                if args[i] == "-d" and i + 1 < len(args):
                    description = args[i + 1]
                    i += 2
                elif args[i] == "-o" and i + 1 < len(args):
                    objectives = [o.strip() for o in args[i + 1].split(",")]
                    i += 2
                elif args[i] == "-c" and i + 1 < len(args):
                    criteria = [c.strip() for c in args[i + 1].split(",")]
                    i += 2
                else:
                    i += 1

            content = self.spec_manager.create_spec(title, description, objectives, criteria)
            logger.success(f"Created SPEC.md:\n{content}")

    def _cmd_plan(self, spec_file: Optional[str]) -> None:
        """Handle /plan command."""
        spec_path = Path(spec_file) if spec_file else self.spec_manager.get_spec_path()
        if not spec_path.exists():
            logger.error(f"Spec file not found: {spec_path}")
            return

        plan = self.planner.create_implementation_plan(spec_path)
        print()
        print(plan)

    def _cmd_develop(self, spec_file: Optional[str]) -> None:
        """Handle /develop command."""
        spec_path = Path(spec_file) if spec_file else self.spec_manager.get_spec_path()
        if not spec_path.exists():
            logger.error(f"Spec file not found: {spec_path}")
            return

        analysis = self.planner.analyze_spec(spec_path)
        module_content = f'''"""Generated module for {analysis['title']}."""

from typing import Any


def main() -> None:
    """Main entry point."""
    print("TODO: Implement {analysis['title']}")


if __name__ == "__main__":
    main()
'''
        module_path = self.developer.create_module(
            analysis['title'].lower().replace(" ", "_"),
            module_content
        )
        logger.success(f"Generated: {module_path}")

    def _cmd_test(self, test_file: Optional[str]) -> None:
        """Handle /test command."""
        test_path = Path(test_file) if test_file else None
        code, output = self.tester.run_tests(test_path)
        print(output)

    def _cmd_analyze(self, target: Optional[str]) -> None:
        """Handle /analyze command."""
        target_path = Path(target) if target else Path.cwd()
        if target_path.is_file():
            issues = self.analyzer.analyze_file(target_path)
            results = [(target_path, issues)]
        else:
            results = self.analyzer.analyze_directory(target_path)

        self.analyzer.print_report(results)

    def _cmd_deploy(self, args: list[str]) -> None:
        """Handle /deploy command."""
        target_name = "local"
        run_script = None

        i = 0
        while i < len(args):
            if not args[i].startswith("-"):
                target_name = args[i]
            elif args[i] == "-r" and i + 1 < len(args):
                run_script = args[i + 1]
                i += 1
            i += 1

        self.deployer.register_target(target_name, "local", {"run_script": run_script})
        success, message = self.deployer.deploy(target_name)
        if success:
            logger.success(message)
        else:
            logger.error(f"Error: {message}")

    def _cmd_status(self) -> None:
        """Handle /status command."""
        self.deployer.register_target("local", "local", {})
        print()
        print(self.deployer.get_status("local"))

    # ========== Agent Command Handlers ==========

    def _cmd_agent(self, args: list[str]) -> None:
        """Handle /agent command - interactive agent mode."""
        logger.section("AGENT MODE - AI will use tools to help you")
        print()
        print("Type your request and AI will:")
        print("  - Read/write files")
        print("  - Execute commands")
        print("  - Search code")
        print("  - Analyze and fix issues")
        print()
        print("Commands available in agent mode:")
        print("  /done              - Exit agent mode")
        print("  /model <name>      - Switch AI model")
        print("  /models            - List available models")
        print("  /debug             - Toggle debug mode")
        print("  /verbose           - Toggle verbose output")
        print()

        while True:
            try:
                line = input("\nagent> ").strip()
                if not line:
                    continue

                if line == "/done":
                    logger.info("Exiting agent mode.")
                    break

                if line.startswith("/"):
                    # Parse agent-mode slash commands
                    parts = shlex.split(line)
                    cmd = parts[0][1:] if parts else ""

                    if cmd == "done":
                        logger.info("Exiting agent mode.")
                        break
                    elif cmd == "model":
                        self._handle_agent_model(parts[1:])
                    elif cmd == "models":
                        self._handle_agent_models()
                    elif cmd == "debug":
                        self.verbose = not self.verbose
                        self.agent.config.max_iterations = 50 if self.verbose else 10
                        logger.level = LogLevel.DEBUG if self.verbose else LogLevel.INFO
                        status = "开启" if self.verbose else "关闭"
                        logger.info(f"Debug 模式: {status} (max iterations: {self.agent.config.max_iterations}, debug日志: {'开启' if self.verbose else '关闭'})")
                    elif cmd == "verbose":
                        self.verbose = not self.verbose
                        logger.level = LogLevel.DEBUG if self.verbose else LogLevel.INFO
                        status = "开启" if self.verbose else "关闭"
                        logger.info(f"Verbose 模式: {status} (debug日志: {'开启' if self.verbose else '关闭'})")
                    else:
                        logger.warning(f"Unknown command: /{cmd}. Use /done to exit.")
                    continue

                # Run agent
                print()
                response = self.agent.run(line, verbose=self.verbose)
                if response:
                    print(f"\n{response}\n")

            except KeyboardInterrupt:
                print("\nUse /done to exit.")
            except EOFError:
                break

    def _handle_agent_model(self, args: list[str]) -> None:
        """Handle /model command in agent mode."""
        if not args:
            current = self.agent.model
            if current:
                logger.info(f"Current model: {current.name}")
            else:
                logger.warning("No model loaded")
            return

        model_name = args[0]
        success, msg = self.agent.switch_model(model_name)
        if success:
            logger.success(msg)
        else:
            logger.error(f"Error: {msg}")

    def _handle_agent_models(self) -> None:
        """Handle /models command in agent mode."""
        try:
            from core.models.ollama_model import OllamaModel
            ollama = OllamaModel()
            available = ollama.list_models()
            print()
            logger.info("Available Ollama models:")
            current = self.agent.model
            current_name = current.model if current else ""
            for m in available:
                marker = " <=" if m == current_name else ""
                print(f"  {m}{marker}")
            print()
            logger.info(f"Current: {current_name}")
        except Exception as e:
            logger.error(f"Error listing models: {e}")

    def _cmd_code(self, description: str) -> None:
        """Handle /code command - generate code with AI."""
        print()
        logger.info(f"Generating code for: {description}")

        prompt = f"""Generate Python code based on this request:

{description}

Project root: {self.project_root}

IMPORTANT: When you need to create or modify files, use the file_operations tool:
{{"tool": "file_operations", "parameters": {{"operation": "file_write", "path": "filename.py", "content": "# code content"}}}}

Generate complete, working code. Create the actual files using tool calls.
If multiple files needed, create them all.
"""
        response = self.agent.run(prompt, stream=self.stream)
        if not self.stream:
            print(f"\n{response}\n")

    def _cmd_fix(self, bug: str) -> None:
        """Handle /fix command - fix bug with AI."""
        print()
        logger.info(f"Analyzing and fixing bug: {bug}")

        prompt = f"""Bug to fix: {bug}

The user wants to fix this bug. Analyze the code and:
1. Identify the likely cause
2. If you can write the fix, use edit_file tool to make the change:
{{"tool": "edit_file", "parameters": {{"operation": "replace", "path": "file.py", "old_content": "buggy code", "new_content": "fixed code"}}}}

Project root: {self.project_root}
"""
        response = self.agent.run(prompt)
        print(f"\n{response}\n")

    def _cmd_explain(self, target: str) -> None:
        """Handle /explain command - explain code with AI."""
        target_path = Path(target)
        if target_path.exists() and target_path.is_file():
            content = target_path.read_text()
            prompt = f"""Explain this code:

```python
{content}
```

File: {target_path}
"""
        else:
            prompt = f"Explain this concept or code: {target}"

        response = self.agent.chat(prompt)
        print()
        print(response)
        print()

    def _cmd_review(self, target: str) -> None:
        """Handle /review command - AI code review."""
        target_path = Path(target)
        if target_path.is_dir():
            target_path = self.project_root

        results = self.analyzer.analyze_directory(target_path)

        review_text = "Please review this code for issues:\n"
        for file_path, issues in results:
            review_text += f"\n{file_path}:\n"
            for issue in issues:
                review_text += f"  - [{issue.severity}] {issue.message}\n"

        response = self.agent.chat(review_text)
        print()
        logger.info("AI Review:")
        print(response)
        print()

    # ========== Git Commands ==========

    def _cmd_git(self, args: list[str]) -> None:
        """Handle /git command."""
        from core.tools.git_tool import GitTool

        if not args:
            logger.warning("Usage: /git <status|log|add|commit|branch|checkout|push|pull>")
            return

        subcmd = args[0]
        git_tool = GitTool(str(self.project_root))

        if subcmd == "status":
            result = git_tool.execute("status")
        elif subcmd == "log":
            result = git_tool.execute("log")
        elif subcmd == "add":
            files = args[1:] if len(args) > 1 else None
            result = git_tool.execute("add", files=files)
        elif subcmd == "commit":
            if len(args) < 2:
                logger.warning("Usage: /git commit <message>")
                return
            result = git_tool.execute("commit", message=" ".join(args[1:]))
        elif subcmd == "branch":
            branch = args[1] if len(args) > 1 else None
            result = git_tool.execute("branch", branch=branch)
        elif subcmd == "checkout":
            if len(args) < 2:
                logger.warning("Usage: /git checkout <branch>")
                return
            result = git_tool.execute("checkout", branch=args[1])
        elif subcmd == "push":
            remote = args[1] if len(args) > 1 else "origin"
            result = git_tool.execute("push", remote=remote)
        elif subcmd == "pull":
            remote = args[1] if len(args) > 1 else "origin"
            result = git_tool.execute("pull", remote=remote)
        else:
            logger.error(f"Unknown git command: {subcmd}")
            logger.info("Usage: /git <status|log|add|commit|branch|checkout|push|pull>")
            return

        if result.success:
            print()
            print(result.content)
            print()
        else:
            logger.error(f"Error: {result.error}")

    def run(self) -> None:
        """Run the REPL in Agent mode by default."""
        self.print_banner()
        print("  Just describe what you want and AI will create it!")
        print()

        while self.running:
            try:
                line = input("\nagent> ").strip()
                if not line:
                    continue

                # Add to readline history
                readline.add_history(line)

                # Handle slash commands
                if line.startswith("/"):
                    self.handle_slash_command(line)
                    continue

                # Free-form input - use agent with tools
                print()
                response = self.agent.run(line, verbose=self.verbose, stream=self.stream)
                if response:
                    print(f"\n{response}\n")

            except KeyboardInterrupt:
                logger.info("Use /exit to quit.")
            except EOFError:
                break

        self._save_history()
        logger.success("Goodbye!")


def run_repl() -> int:
    """Start the interactive REPL."""
    repl = REPL()
    repl.run()
    return 0
