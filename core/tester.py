"""Test generation and execution module."""

import subprocess
import sys
from pathlib import Path
from typing import Optional
from utils.logger import logger


class Tester:
    """Handles test generation and execution."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()

    def run_tests(self, test_path: Optional[Path] = None, verbose: bool = True) -> tuple[int, str]:
        """Run pytest on specified path or all tests."""
        if test_path is None:
            test_path = self.project_root / "tests"

        if not test_path.exists():
            return -1, f"Test path does not exist: {test_path}"

        cmd = [sys.executable, "-m", "pytest", str(test_path)]
        if verbose:
            cmd.append("-v")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def generate_test(self, module_path: Path, test_name: str, test_cases: list[str]) -> str:
        """Generate pytest test content for a module."""
        module_name = module_path.stem

        test_lines = [
            '"""Auto-generated tests."""',
            f'from {module_name} import *',
            '',
            f'def test_{test_name}():',
        ]

        for i, case in enumerate(test_cases, 1):
            test_lines.append(f'    # Test case {i}: {case}')
            test_lines.append(f'    pass')

        return '\n'.join(test_lines)

    def generate_test_for_function(self, func_name: str, func_signature: str, return_type: str) -> str:
        """Generate a test template for a function."""
        return f'''def test_{func_name}():
    """Test {func_name}."""
    # TODO: Implement test cases based on spec
    result = {func_name}({", ".join([""] for _ in func_signature.split(",") )})
    assert result is not None
'''

    def check_coverage(self, module_path: Path) -> tuple[bool, str]:
        """Check if module has associated tests."""
        test_path = self.project_root / "tests" / f"test_{module_path.stem}.py"
        if test_path.exists():
            return True, f"Tests found: {test_path}"
        return False, f"No tests found for {module_path.stem}"
