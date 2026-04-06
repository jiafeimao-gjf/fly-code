"""Tests for fly-code core modules."""

import pytest
from pathlib import Path
import tempfile
import shutil

from core.planner import Planner
from core.developer import Developer
from core.tester import Tester
from core.analyzer import Analyzer
from core.deployer import Deployer
from docs.spec_manager import SpecManager
from docs.reader import DocReader


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestSpecManager:
    def test_create_spec(self, temp_project):
        sm = SpecManager(temp_project)
        content = sm.create_spec(
            title="Test Feature",
            description="Test description",
            objectives=["Objective 1", "Objective 2"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        )

        assert "Test Feature" in content
        assert "Test description" in content
        assert "Objective 1" in content
        assert "[ ] Criteria 1" in content

    def test_read_write_spec(self, temp_project):
        sm = SpecManager(temp_project)
        sm.write_spec("# Test\n\nContent")
        assert sm.read_spec() == "# Test\n\nContent"

    def test_spec_exists(self, temp_project):
        sm = SpecManager(temp_project)
        assert not sm.spec_exists()
        sm.write_spec("# Test")
        assert sm.spec_exists()


class TestDocReader:
    def test_parse_spec(self):
        content = """# Title

## Description
Test description

## Objectives
- Obj 1
- Obj 2
"""
        parsed = DocReader.parse_spec(content)

        assert parsed["Description"] == "Test description"
        assert "Obj 1" in parsed["Objectives"]

    def test_extract_checkboxes(self):
        content = "- [x] Done\n- [ ] Not done"
        checkboxes = DocReader.extract_checkboxes(content)

        assert len(checkboxes) == 2
        assert checkboxes[0] == ("Done", True)
        assert checkboxes[1] == ("Not done", False)


class TestPlanner:
    def test_create_implementation_plan(self, temp_project):
        planner = Planner(temp_project)
        sm = SpecManager(temp_project)

        sm.create_spec("Test Feature", "Description", ["Obj 1"], ["Criteria 1"])

        plan = planner.create_implementation_plan()
        assert "Implementation Plan" in plan or "Phase" in plan


class TestDeveloper:
    def test_create_module(self, temp_project):
        dev = Developer(temp_project)
        path = dev.create_module("test_module", '"""Test module."""\n')

        assert path.exists()
        assert "test_module.py" in str(path)

    def test_create_package(self, temp_project):
        dev = Developer(temp_project)
        path = dev.create_package("testpkg", {
            "module1": '"""Module 1."""\n',
            "module2": '"""Module 2."""\n'
        })

        assert path.exists()
        assert (path / "module1.py").exists()
        assert (path / "module2.py").exists()


class TestAnalyzer:
    def test_analyze_file(self, temp_project):
        analyzer = Analyzer(temp_project)

        test_file = temp_project / "test.py"
        test_file.write_text('"""Test file."""\n\ndef foo():\n    pass\n')

        issues = analyzer.analyze_file(test_file)
        assert all(issue.severity in ("error", "warning", "info") for issue in issues)

    def test_check_documentation(self, temp_project):
        analyzer = Analyzer(temp_project)

        test_file = temp_project / "test.py"
        test_file.write_text('"""Module docstring."""\n\ndef func():\n    """Function docstring."""\n    pass\n')

        issues = analyzer.check_documentation(test_file)
        assert len(issues) == 0


class TestDeployer:
    def test_register_target(self, temp_project):
        deployer = Deployer(temp_project)
        deployer.register_target("test", "local", {"run_script": "echo test"})

        assert "test" in deployer.targets
        assert deployer.targets["test"].type == "local"
