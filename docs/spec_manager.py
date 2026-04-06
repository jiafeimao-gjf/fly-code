"""Specification document management for documentation-driven development."""

from pathlib import Path


class SpecManager:
    """Manages SPEC.md documents for tasks and features."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def get_spec_path(self) -> Path:
        """Get path to SPEC.md file."""
        return self.project_root / "SPEC.md"

    def read_spec(self) -> str | None:
        """Read current SPEC.md content."""
        spec_path = self.get_spec_path()
        if spec_path.exists():
            return spec_path.read_text()
        return None

    def write_spec(self, content: str) -> None:
        """Write content to SPEC.md."""
        spec_path = self.get_spec_path()
        spec_path.write_text(content)

    def spec_exists(self) -> bool:
        """Check if SPEC.md exists."""
        return self.get_spec_path().exists()

    def create_spec(self, title: str, description: str, objectives: list[str], acceptance_criteria: list[str]) -> str:
        """Create a new SPEC.md document."""
        content = f"""# {title}

## Description
{description}

## Objectives
{chr(10).join(f"- {obj}" for obj in objectives)}

## Acceptance Criteria
{chr(10).join(f"- [ ] {criteria}" for criteria in acceptance_criteria)}

## Implementation Plan
1. TODO: Define implementation steps
"""
        self.write_spec(content)
        return content

    def update_spec(self, task_id: str, updates: str) -> None:
        """Update a specific section of SPEC.md."""
        spec = self.read_spec()
        if spec is None:
            raise ValueError("SPEC.md does not exist")

        # Simple append-based update for now
        spec += f"\n\n## Update: {task_id}\n{updates}"
        self.write_spec(spec)
