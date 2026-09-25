"""The package imports nothing but the standard library and itself.

Not a style rule. The mirror exists so that a command station can be watched
and typed at on a box with nothing else running, and every import that is not
the standard library's is a thing that has to be there for a cable to be
mirrored. The bus was the last of them and it went (ADR-0001); this is what
keeps the next one from arriving quietly.

The flasher is the one dependency and it is not imported: esptool is a
subprocess with a timeout, which is what keeps its failures off the process
every throttle depends on (control ADR-0065).
"""

import ast
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "src" / "dccex_usb"

OWN = "dccex_usb"


def imported(module: Path) -> set[str]:
    """The top-level name of everything one module imports."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(module.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_the_package_imports_nothing_but_the_standard_library_and_itself() -> None:
    reached: dict[str, set[str]] = {}
    for module in sorted(PACKAGE.glob("*.py")):
        outside = {
            name
            for name in imported(module)
            if name != OWN and name not in sys.stdlib_module_names
        }
        if outside:
            reached[module.name] = outside

    assert reached == {}, f"the package reaches outside the standard library: {reached}"


def test_the_package_is_all_that_is_here() -> None:
    """Named so the check above cannot pass by looking at nothing."""
    assert {module.name for module in PACKAGE.glob("*.py")} == {
        "__init__.py",
        "__main__.py",
        "face.py",
        "firmware.py",
        "framing.py",
        "station.py",
        "stream.py",
    }
