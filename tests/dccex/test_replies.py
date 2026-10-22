"""What the station says, framed and read: the three facts, and everything
else.

The port carries the whole conversation — this app's replies, and every
broadcast meant for JMRI, a hand-held throttle or a browser — so most of what
is read here is somebody else's and reads as nothing at all (control#289).
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


def test_the_banner_reads_as_the_build_the_station_runs() -> None:
    """The `G-` field, which is the **build**. It reaches no row this app
    publishes — that went to the mirror's face with the flash (control#567) —
    and is read because every journal line carries it (ADR-0022 d.2)."""
    assert replies.reply(
        b"<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>"
    ) == replies.Banner(build="v5.6.4-rails49.1")


def test_a_banner_without_a_build_reads_as_nothing() -> None:
    """A banner this app can read no field off raises the link just the same,
    the station having answered, but that is the translator's reading and not
    a fact out of this line."""
    assert replies.reply(b"<iDCC-EX V-5.6.4 / ESP32>") is None
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


# -- a district the station cut itself (ADR-0016) -------------------------
#
# Each line as `MotorDriver.cpp` prints it, at fork tag
# `v5.6.4-rails49.6-ocp-test`: `%4M` pads the milliseconds to four places in
# the lines the retry prints, and the Guard's cut pads nothing.


def test_an_overload_is_a_trip() -> None:
    said = b"<* TRACK B POWER OVERLOAD 3120mA (max 3000mA) detected after    2ms. Pause   40ms *>"
    assert replies.reply(said) == replies.Diagnostic(track="B", kind=replies.TRIP)


def test_a_guard_cut_is_a_trip() -> None:
    said = b"<* TRACK B FAST OVERLOAD 4210mA. Pause 100ms *>"
    assert replies.reply(said) == replies.Diagnostic(track="B", kind=replies.TRIP)


def test_a_guard_cut_on_a_fault_pin_is_a_trip() -> None:
    said = b"<* TRACK B FAST OVERLOAD 4210mA FAULT PIN. Pause 100ms *>"
    assert replies.reply(said) == replies.Diagnostic(track="B", kind=replies.TRIP)


def test_a_fault_pin_is_a_trip() -> None:
    said = b"<* TRACK C FAULT PIN detected after    2ms. Pause   40ms) *>"
    assert replies.reply(said) == replies.Diagnostic(track="C", kind=replies.TRIP)


def test_a_fault_pin_that_is_ignored_is_nothing() -> None:
    assert replies.reply(b"<* TRACK C FAULT PIN (100ms ignore) *>") is None


def test_a_restore_is_a_retry() -> None:
    said = b"<* TRACK B POWER RESTORE (after   40ms) *>"
    assert replies.reply(said) == replies.Diagnostic(track="B", kind=replies.RESTORE)


def test_normal_ends_a_trip() -> None:
    said = b"<* TRACK B NORMAL (after 20ms/40ms) 180mA *>"
    assert replies.reply(said) == replies.Diagnostic(track="B", kind=replies.NORMAL)


def test_an_alert_is_a_rising_current() -> None:
    for said in (
        b"<* TRACK A ALERT  2900mA *>",
        b"<* TRACK A ALERT FAULT 2900mA *>",
        b"<* TRACK A ALERT FAULT *>",
    ):
        assert replies.reply(said) == replies.Diagnostic(track="A", kind=replies.ALERT)


def test_a_diagnostic_this_app_does_not_read_is_nothing() -> None:
    assert replies.reply(b"<* TRACK A INVERT *>") is None
    assert replies.reply(b"<* TRACK J NORMAL (after 20ms/40ms) 180mA *>") is None
    assert replies.reply(b"<* Calling EXRAIL *>") is None


# -- the stash a boot clears (ADR-0021) -----------------------------------


def test_the_stash_reads_as_held_or_as_empty() -> None:
    """`<JM id>` answers `<jM id loco>`, and `0` where the entry is unset,
    which every boot leaves it (`Stash.cpp`). The value itself names nothing
    here: anything that is not `0` is the mark this app set."""
    assert replies.reply(b"<jM 32000 1>") == replies.Stash(held=True)
    assert replies.reply(b"<jM 32000 0>") == replies.Stash(held=False)
    assert replies.reply(b"<jM 32000 3>") == replies.Stash(held=True)


def test_a_stash_that_is_not_this_app_s_reads_as_nothing() -> None:
    """One entry is this app's and the rest are EXRAIL's and other clients'
    (ADR-0021 d.1)."""
    for other in (
        b"<jM 1 0>",
        b"<jM 31999 0>",
        b"<jM 320000 0>",
        b"<jM 32000>",
        b"<jM 32000 x>",
        b"<jM>",
    ):
        assert replies.reply(other) is None


def test_the_boot_is_nothing() -> None:
    """The virtual LCD's text, row and port are part of no documented
    interface: a firmware that prints another form leaves a restart unseen,
    which is what happened on the first `<D RESET>` (ADR-0021)."""
    assert replies.reply(b'<@ 0 3 "Ready">') is None
    assert replies.reply(b"<* License GPLv3 fsf.org (c) dcc-ex.com *>") is None
    assert replies.reply(b'<@ 0 0 "DCC-EX v5.6.4">') is None
    assert replies.reply(b'<@ 0 3 "Free RAM=  312Kb">') is None


# -- what a track is set to and the most it may draw (ADR-0022 d.2) -------


def test_what_a_track_is_set_to_reads_as_the_mode() -> None:
    """The word the `<=` command takes, which is what a **script** writes:
    a DC track carries its cab after the mode and the cab is left on the
    line."""
    assert replies.reply(b"<= A MAIN>") == replies.Mode(track="A", mode="MAIN")
    assert replies.reply(b"<= B PROG>") == replies.Mode(track="B", mode="PROG")
    assert replies.reply(b"<= C DC 3>") == replies.Mode(track="C", mode="DC")
    assert replies.reply(b"<= H NONE>") == replies.Mode(track="H", mode="NONE")


def test_a_modifier_reads_as_the_word_the_command_takes_for_it() -> None:
    """MAIN and BOOST carry `A` for auto-reverse and `I` for inverted, and
    a reversed auto-reverse track carries both."""
    assert replies.reply(b"<= C MAIN A>") == replies.Mode(track="C", mode="MAIN_AUTO")
    assert replies.reply(b"<= C MAIN A I>") == replies.Mode(
        track="C", mode="MAIN_AUTO_INV"
    )
    assert replies.reply(b"<= D MAIN I>") == replies.Mode(track="D", mode="MAIN_INV")
    assert replies.reply(b"<= E BOOST A>") == replies.Mode(track="E", mode="BOOST_AUTO")
    assert replies.reply(b"<= E BOOST I>") == replies.Mode(track="E", mode="BOOST_INV")


def test_a_mode_line_of_another_shape_reads_as_nothing() -> None:
    for other in (b"<= Z MAIN>", b"<= A>", b"<= C MAIN X>", b"<= C PROG A>", b"<=>"):
        assert replies.reply(other) is None


def test_the_most_each_track_may_draw_reads_as_the_limits() -> None:
    """One line carries every track, A first, in milliamps."""
    assert replies.reply(b"<jG 1233 1233 250 250>") == replies.Limits(
        milliamps=(1233, 1233, 250, 250)
    )
    assert replies.reply(b"<jG 2000>") == replies.Limits(milliamps=(2000,))


def test_a_limit_line_of_another_shape_reads_as_nothing() -> None:
    """`<jI …>` is what each track is drawing rather than what it may, and is
    not read here."""
    for other in (b"<jG>", b"<jG A 2000>", b"<jI 13 2 0 0>"):
        assert replies.reply(other) is None


# -- what the journal keeps (ADR-0022 d.2) --------------------------------


def test_the_journal_keeps_every_track_diagnostic_and_the_district_it_names() -> None:
    """Wider than what this app acts on: a reverser flipping a district is a
    line the journal keeps and no fact here (d.3)."""
    assert replies.kept(b"<* TRACK C INVERT (fast) *>") == replies.Kept(
        district="C", power=False
    )
    assert replies.kept(
        b"<* TRACK B FAST OVERLOAD 4210mA. Pause 100ms *>"
    ) == replies.Kept(district="B", power=False)


def test_the_journal_keeps_a_power_line_that_names_a_district() -> None:
    """The district is read off it, and the line says it is a `<p…>`: the
    journal keeps one of those only where it says something different from
    the last one about the same district (ADR-0022 d.2 as amended)."""
    assert replies.kept(b"<p1 A>") == replies.Kept(district="A", power=True)
    assert replies.kept(b"<p0 C>") == replies.Kept(district="C", power=True)


def test_the_journal_keeps_no_power_line_that_names_no_district() -> None:
    """The bare `<p0>`/`<p1>` and the `MAIN`, `PROG` and `JOIN` lines. The
    station prints them in `broadcastPower()` alone, always after a `<pN X>`
    for each district, so they say nothing a line of the journal does not
    already carry (rails49/CommandStation-EX,
    `CommandDistributor::broadcastPower`, #269)."""
    for other in (b"<p0>", b"<p1>", b"<p1 MAIN>", b"<p0 PROG>", b"<p1 JOIN>"):
        assert replies.kept(other) is None


def test_the_journal_keeps_nothing_else_on_the_port() -> None:
    """The rest is another client's conversation, and the journal is what the
    station said about power (GLOSSARY.md, **journal**)."""
    for other in (
        b"<* Calling EXRAIL *>",
        b"<* License GPLv3 fsf.org (c) dcc-ex.com *>",
        b"<= A MAIN>",
        b"<jG 1233 1233 250 250>",
        b"<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>",
        b"<jM 32000 0>",
        b"<H 12 1>",
        b"<l 3 0 128 0>",
        b"<>",
    ):
        assert replies.kept(other) is None
