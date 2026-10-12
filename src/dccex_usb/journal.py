"""The **journal** the face serves and clears, which another app writes
(ADR-0022 d.4).

The translator keeps the journal: one JSON object per line, appended to a file
on a volume the box keeps (d.1, `dccex.journal`). The mirror mounts the same
volume at the same path, and this is the whole of what it does with the file —
hand the bytes over as they are, and empty it when the page asks. **No line is
read here**: whether a line is part of an **incident** is the page's to decide
over the whole file, under a rule that can change while the file does not
(d.3, d.5).

**It is the file and not a document.** A journal that is not there is no bytes
rather than an outage: the ordinary state of a box whose translator has not
written a line yet, and the page reads nothing out of it either way. A clear
truncates the file in place rather than removing it, so the translator's next
append — under `O_APPEND` on a handle it opened once and does not reopen —
lands at the start of the same file (d.4).

Blocking work is done off the loop's thread, as everything that waits here is:
the mirror's fan-out happens while a page is reading a journal, and a throttle
whose bytes waited on a disk would be a throttle this app stopped mirroring
for (`store.py`, `firmware.py`).
"""

import asyncio
import os
from pathlib import Path


class Journal:
    """The file the translator appends to, served and cleared.

    Constructed with the path, which is `--journal` on this app's command
    line and a file on the named volume both containers mount
    (`compose.box.yaml`). Nothing is opened until a caller asks: the writer is
    the other app, and a handle kept open here would be a handle a clear has
    to agree with.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def where(self) -> str:
        """The path, for the sentence an answer carries where the file could
        not be read or emptied."""
        return str(self._path)

    async def served(self) -> bytes:
        """The file as it is, and no bytes where there is no file."""
        return await asyncio.to_thread(self._read)

    async def cleared(self) -> int:
        """The file emptied, and how many bytes went."""
        return await asyncio.to_thread(self._clear)

    def _read(self) -> bytes:
        try:
            return self._path.read_bytes()
        except FileNotFoundError:
            return b""

    def _clear(self) -> int:
        # Truncated in place and never removed or replaced: the translator
        # holds a handle on this file and does not reopen it, so a clear that
        # unlinked the name would leave that app appending to a file nothing
        # can read (ADR-0022 d.4).
        try:
            with self._path.open("r+b") as file:
                emptied = file.seek(0, os.SEEK_END)
                file.truncate(0)
        except FileNotFoundError:
            return 0
        return emptied
