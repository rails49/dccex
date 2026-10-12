"""The **journal** the face serves, which another app writes
(ADR-0022 d.4).

The translator keeps the journal: one JSON object per line, appended to a file
on a volume the box keeps (d.1, `dccex.journal`). The mirror mounts the same
volume at the same path, read-only, and this is the whole of what it does with
the file — hand the bytes over as they are. **No line is read here**: whether a line is part of an **incident** is the page's to decide
over the whole file, under a rule that can change while the file does not
(d.3, d.5).

**It is the file and not a document.** A journal that is not there is no bytes
rather than an outage: the ordinary state of a box whose translator has not
written a line yet, and the page reads nothing out of it either way. The file
is opened by name on every read, so a trim, which the translator renames over
it, is served whole (d.4).

Blocking work is done off the loop's thread, as everything that waits here is:
the mirror's fan-out happens while a page is reading a journal, and a throttle
whose bytes waited on a disk would be a throttle this app stopped mirroring
for (`store.py`, `firmware.py`).
"""

import asyncio
from pathlib import Path


class Journal:
    """The file the translator appends to, served.

    Constructed with the path, which is `--journal` on this app's command
    line and a file on the named volume both containers mount
    (`compose.box.yaml`). Nothing is opened until a caller asks: a handle kept
    open here would go on reading a file a trim has replaced.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def where(self) -> str:
        """The path, for the sentence an answer carries where the file could
        not be read."""
        return str(self._path)

    async def served(self) -> bytes:
        """The file as it is, and no bytes where there is no file."""
        return await asyncio.to_thread(self._read)

    def _read(self) -> bytes:
        try:
            return self._path.read_bytes()
        except FileNotFoundError:
            return b""
