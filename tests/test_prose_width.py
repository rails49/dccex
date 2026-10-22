"""Prose lines over 80 columns that could wrap turn the gate red (#335).

Python comments and docstrings are ruff's `W505`, configured in
`pyproject.toml`; it is run here on a probe through stdin, named as the file
it stands for. TS/JS comment lines and Markdown are `scripts/prose_width.py`,
run on files written under a temporary tree laid out like this one.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The script the gate runs for the two scopes ruff does not cover.
SCRIPT = ROOT / "scripts" / "prose_width.py"

#: Words that wrap, 81 columns once a two-column marker is in front.
WORDS = " ".join(["word"] * 15) + " word"
assert len(WORDS) == 79

#: A URL 100 columns long.
URL = "https://example.com/" + "a" * 80
assert len(URL) == 100


def ruff(name: str, text: str) -> subprocess.CompletedProcess[str]:
    """Ruff's `W505` on `text`, as if it were the file `name`."""
    return subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", "--select", "W505"]
        + ["--stdin-filename", name, "-"],
        cwd=ROOT,
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )


def width(tmp_path: Path, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """`scripts/prose_width.py` on `files`, written under `tmp_path`."""
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *files],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "text",
    [f"# {WORDS}\n", f'"""{WORDS[:-1]}"""\n'],
    ids=["comment", "docstring"],
)
def test_a_python_line_of_81_columns_is_red(text: str) -> None:
    said = ruff("tests/dccex/probe.py", text)
    assert said.returncode == 1, said.stdout
    assert "W505" in said.stdout


def test_a_python_line_of_80_columns_passes() -> None:
    said = ruff("tests/dccex/probe.py", f"# {WORDS[:-1]}\n")
    assert said.returncode == 0, said.stdout


@pytest.mark.parametrize("name", ["src/dccex_usb/probe.py", "tests/dccex_usb/probe.py"])
def test_the_copied_package_is_not_flagged(name: str) -> None:
    said = ruff(name, f"# {WORDS}\n")
    assert said.returncode == 0, said.stdout


@pytest.mark.parametrize(
    ("name", "line"),
    [
        ("ui/src/probe.ts", f"// {WORDS[1:]}"),
        ("ui/src/probe.js", f"/* {WORDS[1:]}"),
        ("ui/test/probe.ts", f" * {WORDS[1:]}"),
        ("README.md", f"  {WORDS}"),
        ("docs/adr/probe.md", f"- {WORDS}"),
    ],
)
def test_a_line_of_81_columns_that_could_wrap_is_red(
    tmp_path: Path, name: str, line: str
) -> None:
    assert len(line) == 81
    said = width(tmp_path, {name: f"{line}\n"})
    assert said.returncode == 1
    assert said.stdout == f"{name}:1: 81\n"


def test_a_line_of_80_columns_passes(tmp_path: Path) -> None:
    said = width(
        tmp_path, {"README.md": f"{WORDS}\n", "ui/src/a.ts": f"// {WORDS[3:]}\n"}
    )
    assert said.returncode == 0, said.stdout


@pytest.mark.parametrize(
    "text",
    [
        f"{URL}\n",
        f"  ([ADR-0001]({URL})).\n",
        f"- [ADR-0001]({URL})\n",
        f"| {WORDS} | {WORDS} |\n",
        f"Before.\n\n```sh\n{WORDS} {WORDS}\n```\n\nAfter.\n",
        f"- A list.\n\n  ~~~~\n  {WORDS} {WORDS}\n  ~~~\n  {WORDS}\n  ~~~~\n",
    ],
    ids=["url", "link", "list-link", "table", "fence", "nested-fence"],
)
def test_markdown_that_cannot_wrap_or_is_not_prose_passes(
    tmp_path: Path, text: str
) -> None:
    said = width(tmp_path, {"docs/probe.md": text})
    assert said.returncode == 0, said.stdout


def test_a_line_after_a_fence_closes_is_read(tmp_path: Path) -> None:
    said = width(tmp_path, {"README.md": f"```\ncode\n```\n  {WORDS}\n"})
    assert said.stdout == "README.md:4: 81\n"


@pytest.mark.parametrize(
    "line", [f"// {URL}", f" * {URL}", f"const a = '{WORDS} {WORDS}';"]
)
def test_a_code_line_or_a_lone_url_in_a_comment_passes(
    tmp_path: Path, line: str
) -> None:
    said = width(tmp_path, {"ui/src/probe.ts": f"{line}\n"})
    assert said.returncode == 0, said.stdout


@pytest.mark.parametrize(
    "name",
    [
        "docs/agents/probe.md",
        ".out-of-scope/probe.md",
        "ui/probe.ts",
        "ui/src/probe.css",
        "src/probe.py",
    ],
)
def test_a_file_outside_the_scopes_is_not_read(tmp_path: Path, name: str) -> None:
    said = width(tmp_path, {name: f"// {WORDS}\n"})
    assert said.returncode == 0, said.stdout
