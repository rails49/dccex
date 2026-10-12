"""The journal: what the station said about power, kept on the box (ADR-0022).

One JSON object per line, appended to a file on a volume the box keeps. It is
written whether or not a page is open, because the translator is the client
that wants the record (d.1), and **nothing here decides anything about a
line** (d.3): whether a line is part of an **incident** is read off the file
afterwards, by the page, under a rule that can change while the file does not.

What goes on a line is the translator's (`DccEx._journalled`); what is here is
the file and the clock. Each line is stamped with when it arrived and flushed
as it is written, so a reader of the file is never one line behind a railroad.

**The file is opened once, for appending, and is not reopened, rotated or
truncated here** (d.4). Clearing it is the mirror's face, on a request from
the page, and the two apps agree on nothing more than the volume: appending is
what makes that safe, a write under `O_APPEND` landing at whatever the end of
the file is at the moment it happens. So a clear loses no line, and the line
after one lands at the start of the file.
"""

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

Line = dict[str, object]
"""One line, as the translator hands it over: the fields that are this line's,
with `at` still to be stamped."""

Stamp = Callable[[], str]
"""Where a line's `at` comes from, injected so the suite asserts a line
rather than a clock."""


def arrived() -> str:
    """When a line arrived, as a line carries it: ISO 8601 in UTC, to the
    millisecond.

    UTC because a box's own zone is not a fact about the railroad, and
    milliseconds because the station cuts a district and retries it inside
    one second (ADR-0016) — a stamp to the second would put a trip and its
    retry at the same moment.
    """
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class Journal:
    """The file the translator appends to, open for as long as the process
    runs."""

    def __init__(self, path: str | Path, *, at: Stamp = arrived) -> None:
        # Open for as long as the process is, which is what d.4 asks for: a
        # context manager here would close the file after one line and reopen
        # it for the next.
        self._file: IO[str] = Path(path).open("a", encoding="utf-8")  # noqa: SIM115
        self._at = at
        self._end = self._size()

    def _size(self) -> int:
        return os.fstat(self._file.fileno()).st_size

    def cleared(self) -> bool:
        """Whether the file is shorter than this left it: the mirror's face
        truncated it since the last line written here (d.4)."""
        return self._size() < self._end

    def wrote(self, line: Line) -> None:
        """One line, stamped with when it arrived and on the disk before this
        returns.

        Flushed rather than left to the buffer: the file is read by another
        app and by a person, and a line that is only in this process is a line
        a reader is told nothing about.
        """
        self._file.write(json.dumps({"at": self._at(), **line}) + "\n")
        self._file.flush()
        self._end = self._size()

    def close(self) -> None:
        """Let the file go. Nothing is lost by not calling it — every line is
        flushed as it is written — and whoever opened the journal closes it
        (`__main__.py`)."""
        self._file.close()
