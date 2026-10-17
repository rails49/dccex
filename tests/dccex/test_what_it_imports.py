"""The translator imports the standard library, `control`'s bus library and
itself, and nothing else.

`tc49` is a dependency for its library (ADR-0014 d.2). The rest of `tc49` is
`control`'s apps, and reaching into one of them would tie the translator to
code `control` is free to change without telling anyone.
"""

import ast
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent.parent / "src" / "dccex"


def imported(module: Path) -> set[str]:
    """The full name of everything one module imports."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(module.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def allowed(name: str) -> bool:
    top = name.split(".")[0]
    return (
        top == "dccex"
        or top in sys.stdlib_module_names
        or name == "tc49.lib"
        or name.startswith("tc49.lib.")
    )


def reached(package: Path) -> dict[str, set[str]]:
    """What each module under `package` imports that is not allowed, by its path."""
    return {
        str(module.relative_to(package)): outside
        for module in sorted(package.rglob("*.py"))
        if (outside := {name for name in imported(module) if not allowed(name)})
    }


def test_the_translator_imports_the_standard_library_the_bus_library_and_itself() -> (
    None
):
    outside = reached(PACKAGE)
    assert outside == {}, f"the translator reaches outside: {outside}"


def test_a_module_in_a_subpackage_is_read(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "module.py").write_text("from tc49.layout import x\n")
    assert reached(tmp_path) == {"sub/module.py": {"tc49.layout"}}


def test_the_translator_is_all_that_is_here() -> None:
    """Named so the check above cannot pass by looking at nothing."""
    assert {str(module.relative_to(PACKAGE)) for module in PACKAGE.rglob("*.py")} == {
        "__init__.py",
        "__main__.py",
        "commands.py",
        "journal.py",
        "replies.py",
        "sample.py",
        "script.py",
        "store.py",
        "translator.py",
    }
