"""The translator and its tests import the standard library, the four modules
`control` declares for another repository, and this repository, and nothing
else.

`tc49` is a dependency for its library (ADR-0014 d.2). control ADR-0075
declares `tc49.lib.bus`, `mqtt`, `clock` and `inventory` for another
repository; the rest is code `control` is free to change without telling
anyone.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = ROOT / "src" / "dccex"
TESTS = ROOT / "tests"

TC49 = frozenset(
    {"tc49.lib.bus", "tc49.lib.mqtt", "tc49.lib.clock", "tc49.lib.inventory"}
)

TESTED_WITH = frozenset({"pytest", "playwright", "dccex_usb"})
"""What the tests import beside the translator: the runner, the browser and
the mirror."""


def imported(module: Path) -> set[str]:
    """The full name of everything one module imports."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(module.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def allowed(name: str, extra: frozenset[str] = frozenset()) -> bool:
    top = name.split(".")[0]
    return (
        name in TC49
        or top in {"dccex", "tests"}
        or top in extra
        or top in sys.stdlib_module_names
    )


def reached(package: Path, extra: frozenset[str] = frozenset()) -> dict[str, set[str]]:
    """What each module under `package` imports that is not allowed, by its
    path."""
    return {
        str(module.relative_to(package)): outside
        for module in sorted(package.rglob("*.py"))
        if (outside := {name for name in imported(module) if not allowed(name, extra)})
    }


def test_the_translator_imports_the_standard_library_four_tc49_modules_and_itself() -> (
    None
):
    outside = reached(PACKAGE)
    assert outside == {}, f"the translator reaches outside: {outside}"


def test_the_tests_import_the_same_and_what_they_are_tested_with() -> None:
    outside = reached(TESTS, TESTED_WITH)
    assert outside == {}, f"the tests reach outside: {outside}"


def test_a_module_in_a_subpackage_is_read(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "module.py").write_text("import tc49.layout\n")
    assert reached(tmp_path) == {"sub/module.py": {"tc49.layout"}}


def test_a_test_that_imports_an_undeclared_tc49_module_is_refused(
    tmp_path: Path,
) -> None:
    (tmp_path / "dccex").mkdir()
    (tmp_path / "dccex" / "test_x.py").write_text(
        "import pytest\nimport tc49.lib.payload\n"
    )
    assert reached(tmp_path, TESTED_WITH) == {"dccex/test_x.py": {"tc49.lib.payload"}}


def test_the_translator_is_all_that_is_here() -> None:
    """Named so the check above cannot pass by looking at nothing."""
    assert {str(module.relative_to(PACKAGE)) for module in PACKAGE.rglob("*.py")} == {
        "__init__.py",
        "__main__.py",
        "commands.py",
        "journal.py",
        "log.py",
        "replies.py",
        "rows.py",
        "sample.py",
        "script.py",
        "store.py",
        "translator.py",
    }
