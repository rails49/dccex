"""The file the translator appends to: one JSON object per line, on the disk
as it is written (ADR-0022 d.1, d.4).

What goes on a line is `test_translator.py`'s, where there is a station to
say it. What is here is the file: that a line is whole JSON, that it is
stamped, that nothing already in the file is rewritten, and that a clear by
another process loses no line and is not fought over.
"""

import json
import os
from pathlib import Path

from dccex.journal import Journal

AT = "2026-10-12T18:00:12.345+00:00"


def lines(path: Path) -> list[dict[str, object]]:
    """The file read back, one object per line."""
    return [json.loads(said) for said in path.read_text().splitlines()]


def test_a_line_is_one_json_object_stamped_with_when_it_arrived(
    tmp_path: Path,
) -> None:
    """`at` first and the fields the translator handed over after it, which is
    the order a person reads them in."""
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT)
    journal.wrote({"railroad": "gleis49", "build": "v5.6.4", "link": "up"})
    assert lines(path) == [
        {"at": AT, "railroad": "gleis49", "build": "v5.6.4", "link": "up"}
    ]
    assert list(lines(path)[0]) == ["at", "railroad", "build", "link"]


def test_every_line_is_on_the_disk_as_it_is_written(tmp_path: Path) -> None:
    """Read back with the journal still open: the file is read by another app
    and by a person, so a line left in a buffer is a line a reader is told
    nothing about."""
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT)
    for said in ("<p1 A>", "<p0 A>", "<p1 A>"):
        journal.wrote({"said": said})
        assert [line["said"] for line in lines(path)][-1] == said
    assert len(lines(path)) == 3


def test_a_journal_opened_on_a_file_that_is_there_appends_to_it(
    tmp_path: Path,
) -> None:
    """Appending and never truncating: a process that comes back up adds to
    the record rather than replacing it (d.4)."""
    path = tmp_path / "journal.jsonl"
    path.write_text('{"at": "before", "said": "<p1 A>"}\n')
    Journal(path, at=lambda: AT).wrote({"said": "<p0 A>"})
    assert [line["at"] for line in lines(path)] == ["before", AT]


def test_a_line_arriving_after_a_clear_lands_at_the_start_of_the_file(
    tmp_path: Path,
) -> None:
    """The mirror's face truncates the file on a request from the page, and
    the translator is appending to it at the time (d.4).

    Under `O_APPEND` a write lands at whatever the end of the file is at the
    moment it happens, so a clear loses no line and the next line starts the
    file rather than sitting at the offset the cleared lines reached. A
    journal that held its own offset would leave a reader bytes of nothing to
    get past.
    """
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT)
    journal.wrote({"said": "<p1 A>"})
    os.truncate(path, 0)
    journal.wrote({"said": "<p0 A>"})
    assert path.read_text() == json.dumps({"at": AT, "said": "<p0 A>"}) + "\n"


def test_the_stamp_is_iso_8601_to_the_millisecond(tmp_path: Path) -> None:
    """The station cuts a district and retries it inside one second
    (ADR-0016), so a stamp to the second would put a trip and its retry at
    the same moment."""
    path = tmp_path / "journal.jsonl"
    Journal(path).wrote({"said": "<p1 A>"})
    at = lines(path)[0]["at"]
    assert isinstance(at, str)
    assert at.endswith("+00:00"), at
    assert len(at.split(".")[1]) == len("000+00:00"), at
