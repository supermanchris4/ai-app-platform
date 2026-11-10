"""The package imports only the standard library, itself and its declared dependencies, so it never
reaches into an application's code and installs with nothing missing (README, CLAUDE.md)."""

import ast
import sys
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE_ROOT / "src" / "ai_app_platform"

# The modules each declared dependency provides, where the module is not named like the distribution.
PROVIDED_BY = {
    "fastapi": {"fastapi", "starlette"},  # Starlette is FastAPI's foundation, and part of its API
    "psycopg": {"psycopg"},
    "pydantic-settings": {"pydantic_settings"},
    "pyjwt": {"jwt", "cryptography"},  # the crypto extra installs cryptography
}
# Imported only for type checking, from the development dependencies.
TYPE_CHECKING_ONLY = {"mypy_boto3_secretsmanager"}


def declared_modules() -> set[str]:
    pyproject = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())
    modules: set[str] = set()
    for requirement in pyproject["project"]["dependencies"]:
        name = requirement.split("[")[0].split(">")[0].split("=")[0].split("<")[0].strip().lower()
        modules |= PROVIDED_BY.get(name, {name.replace("-", "_")})
    return modules


def imports(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


def type_checking_imports(tree: ast.AST) -> set[str]:
    """Imports inside `if TYPE_CHECKING:` blocks, which never run."""
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            for statement in node.body:
                modules |= imports(statement)
    return modules


@pytest.mark.parametrize("path", sorted(SOURCE.rglob("*.py")), ids=lambda path: str(path.relative_to(SOURCE)))
def test_the_package_imports_only_what_it_declares(path: Path) -> None:
    tree = ast.parse(path.read_text())
    allowed = set(sys.stdlib_module_names) | {"ai_app_platform"} | declared_modules()
    undeclared = imports(tree) - allowed - (type_checking_imports(tree) & TYPE_CHECKING_ONLY)
    assert not undeclared, f"imports {sorted(undeclared)}, which the package does not declare"


def test_the_package_imports_itself_by_name() -> None:
    """Absolute imports only, so a module's imports read the same wherever it sits."""
    relative = [
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.ImportFrom) and node.level
    ]
    assert not relative
