"""The traceability check reads requirements, specification sections and tests, and fails on each gap."""

from pathlib import Path

import pytest

from ai_app_platform.traceability import main, requirement_ids, trace

REQUIREMENTS = """# Requirements

### FR-INSP-01: Record an inspection

| ID | Requirement | Status |
|----|-------------|--------|
| NFR-SEC-01 | Every request is authenticated | Validated |
| FR-ASN-05a | Assertions are validated | Validated |
"""


def _repository(root: Path, *, spec: str, python_test: str, web_test: str) -> Path:
    (root / "specs").mkdir()
    (root / "specs/02-requirements.md").write_text(REQUIREMENTS)
    (root / "specs/20-api.md").write_text(spec)
    (root / "apps/api/tests").mkdir(parents=True)
    (root / "apps/api/tests/test_inspections.py").write_text(python_test)
    (root / "apps/web/src").mkdir(parents=True)
    (root / "apps/web/src/page.test.tsx").write_text(web_test)
    return root


GOOD_SPEC = "# API\n\n## Inspections\n\n**Requirements:** FR-INSP-01, NFR-SEC-01\n"
GOOD_PYTHON = '''
def test_records_an_inspection():
    """Verifies FR-INSP-01 and NFR-SEC-01. Records it."""


def test_helper():
    """Verifies no requirement."""


class TestValidation:
    async def test_validates(self):
        """Verifies FR-ASN-05a."""
'''
GOOD_WEB = 'it("FR-INSP-01: shows the inspection", () => {});\ntest("No requirement: renders", () => {});\n'


def test_requirement_ids_come_from_headings_and_table_rows() -> None:
    assert requirement_ids(REQUIREMENTS) == ["FR-ASN-05a", "FR-INSP-01", "NFR-SEC-01"]


def test_a_complete_repository_has_no_problems(tmp_path: Path) -> None:
    root = _repository(tmp_path, spec=GOOD_SPEC, python_test=GOOD_PYTHON, web_test=GOOD_WEB)
    result = trace(
        root, "specs/02-requirements.md", "specs", ["apps/api/tests/**/test_*.py", "apps/web/src/**/*.test.tsx"]
    )
    assert result.problems == []
    assert result.sections["FR-INSP-01"] == ["specs/20-api.md#inspections"]
    assert sorted(result.tests["FR-INSP-01"]) == [
        "apps/api/tests/test_inspections.py::test_records_an_inspection",
        "apps/web/src/page.test.tsx::FR-INSP-01: shows the inspection",
    ]
    assert result.tests["FR-ASN-05a"] == ["apps/api/tests/test_inspections.py::test_validates"]


def test_each_gap_is_a_problem(tmp_path: Path) -> None:
    root = _repository(
        tmp_path,
        spec="## Inspections\n\n**Requirements:** FR-INSP-09\n",
        python_test='def test_unnamed():\n    """Records it."""\n',
        web_test='it("shows it", () => {});\n',
    )
    problems = trace(
        root, "specs/02-requirements.md", "specs", ["apps/api/tests/**/test_*.py", "apps/web/src/**/*.test.tsx"]
    ).problems
    assert problems == [
        "specs/20-api.md#inspections: FR-INSP-09 is not a requirement",
        "apps/api/tests/test_inspections.py::test_unnamed: the test names no requirement it verifies",
        "apps/web/src/page.test.tsx::shows it: the test names no requirement it verifies",
    ]


def test_the_check_fails_until_the_report_is_written(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _repository(tmp_path, spec=GOOD_SPEC, python_test=GOOD_PYTHON, web_test=GOOD_WEB)
    arguments = ["--root", str(root), "--tests", "apps/api/tests/**/test_*.py", "apps/web/src/**/*.test.tsx"]
    assert main(arguments) == 1
    assert "docs/requirements-trace.md is not current" in capsys.readouterr().err
    assert main([*arguments, "--write"]) == 0
    assert main(arguments) == 0
    report = (root / "docs/requirements-trace.md").read_text()
    assert "| FR-INSP-01 | [specs/20-api.md#inspections](../specs/20-api.md#inspections) | 2 |" in report
