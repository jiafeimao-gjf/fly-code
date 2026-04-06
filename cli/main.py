"""CLI interface for fly-code programming agent."""

import argparse
import sys
from pathlib import Path

from core.planner import Planner
from core.developer import Developer
from core.tester import Tester
from core.analyzer import Analyzer
from core.deployer import Deployer
from docs.spec_manager import SpecManager
from utils.logger import logger, LogLevel
from cli.repl import run_repl


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new fly-code project."""
    project_name = args.project_name
    project_path = Path(project_name)

    if project_path.exists() and any(project_path.iterdir()):
        logger.error(f"Directory '{project_name}' already exists and is not empty.")
        return 1

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

    (project_path / "README.md").write_text(f"""# {project_name}

TODO: Add project description.
""")

    logger.info(f"Initialized project: {project_name}")
    return 0


def cmd_spec_create(args: argparse.Namespace) -> int:
    """Create a new specification document."""
    spec_manager = SpecManager(Path.cwd())

    description = args.description or "TODO: Add description"
    objectives = [o.strip() for o in args.objectives.split(",")] if args.objectives else ["TODO: Define objectives"]
    criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else ["TODO: Define acceptance criteria"]

    content = spec_manager.create_spec(
        title=args.title,
        description=description,
        objectives=objectives,
        acceptance_criteria=criteria
    )

    logger.success(f"Created SPEC.md")
    print()
    print(content)
    return 0


def cmd_spec_update(args: argparse.Namespace) -> int:
    """Update the specification document."""
    spec_manager = SpecManager(Path.cwd())
    spec_manager.update_spec(args.task_id, args.updates)
    logger.info(f"Updated SPEC.md with: {args.task_id}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Create implementation plan from spec."""
    planner = Planner(Path.cwd())
    spec_path = Path(args.spec_file) if args.spec_file else None

    if spec_path and not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return 1

    plan = planner.create_implementation_plan(spec_path)
    print()
    print(plan)
    return 0


def cmd_develop(args: argparse.Namespace) -> int:
    """Generate code from specification."""
    developer = Developer(Path.cwd())
    spec_manager = SpecManager(Path.cwd())

    spec_path = Path(args.spec_file) if args.spec_file else spec_manager.get_spec_path()
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return 1

    analysis = Planner(Path.cwd()).analyze_spec(spec_path)
    logger.info(f"Developing based on spec: {analysis['title']}")

    # Create a basic module based on the spec
    module_content = f'''"""Generated module for {analysis['title']}."""

from typing import Any


def main() -> None:
    """Main entry point."""
    print("TODO: Implement {analysis['title']}")


if __name__ == "__main__":
    main()
'''

    module_path = developer.create_module(analysis['title'].lower().replace(" ", "_"), module_content)
    logger.success(f"Generated: {module_path}")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests."""
    tester = Tester(Path.cwd())
    test_path = Path(args.test_file) if args.test_file else None

    code, output = tester.run_tests(test_path)
    print()
    print(output)
    return code


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze code for issues."""
    analyzer = Analyzer(Path.cwd())
    target = Path(args.target) if args.target else Path.cwd()

    if target.is_file():
        issues = analyzer.analyze_file(target)
        results = [(target, issues)]
    else:
        results = analyzer.analyze_directory(target)

    analyzer.print_report(results)

    # Check documentation
    if target.is_file():
        doc_issues = analyzer.check_documentation(target)
        if doc_issues:
            print()
            logger.info("Documentation check:")
            for issue in doc_issues:
                print(f"  [{issue.severity}] {issue.message}")

    return 0


def cmd_deploy(args: argparse.Namespace) -> int:
    """Deploy to target environment."""
    deployer = Deployer(Path.cwd())

    # Register a local target by default
    deployer.register_target("local", "local", {
        "run_script": args.run_script
    })

    if args.target and args.target != "local":
        deployer.register_target(args.target, args.target_type or "local", {
            "run_script": args.run_script
        })

    success, message = deployer.deploy(args.target or "local")
    if success:
        logger.info(f"Deployment successful: {message}")
        return 0
    else:
        logger.error(f"Deployment failed: {message}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Check deployment status."""
    deployer = Deployer(Path.cwd())
    deployer.register_target("local", "local", {})
    print()
    print(deployer.get_status("local"))
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="fly-code",
        description="Documentation-driven programming agent CLI"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands (use 'fly-code interactive' or 'fly-code i' for REPL mode)")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("project_name", help="Name of the project to create")
    init_parser.set_defaults(func=cmd_init)

    # spec commands
    spec_parser = subparsers.add_parser("spec", help="Specification management")
    spec_subparsers = spec_parser.add_subparsers(dest="spec_command")

    spec_create = spec_subparsers.add_parser("create", help="Create a new specification")
    spec_create.add_argument("title", help="Specification title")
    spec_create.add_argument("-d", "--description", help="Project description")
    spec_create.add_argument("-o", "--objectives", help="Comma-separated objectives")
    spec_create.add_argument("-c", "--criteria", help="Comma-separated acceptance criteria")
    spec_create.set_defaults(func=cmd_spec_create)

    spec_update = spec_subparsers.add_parser("update", help="Update specification")
    spec_update.add_argument("task_id", help="Task identifier")
    spec_update.add_argument("updates", help="Update content")
    spec_update.set_defaults(func=cmd_spec_update)

    # plan command
    plan_parser = subparsers.add_parser("plan", help="Create implementation plan from spec")
    plan_parser.add_argument("spec_file", nargs="?", help="Path to spec file")
    plan_parser.set_defaults(func=cmd_plan)

    # develop command
    develop_parser = subparsers.add_parser("develop", help="Generate code from specification")
    develop_parser.add_argument("spec_file", nargs="?", help="Path to spec file")
    develop_parser.set_defaults(func=cmd_develop)

    # test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("test_file", nargs="?", help="Specific test file to run")
    test_parser.set_defaults(func=cmd_test)

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code for issues")
    analyze_parser.add_argument("target", nargs="?", help="File or directory to analyze")
    analyze_parser.set_defaults(func=cmd_analyze)

    # deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to target")
    deploy_parser.add_argument("target", nargs="?", default="local", help="Deployment target")
    deploy_parser.add_argument("-t", "--target-type", help="Target type (local, docker)")
    deploy_parser.add_argument("-r", "--run-script", help="Script to run for deployment")
    deploy_parser.set_defaults(func=cmd_deploy)

    # status command
    status_parser = subparsers.add_parser("status", help="Check deployment status")
    status_parser.set_defaults(func=cmd_status)

    # interactive command
    interact_parser = subparsers.add_parser("interactive", aliases=["i"], help="Start interactive REPL mode")
    interact_parser.set_defaults(func=lambda _: run_repl())

    # shell command (alias for interactive)
    shell_parser = subparsers.add_parser("shell", aliases=["sh"], help="Start interactive REPL mode")
    shell_parser.set_defaults(func=lambda _: run_repl())

    args = parser.parse_args()

    if args.verbose:
        logger.level = LogLevel.DEBUG

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
