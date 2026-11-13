"""Requirement traceability, from the implementation to the requirements (the template's 13-delivery-pipeline.md).

Requirements name nothing that implements them. Instead each specification section names the requirements it
implements on a `**Requirements:**` line, and each test names the requirements it verifies:

- A Python test's docstring starts with `Verifies FR-INSP-01, NFR-SEC-01.` or `Verifies no requirement.`
- A web or end-to-end test's title starts with `FR-INSP-01, NFR-SEC-01: ...` or `No requirement: ...`

The check fails when a cited ID is not a requirement, when a test names none, or when the committed trace report is
not what this module generates. Run from the repository root:

    python -m ai_app_platform.traceability            # check
    python -m ai_app_platform.traceability --write    # regenerate the trace report
"""

import argparse
import ast
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

ID = r"(?:FR|NFR|CMP)-[A-Z]{2,5}-\d{2}[a-z]?"
_ID = re.compile(rf"\b{ID}\b")
_HEADING_ID = re.compile(rf"^#{{2,6}} ({ID})\b", re.MULTILINE)
_TABLE_ID = re.compile(rf"^\| *({ID}) *\|", re.MULTILINE)
_REQUIREMENTS_LINE = re.compile(r"^\*\*Requirements:\*\*(.*)$")
_HEADING = re.compile(r"^(#{1,6}) +(.+?) *$")
_PY_VERIFIES = re.compile(rf"^Verifies ((?:{ID})(?:(?:, | and ){ID})*)\.")
_PY_NONE = "Verifies no requirement."
_WEB_TITLE = re.compile(r"""\b(?:it|test)(?:\.only|\.skip|\.fixme)?\(\s*(["'`])((?:\\.|(?!\1).)*)\1""", re.DOTALL)
_WEB_VERIFIES = re.compile(rf"^((?:{ID})(?:, {ID})*): ")
_WEB_NONE = "No requirement: "

DEFAULT_TESTS = (
    "apps/api/tests/**/test_*.py",
    "apps/web/src/**/*.test.ts",
    "apps/web/src/**/*.test.tsx",
    "apps/web/e2e/**/*.spec.ts",
)


@dataclass
class Trace:
    """What the specifications and tests say about each requirement."""

    requirements: list[str]
    sections: dict[str, list[str]] = field(default_factory=dict[str, list[str]])
    tests: dict[str, list[str]] = field(default_factory=dict[str, list[str]])
    problems: list[str] = field(default_factory=list[str])


def requirement_ids(text: str) -> list[str]:
    """The IDs the requirements file defines, as `### ID:` headings or as the first cell of a table row."""
    found = _HEADING_ID.findall(text) + _TABLE_ID.findall(text)
    return sorted(set(found), key=_sort_key)


def _sort_key(requirement: str) -> tuple[str, str, int, str]:
    kind, area, number = requirement.split("-", 2)
    digits = re.match(r"\d+", number)
    return kind, area, int(digits.group()) if digits else 0, number


def _slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9 _-]", "", heading.lower()).replace(" ", "-")


def section_citations(path: Path, root: Path) -> list[tuple[str, list[str]]]:
    """Each section of a specification with a Requirements line, as (link, cited IDs)."""
    heading = ""
    cited: list[tuple[str, list[str]]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := _HEADING.match(line):
            heading = match.group(2)
        elif match := _REQUIREMENTS_LINE.match(line.strip()):
            link = path.relative_to(root).as_posix() + (f"#{_slug(heading)}" if heading else "")
            cited.append((link, _ID.findall(match.group(1))))
    return cited


def python_test_citations(path: Path, root: Path) -> list[tuple[str, list[str] | None]]:
    """Each test function in a Python test file, as (name, cited IDs); None when it names nothing."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, list[str] | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_"):
            name = f"{path.relative_to(root).as_posix()}::{node.name}"
            docstring = (ast.get_docstring(node) or "").strip()
            if docstring.startswith(_PY_NONE):
                found.append((name, []))
            elif match := _PY_VERIFIES.match(docstring):
                found.append((name, _ID.findall(match.group(1))))
            else:
                found.append((name, None))
    return sorted(found)


def web_test_citations(path: Path, root: Path) -> list[tuple[str, list[str] | None]]:
    """Each `it` or `test` in a web test file, as (title, cited IDs); None when it names nothing."""
    found: list[tuple[str, list[str] | None]] = []
    for match in _WEB_TITLE.finditer(path.read_text(encoding="utf-8")):
        title = match.group(2)
        name = f"{path.relative_to(root).as_posix()}::{title}"
        if title.startswith(_WEB_NONE):
            found.append((name, []))
        elif verifies := _WEB_VERIFIES.match(title):
            found.append((name, _ID.findall(verifies.group(1))))
        else:
            found.append((name, None))
    return found


def _files(root: Path, patterns: Iterable[str]) -> list[Path]:
    return sorted({path for pattern in patterns for path in root.glob(pattern) if "node_modules" not in path.parts})


def trace(root: Path, requirements: str, specs: str, tests: Sequence[str]) -> Trace:
    """Collect every citation under root and record each problem."""
    requirements_path = root / requirements
    result = Trace(requirements=requirement_ids(requirements_path.read_text(encoding="utf-8")))
    known = set(result.requirements)
    if not known:
        result.problems.append(f"{requirements}: no requirement IDs found")

    for spec in sorted((root / specs).glob("*.md")):
        if spec.resolve() == requirements_path.resolve():
            continue
        for link, cited in section_citations(spec, root):
            if not cited:
                result.problems.append(f"{link}: the Requirements line names no requirement")
            for requirement in cited:
                if requirement in known:
                    result.sections.setdefault(requirement, []).append(link)
                else:
                    result.problems.append(f"{link}: {requirement} is not a requirement")

    for path in _files(root, tests):
        citations = python_test_citations(path, root) if path.suffix == ".py" else web_test_citations(path, root)
        for name, cited in citations:
            if cited is None:
                result.problems.append(f"{name}: the test names no requirement it verifies")
                continue
            for requirement in cited:
                if requirement in known:
                    result.tests.setdefault(requirement, []).append(name)
                else:
                    result.problems.append(f"{name}: {requirement} is not a requirement")
    return result


def report(result: Trace) -> str:
    """The trace report: for each requirement, the specification sections and tests that cite it."""
    lines = [
        "# Requirements trace",
        "",
        "Generated by `python -m ai_app_platform.traceability --write`; do not edit. For each requirement, the "
        "specification sections that implement it and the tests that verify it.",
        "",
        "| Requirement | Specification sections | Tests |",
        "|---|---|---|",
    ]
    for requirement in result.requirements:
        sections = ", ".join(f"[{link}](../{link})" for link in result.sections.get(requirement, [])) or "None"
        tests = result.tests.get(requirement, [])
        lines.append(f"| {requirement} | {sections} | {len(tests)} |")
    lines += ["", "## Tests", ""]
    for requirement in result.requirements:
        tests = result.tests.get(requirement, [])
        if tests:
            lines += [f"### {requirement}", "", *(f"- `{name}`" for name in tests), ""]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ai_app_platform.traceability",
        description="Check requirement traceability, or regenerate the trace report.",
    )
    parser.add_argument("--root", default=".", help="The repository root (default: the current directory)")
    parser.add_argument("--requirements", default="specs/02-requirements.md")
    parser.add_argument("--specs", default="specs", help="The directory of specifications")
    parser.add_argument("--tests", nargs="+", default=list(DEFAULT_TESTS), help="Glob patterns of test files")
    parser.add_argument("--report", default="docs/requirements-trace.md", help="The committed trace report")
    parser.add_argument("--write", action="store_true", help="Regenerate the trace report instead of checking it")
    args = parser.parse_args(argv)

    root = Path(args.root)
    result = trace(root, args.requirements, args.specs, args.tests)
    generated = report(result)
    report_path = root / args.report
    if args.write:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(generated, encoding="utf-8")
    elif not report_path.exists() or report_path.read_text(encoding="utf-8") != generated:
        result.problems.append(f"{args.report} is not current: run python -m ai_app_platform.traceability --write")

    for problem in result.problems:
        print(problem, file=sys.stderr)
    tested = sum(1 for requirement in result.requirements if result.tests.get(requirement))
    print(
        f"{len(result.requirements)} requirements, {tested} verified by a test; {len(result.problems)} problems",
        file=sys.stderr,
    )
    return 1 if result.problems else 0


if __name__ == "__main__":
    sys.exit(main())
