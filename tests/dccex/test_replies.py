"""What the station says, framed and read: the three facts, and everything
else.

The port carries the whole conversation — this app's replies, and every
broadcast meant for JMRI, a hand-held throttle or a browser — so most of what
is read here is somebody else's and reads as nothing at all (#289).
"""

from dccex import replies


def test_bytes_become_whole_messages() -> None:
    assert replies.messages(b"", b"<p1><p0 A>") == (b"", [b"<p1>", b"<p0 A>"])


def test_a_partial_message_is_carried_to_the_next_read() -> None:
    partial, whole = replies.messages(b"", b"<p1 ")
    assert whole == []
    assert replies.messages(partial, b"A>") == (b"", [b"<p1 A>"])


def test_bytes_outside_a_message_are_dropped() -> None:
    assert replies.messages(b"", b"junk<p1>more") == (b"", [b"<p1>"])


def test_a_second_start_begins_the_message_again() -> None:
    assert replies.messages(b"", b"<p1<p0>") == (b"", [b"<p0>"])


def test_a_message_that_never_ends_is_discarded() -> None:
    partial, whole = replies.messages(b"", b"<" + b"x" * (replies.MAX_MESSAGE + 1))
    assert (partial, whole) == (b"", [])


def test_the_line_naming_a_track_says_which() -> None:
    assert replies.reply(b"<p1 A>") == replies.Power(track="A", on=True)
    assert replies.reply(b"<p0 B>") == replies.Power(track="B", on=False)


def test_the_line_naming_no_track_says_it_of_every_one() -> None:
    assert replies.reply(b"<p1>") == replies.Power(track="", on=True)
    assert replies.reply(b"<p0>") == replies.Power(track="", on=False)


def test_a_power_line_naming_a_mode_names_no_track() -> None:
    """`MAIN`, `PROG` and `JOIN` are what a track is *for*, not a district:
    reading one as a track would put a district on the railroad the hardware
    does not have."""
    assert replies.reply(b"<p1 MAIN>") is None
    assert replies.reply(b"<p1 JOIN>") is None


def test_the_lock_is_read_off_what_the_station_broadcasts() -> None:
    assert replies.reply(b"<!PAUSED>") == replies.Lock(locked=True)
    assert replies.reply(b"<!RESUMED>") == replies.Lock(locked=False)


def test_the_banner_reads_as_nothing() -> None:
    """The banner names the build the station runs, and this app reads none
    of it: the build left the contract with the mirror (#567). The banner
    still raises the link, the station having answered, but that is the
    translator's reading and not a fact out of this line."""
    assert (
        replies.reply(
            b"<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>"
        )
        is None
    )
    assert replies.reply(b"<iDCC-EX>") is None
    assert replies.reply(b"<i>") is None


def test_a_turnout_the_station_reports_reads_as_one() -> None:
    """The station keeps turnouts of its own and this app commands none of
    them, so the position is one it faked and reaches no bus row. It is read
    because a script may be keyed on it (ADR-0013 d.3)."""
    assert replies.reply(b"<H 12 1>") == replies.Turnout(point="12", thrown=True)
    assert replies.reply(b"<H 12 0>") == replies.Turnout(point="12", thrown=False)


def test_a_turnout_line_of_another_shape_reads_as_nothing() -> None:
    """The station's longer `<H>` forms carry a description or a word where
    the digit goes, and this app reads neither: a line it does not recognise
    is the ordinary case here."""
    for other in (b"<H 12>", b"<H 12 T>", b"<H 12 1 Yard ladder>", b"<H>"):
        assert replies.reply(other) is None


def test_everything_else_on_the_port_reads_as_nothing() -> None:
    for other in (
        b"<l 3 0 128 0>",
        b"<Q 7>",
        b"<jI 250 0>",
        b"<>",
    ):
        assert replies.reply(other) is None
