"""The journal: what the station said about power, kept on the box (ADR-0022).

One JSON object per line, appended to a file on a volume the box keeps. It is
written whether or not a page is open, because the translator is the client
that wants the record (d.1), and **nothing here decides anything about a
line** (d.3): whether a line is part of an **incident** is read off the file
afterwards, by the page, under a rule that can change while the file does not.

What goes on a line is the translator's (`DccEx._journalled`); what is here is
the file and the clock. Each line is stamped with when it arrived and flushed
as it is written, so a reader of the file is never one line behind a railroad.

**The translator is the only writer, and it keeps the file to a size.**
Above `TRIMMED_ABOVE` bytes the oldest lines go, down to the newest
`TRIMMED_TO` bytes, and the last `<p…>` about each district from the part that
went is kept in front of them, so the file still says each district's power
(ADR-0022 d.4 as amended). The trim is written to a file beside the journal
and renamed over it, so the mirror's face, which opens the file by name on
every read, serves the old file or the new one and never half of either.
"""

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

TRIMMED_ABOVE = 10_000_000
"""The journal's size in bytes above which its oldest lines go."""

TRIMMED_TO = 8_000_000
"""The most bytes of newest lines a trim keeps."""

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

    def __init__(
        self,
        path: str | Path,
        *,
        at: Stamp = arrived,
        above: int = TRIMMED_ABOVE,
        to: int = TRIMMED_TO,
    ) -> None:
        self._path = Path(path)
        self._at = at
        self._above = above
        self._to = to
        self._file = self._opened()
        self._trimmed()

    def _opened(self) -> IO[str]:
        # Open until the next trim or the end of the process: a context
        # manager here would close the file after one line.
        return self._path.open("a", encoding="utf-8")

    def _trimmed(self) -> None:
        """The oldest lines gone where the file is over its size, and the
        last power line about each district from them kept."""
        if os.fstat(self._file.fileno()).st_size <= self._above:
            return
        whole = self._path.read_bytes()
        cut = whole.find(b"\n", len(whole) - self._to - 1) + 1
        power: dict[object, bytes] = {}
        for said in whole[:cut].splitlines(keepends=True):
            line = json.loads(said)
            if "district" in line and str(line.get("said")).startswith("<p"):
                power.pop(line["district"], None)
                power[line["district"]] = said
        trimmed = self._path.with_name(self._path.name + ".trimmed")
        trimmed.write_bytes(b"".join(power.values()) + whole[cut:])
        trimmed.replace(self._path)
        self._file.close()
        self._file = self._opened()

    def wrote(self, line: Line) -> None:
        """One line, stamped with when it arrived and on the disk before this
        returns.

        Flushed rather than left to the buffer: the file is read by another
        app and by a person, and a line that is only in this process is a line
        a reader is told nothing about.
        """
        self._file.write(json.dumps({"at": self._at(), **line}) + "\n")
        self._file.flush()
        self._trimmed()

    def close(self) -> None:
        """Let the file go. Nothing is lost by not calling it — every line is
        flushed as it is written — and whoever opened the journal closes it
        (`__main__.py`)."""
        self._file.close()
