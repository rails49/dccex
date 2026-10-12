"""The file the translator appends to: one JSON object per line, on the disk
as it is written (ADR-0022 d.1, d.4).

What goes on a line is `test_translator.py`'s, where there is a station to
say it. What is here is the file: that a line is whole JSON, that it is
stamped, that nothing already in the file is rewritten until it is over its
size, and what a trim keeps.
"""

import json
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


def power(said: str, district: str) -> dict[str, object]:
    """A `<p…>` line about a district, as the translator hands one over."""
    return {"said": said, "district": district}


def test_a_file_over_its_size_keeps_its_newest_lines(tmp_path: Path) -> None:
    """Whole lines, the newest that fit, and nothing older (d.4 as amended)."""
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT, above=500, to=400)
    for n in range(20):
        journal.wrote({"link": str(n)})
    assert path.stat().st_size <= 500
    links = [line["link"] for line in lines(path)]
    assert links == [str(n) for n in range(20 - len(links), 20)]
    journal.wrote({"link": "20"})
    assert lines(path)[-1]["link"] == "20"


def test_a_trim_keeps_the_last_power_line_about_each_district(
    tmp_path: Path,
) -> None:
    """A district whose power has not changed since its last line would say
    nothing about it after the trim (#275). Its last line stays, in front of
    the newest lines and in the order it was written."""
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT, above=1000, to=400)
    journal.wrote(power("<p1 A>", "A"))
    journal.wrote(power("<p1 B>", "B"))
    journal.wrote(power("<p0 A>", "A"))
    journal.wrote({"said": "<* TRACK A ALERT *>", "district": "A"})
    for n in range(30):
        journal.wrote({"link": str(n)})
    said = [line.get("said") for line in lines(path)]
    assert said[:2] == ["<p1 B>", "<p0 A>"]
    assert "<* TRACK A ALERT *>" not in said
    assert lines(path)[-1] == {"at": AT, "link": "29"}


def test_a_file_over_its_size_is_trimmed_when_it_is_opened(
    tmp_path: Path,
) -> None:
    """A journal left large by a process that kept a larger size."""
    path = tmp_path / "journal.jsonl"
    path.write_text("".join(f'{{"at": "before", "link": "{n}"}}\n' for n in range(50)))
    Journal(path, at=lambda: AT, above=500, to=400)
    assert path.stat().st_size <= 400
    assert lines(path)[-1]["link"] == "49"


def test_a_reader_holding_the_file_through_a_trim_reads_it_whole(
    tmp_path: Path,
) -> None:
    """The trim is a new file renamed over the old one, so a reader that
    opened the file before it reads the old file, whole lines from its
    start up to the trim."""
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, at=lambda: AT, above=500, to=400)
    journal.wrote({"link": "0"})
    with path.open() as reading:
        for n in range(1, 20):
            journal.wrote({"link": str(n)})
        held = [json.loads(said)["link"] for said in reading.read().splitlines()]
    assert held == [str(n) for n in range(len(held))]
    assert len(held) < 20


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
