#!/usr/bin/env python3
"""Prose lines over 80 columns that could have been wrapped (#335).

Two of the gate's three scopes: comment lines in tracked `.ts` and `.js`
files under `ui/src` and `ui/test`, and prose in tracked Markdown outside
`docs/agents` and `.out-of-scope`. The third, Python comments and
docstrings, is ruff's `W505` (`pyproject.toml`).

A comment line is one whose first non-blank characters are `//`, `/*` or `*`.
In Markdown, lines inside a fenced block and table rows are not read.

A line over 80 columns passes when no space follows its first word at or
before column 80: a link or URL alone on its line cannot be broken. Leading
list, quote and comment markers are not a word, so `- [ADR-0001](url)` is one
link alone.

    python3 scripts/prose_width.py [path ...]

With no paths it reads what `git ls-files` lists and the working tree still
holds. It prints `file:line: columns` for each line it flags and exits 1 if
there is one.
"""

import os
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from pathlib import PurePosixPath

#: The widest a prose line may be.
WIDTH = 80

#: Where the comment scope reads.
CODE_TREES = ("ui/src/", "ui/test/")
CODE_SUFFIXES = (".ts", ".js")

#: What the Markdown scope does not read.
MARKDOWN_SKIPPED = ("docs/agents/", ".out-of-scope/")

#: A comment line.
COMMENT = re.compile(r"\s*(?://|/\*|\*)")

#: A fence opening or closing a code block, and what it is drawn with.
FENCE = re.compile(r"\s*(?P<mark>`{3,}|~{3,})")

#: The markers in front of a line's first word: indent, comment, list, quote.
MARKERS = re.compile(r"(?:\s*(?://|/\*|\*|[-+>]|\d+[.)])(?=\s|$))*\s*")


def scope(path: str) -> str | None:
    """Which scope a path is in: `"code"`, `"markdown"`, or None."""
    if path.startswith(CODE_TREES) and path.endswith(CODE_SUFFIXES):
        return "code"
    if path.endswith(".md") and not path.startswith(MARKDOWN_SKIPPED):
        return "markdown"
    return None


def breakable(line: str) -> bool:
    """Whether a space follows the line's first word at or before `WIDTH`."""
    start = MARKERS.match(line)
    first = start.end() if start else 0
    space = line.find(" ", first)
    return space != -1 and space < WIDTH


def code_lines(text: str) -> Iterator[tuple[int, str]]:
    """The comment lines of a TS or JS file, numbered from 1."""
    for number, line in enumerate(text.splitlines(), 1):
        if COMMENT.match(line):
            yield number, line


def markdown_lines(text: str) -> Iterator[tuple[int, str]]:
    """The prose lines of a Markdown file, numbered from 1."""
    fence = ""
    for number, line in enumerate(text.splitlines(), 1):
        opened = FENCE.match(line)
        if fence:
            if opened and opened["mark"].startswith(fence):
                fence = ""
            continue
        if opened:
            fence = opened["mark"]
            continue
        if line.lstrip().startswith("|"):
            continue
        yield number, line


def flagged(path: str, text: str) -> Iterator[tuple[int, int]]:
    """The lines of a file over `WIDTH` that could wrap, with their columns."""
    kind = scope(path)
    if kind is None:
        return
    lines = code_lines(text) if kind == "code" else markdown_lines(text)
    for number, line in lines:
        line = line.rstrip()
        if len(line) > WIDTH and breakable(line):
            yield number, len(line)


def tracked() -> list[str]:
    """The paths `git ls-files` lists that exist in the working tree."""
    listed = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, check=True, text=True
    )
    return [path for path in listed.stdout.split("\0") if os.path.exists(path)]


def main(paths: Iterable[str]) -> int:
    """Print each flagged line; 1 if there was one."""
    red = False
    for path in paths:
        path = PurePosixPath(path).as_posix()
        if scope(path) is None:
            continue
        with open(path, encoding="utf-8") as file:
            text = file.read()
        for number, columns in flagged(path, text):
            print(f"{path}:{number}: {columns}")
            red = True
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or tracked()))
