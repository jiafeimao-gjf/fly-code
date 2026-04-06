"""Document parsing and validation utilities."""

import re
from pathlib import Path


class DocReader:
    """Reads and parses specification documents."""

    @staticmethod
    def parse_spec(content: str) -> dict:
        """Parse SPEC.md content into structured data."""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            header_match = re.match(r'^## (.+)$', line)
            if header_match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = header_match.group(1)
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    @staticmethod
    def extract_checkboxes(spec: str) -> list[tuple[str, bool]]:
        """Extract checkbox items from spec with completion status."""
        pattern = r'- \[([ x])\] (.+)'
        matches = re.findall(pattern, spec)
        return [(text, checked == 'x') for checked, text in matches]

    @staticmethod
    def extract_code_blocks(spec: str) -> list[str]:
        """Extract code blocks from specification."""
        pattern = r'```(?:\w+)?\n(.*?)```'
        return re.findall(pattern, spec, re.DOTALL)

    @staticmethod
    def validate_spec(spec_path: Path) -> tuple[bool, list[str]]:
        """Validate that a spec file has required sections."""
        if not spec_path.exists():
            return False, ["SPEC.md does not exist"]

        content = spec_path.read_text()
        required_sections = ["Description", "Objectives", "Acceptance Criteria"]
        parsed = DocReader.parse_spec(content)

        errors = []
        for section in required_sections:
            if section not in parsed:
                errors.append(f"Missing required section: {section}")

        return len(errors) == 0, errors
