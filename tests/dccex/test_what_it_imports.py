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


def test_the_translator_imports_the_standard_library_the_bus_library_and_itself() -> (
    None
):
    reached = {
        module.name: outside
        for module in sorted(PACKAGE.glob("*.py"))
        if (outside := {name for name in imported(module) if not allowed(name)})
    }
    assert reached == {}, f"the translator reaches outside: {reached}"


def test_the_translator_is_all_that_is_here() -> None:
    """Named so the check above cannot pass by looking at nothing."""
    assert {module.name for module in PACKAGE.glob("*.py")} == {
        "__init__.py",
        "__main__.py",
        "commands.py",
        "replies.py",
        "sample.py",
        "script.py",
        "store.py",
        "translator.py",
    }
