"""Solution planning and design module."""

from pathlib import Path
from docs.spec_manager import SpecManager
from docs.reader import DocReader


class Planner:
    """Plans and designs solutions based on specifications."""

    def __init__(self, project_root: Path | None = None):
        self.spec_manager = SpecManager(project_root)
        self.doc_reader = DocReader()

    def analyze_spec(self, spec_path: Path | None = None) -> dict:
        """Analyze a specification and extract key information."""
        if spec_path is None:
            spec_path = self.spec_manager.get_spec_path()

        content = spec_path.read_text()
        parsed = self.doc_reader.parse_spec(content)

        return {
            "title": self._extract_title(content),
            "objectives": self._parse_objectives(parsed.get("Objectives", "")),
            "acceptance_criteria": self._parse_criteria(parsed.get("Acceptance Criteria", "")),
            "implementation_plan": parsed.get("Implementation Plan", ""),
        }

    def _extract_title(self, content: str) -> str:
        """Extract title from spec (first # heading)."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled"

    def _parse_objectives(self, objectives_text: str) -> list[str]:
        """Parse objectives list."""
        return [line.strip('- ').strip() for line in objectives_text.split('\n') if line.strip().startswith('-')]

    def _parse_criteria(self, criteria_text: str) -> list[str]:
        """Parse acceptance criteria list."""
        return [line.strip().strip('-[] ') for line in criteria_text.split('\n') if line.strip().startswith('- [')]

    def create_implementation_plan(self, spec_path: Path | None = None) -> str:
        """Create a detailed implementation plan from spec."""
        analysis = self.analyze_spec(spec_path)

        plan_lines = [
            f"# Implementation Plan: {analysis['title']}",
            "",
            "## Phase 1: Setup and Structure",
            "- Set up project structure",
            "- Create necessary directories and base files",
            "",
            "## Phase 2: Core Implementation",
        ]

        for i, obj in enumerate(analysis['objectives'], 1):
            plan_lines.append(f"- Objective {i}: {obj}")

        plan_lines.extend([
            "",
            "## Phase 3: Testing",
            "- Write unit tests for core functionality",
            "- Verify acceptance criteria",
            "",
            "## Phase 4: Integration and Deployment",
            "- Integrate components",
            "- Final verification against spec",
            "- Deploy if all criteria met",
        ])

        return '\n'.join(plan_lines)

    def generate_solution_design(self, requirements: str) -> str:
        """Generate a solution design document from requirements."""
        design = f"""# Solution Design

## Requirements Analysis
{requirements}

## Architecture Overview
- Module structure
- Data flow
- Key components

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| TBD | TBD |

## Risk Assessment
| Risk | Mitigation |
|------|------------|
| TBD | TBD |
"""
        return design
