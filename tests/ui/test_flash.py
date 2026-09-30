"""What the page does to the railroad before a release is written onto the
station.

Scenarios: the stream takes this many messages and the face answers this, so
the page sent these things in this order, showed these steps and came back
saying that. The sequence reaches nothing itself — what sends a message up the
**stream**, what asks the **face** to write and what shows a step are handed to
it (`ui/src/flash.js`) — which is what lets the whole of it be run on a machine
with no command station, no esptool and no browser.

**The ordering is run rather than read**, as the decoder's pairs and the band's
readings are (`tests/ui/test_decoder.py`, `tests/ui/test_readings.py`) and with
the same at stake as the box at the foot: these bytes go down the cable to a
command station, and a rule about what goes down a cable asserted against the
source that would produce it is not asserted. The scenarios go through the real
function under `node`, by way of `tests/ui/flash.mjs`.

**Nothing behind the page guards this** (ADR-0006). The mirror checks the tag,
the release, the digest, the device and whether it is already writing, and it
checks nothing about a railroad; the ordering below is where the care is, and
the operator is the guard. What the mirror does check is held at the other end,
with no command station and no esptool there either — the device closed before
the flash and reopened after it, `latest` refused, the binary checked against
the digest the release API reports before the device is let go, and a second
flash refused rather than queued (`tests/dccex_usb/test_firmware.py`,
`tests/dccex_usb/test_face.py`).

**And the gesture is pressed rather than read** (#126). The words and the
ordering are asserted here; that an operator choosing a release is warned,
presses again and then reads the three steps in the order the sequence runs
them is asserted by mounting the row in happy-dom and pressing it
(`ui/test/flash.test.ts`). What is still held against the source below is what
a press does not reach: the one place a second sequence is refused after the
controls have already gone dead.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import ran
from tests.ui.test_look import UI
from tests.ui.test_stream import code, quoted

#: The sequence, and the module it is the whole of.
FLASH = UI / "src" / "flash.js"

#: What puts a scenario through it.
RUNNER = Path(__file__).resolve().parent / "flash.mjs"

#: The row a release is chosen on.
LIST = UI / "src" / "ui" / "dccex-releases.ts"

#: The page that hands it what it flashes with.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: Where the page asks the mirror to write one.
FACE = UI / "src" / "face.ts"

#: The release the scenarios flash, unless one says otherwise.
TAG = "v5.6.4-rails49.1"


def run(scenarios: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """What the page did, for each of `scenarios`, in one running."""
    happened: list[dict[str, Any]] = ran(RUNNER, list(scenarios), "the sequence")
    return tuple(happened)


def flashed(**scenario: Any) -> dict[str, Any]:
    """What the page did, for one scenario."""
    return run((scenario,))[0]


@lru_cache(maxsize=1)
def words() -> dict[str, Any]:
    """The words the page can say and the messages it sends, as the module
    exports them."""
    return flashed()


def says() -> dict[str, str]:
    """The sentences the page can say about a flash."""
    said: dict[str, str] = words()["says"]
    return said


def progress(answer: Any) -> dict[str, Any] | None:
    """What the page's reader makes of one `flashing` answer."""
    read: dict[str, Any] | None = flashed(flashing=answer)["progress"]
    return read


def bar(answer: Any) -> dict[str, Any] | None:
    """What the bar over that answer reads, and how full it is."""
    shown: dict[str, Any] | None = flashed(flashing=answer)["bar"]
    return shown


# -- what the page does -------------------------------------------------------


@pytest.mark.node
def test_the_locomotives_are_stopped_and_the_power_cut_before_the_write() -> None:
    """The order the railroad depends on (#9, ADR-0006 d.2): everything moving
    is stopped, the rails are dropped, and only then is the station taken away
    to be written.

    The stop is first because a locomotive coasting on dead rails is what is
    left if the power goes under it, and the write is last because it is the
    step the station does not come back from for a minute or two.
    """
    happened = flashed(tag=TAG)

    assert happened["order"] == ["sent <!>", "sent <0>", f"wrote {TAG}"]


@pytest.mark.node
def test_the_stop_is_the_emergency_stop_and_the_cut_is_track_power() -> None:
    """Two whole `<…>` messages of the station's own, sent the way anything
    typed on this page is sent — so they are marked as the page's in the
    monitor and an operator can see what the sequence did (`message.js`,
    `dccex-app.ts`)."""
    assert words()["sends"] == {"STOPS": "<!>", "CUTS": "<0>"}


@pytest.mark.node
def test_the_page_says_which_step_is_running() -> None:
    """A minute of silence reads as a hang, and the last step is a minute or
    two of the station being away (#9)."""
    happened = flashed(tag=TAG)

    assert happened["shown"] == [
        says()["STOPPING"],
        says()["CUTTING"],
        happened["writing"],
    ]
    assert TAG in happened["writing"], "the step does not say which release"
    assert "minute" in happened["writing"], "the step does not say how long"


@pytest.mark.node
def test_a_step_that_did_not_leave_the_page_stops_the_sequence() -> None:
    """The stream is the only way anything reaches the station from here. A
    stop that did not go is a railroad nobody stopped, and a page that asked
    for a write after one would have done the one dangerous half of this."""
    assert flashed(tag=TAG, sends=0)["order"] == []
    assert flashed(tag=TAG, sends=1)["order"] == ["sent <!>"]


@pytest.mark.node
def test_a_stop_that_did_not_go_says_nothing_was_done_and_nothing_written() -> None:
    """What an operator is told is that nothing was stopped and nothing was
    written, because a page that said nothing would leave them reading a list
    that had not changed (ADR-0009 d.2). Nothing left the page, so nothing was
    done to the railroad either."""
    happened = flashed(tag=TAG, sends=0)
    said = says()["UNSTOPPED"]

    assert happened["wrote"] == {"flashed": False, "says": said}
    assert "the locomotives were not stopped" in said
    assert "nothing was written" in said


@pytest.mark.node
def test_a_cut_that_did_not_go_says_the_locomotives_are_stopped_and_the_power_on() -> (
    None
):
    """The stop went and the cut did not, which is the state of the railroad
    this page must not be wrong about (#93): the locomotives are stopped and
    the rails are still hot.

    ADR-0006 makes the operator the only guard on a flash, so what the page
    says about the railroad is the whole of what the guard has to go on — and a
    sentence saying the locomotives were not stopped, said while they are,
    sends that person to a railroad they think is untouched.
    """
    happened = flashed(tag=TAG, sends=1)
    said = says()["UNCUT"]

    assert happened["wrote"] == {"flashed": False, "says": said}
    assert said != says()["UNSTOPPED"], "both steps are said the same way"
    assert "the locomotives are stopped" in said
    assert "not stopped" not in said, "the step that went is denied"
    assert "the power is still on" in said, "the rails read as dropped"
    assert "nothing was written" in said


@pytest.mark.node
def test_a_flash_that_cannot_start_says_why() -> None:
    """The face answers a refusal with a sentence — a tag with no release, a
    source that could not be asked, a release with no asset or no digest, a
    station that is not there, a flash already in flight — and the page says
    that sentence rather than one of its own (#9, `face.py`, control
    ADR-0050)."""
    refused = {"flashed": False, "says": "a flash is already under way"}

    assert flashed(tag=TAG, wrote=refused)["wrote"] == refused


@pytest.mark.node
def test_a_flash_that_was_written_waits_for_the_station() -> None:
    """Success is not replied to with a build: the write is over and what is on
    the station is read off the station, on the banner it sends when it comes
    back (ADR-0006 d.3, ADR-0008 d.3, ADR-0012 d.4).

    So the answer to the POST is not the end of it. The page says it is waiting
    for the station until the station says which **build** it is running, and
    there is nothing else it can truthfully say in that minute.
    """
    happened = flashed(tag=TAG)

    assert happened["wrote"]["flashed"] is True
    assert happened["wrote"]["says"] == says()["WAITING"]
    assert happened["became"] == {"landed": None, "says": says()["WAITING"]}


@pytest.mark.node
def test_a_station_running_the_tag_is_the_flash_that_landed() -> None:
    """The **build** off the banner is the tag that was written, which is the
    one thing that says the flash landed — read off the station and not off the
    mirror's answer (ADR-0006 d.3, ADR-0012 d.4)."""
    happened = flashed(tag=TAG, build=TAG)

    assert happened["became"]["landed"] is True
    assert TAG in happened["became"]["says"]


@pytest.mark.node
def test_a_build_that_differs_from_the_tag_is_a_failure() -> None:
    """The station came back running something else, whatever the mirror
    answered (ADR-0012 d.4). Both are named, because which build came back is
    what whoever fixes it has to go on."""
    happened = flashed(tag=TAG, build="v5.6.3-rails49.2")

    assert happened["became"]["landed"] is False
    assert TAG in happened["became"]["says"]
    assert "v5.6.3-rails49.2" in happened["became"]["says"]


@pytest.mark.node
def test_a_refusal_is_what_became_of_it_whatever_the_station_is_running() -> None:
    """Nothing was written, so the build on the station is not about this
    gesture: what the operator reads is the refusal, and a station that is up
    and running the same release it always was does not turn one into a flash
    that landed."""
    happened = flashed(tag=TAG, sends=0, build="v5.6.3-rails49.2")

    assert happened["became"] == {"landed": False, "says": says()["UNSTOPPED"]}


@pytest.mark.node
def test_the_operator_is_warned_what_flashing_does() -> None:
    """The guard is the person and a person can only be one if they are told
    what the gesture does (#9, ADR-0006 d.2)."""
    warning = says()["WARNS"]

    assert "resets the station" in warning
    assert "drops every throttle" in warning
    assert "minute" in warning


@pytest.mark.node
def test_the_yes_is_a_press_of_its_own() -> None:
    """A sequence the operator declines is a flash that was not asked for
    rather than one that was refused (ADR-0006 d.2), so there is something to
    decline: the choice, the warning, and then the gesture."""
    assert says()["CHOOSES"] and says()["CONFIRMS"] and says()["CANCELS"]
    assert says()["CHOOSES"] != says()["CONFIRMS"]


# -- how far it has got -------------------------------------------------------


@pytest.mark.node
def test_the_stages_are_the_four_the_face_names() -> None:
    """In the flash's own order, and spelt as the mirror spells them: they are
    read off the wire and drawn as they arrive, so a page with a list of its own
    would be a page glossing the face (ADR-0012 d.2, `firmware.py`'s
    `Stage`)."""
    assert words()["stages"] == ["fetching", "checking", "writing", "verifying"]


@pytest.mark.node
def test_a_flash_in_flight_is_the_tag_the_stage_and_the_percentage() -> None:
    """The three the face answers under `flashing` (ADR-0012 d.2, `face.py`'s
    `progress()`)."""
    assert progress({"tag": TAG, "stage": "writing", "percent": 42}) == {
        "tag": TAG,
        "stage": "writing",
        "percent": 42,
    }


@pytest.mark.node
def test_no_flash_running_reads_as_no_flash_running() -> None:
    """The ordinary answer on a box where nobody is writing the station, and
    the one key the face puts it under carries `null` for it."""
    assert progress(None) is None


@pytest.mark.node
def test_an_answer_the_page_cannot_read_reads_as_no_flash() -> None:
    """Read one field at a time, as the releases are, because this arrives from
    another app over a wire (`releases.js`'s `carried()`): an answer that names
    no tag or no stage is not a flash this page can say anything about, and a
    bar over it would be a reading nobody made (ADR-0009 d.2)."""
    for answer in (
        {},
        {"stage": "writing", "percent": 42},
        {"tag": "", "stage": "writing"},
        {"tag": TAG},
        {"tag": TAG, "stage": ""},
        "writing",
        7,
        [],
        True,
    ):
        assert progress(answer) is None, f"{answer!r} reads as a flash in flight"


@pytest.mark.node
def test_a_stage_the_page_has_no_word_for_is_the_face_s_word() -> None:
    """A mirror that names a fifth stage is a flash that is running, and a page
    that answered no flash for it would be hiding one it was told about. The
    word it was given is not a guess; a bar that does not count is what stands
    under it (ADR-0009 d.2, d.5)."""
    assert progress({"tag": TAG, "stage": "wiping", "percent": None}) == {
        "tag": TAG,
        "stage": "wiping",
        "percent": None,
    }


@pytest.mark.node
def test_the_bar_counts_the_writing_and_says_how_far() -> None:
    """One bar with a stage label: the writing is what esptool counts, so that
    is the stage the bar fills for and the only one with a number beside it
    (ADR-0012 d.1, d.2)."""
    assert bar({"tag": TAG, "stage": "writing", "percent": 42}) == {
        "says": "writing 42 %",
        "percent": 42,
    }


@pytest.mark.node
def test_the_stages_nothing_counts_are_a_bar_that_does_not() -> None:
    """Nothing counts a fetch, a hash or a verify, so the bar over them reads
    the stage and runs without a number: a bar drawn at a percentage nobody
    measured is a reading nobody took (ADR-0009 d.2, `firmware.py`)."""
    for stage in ("fetching", "checking", "verifying"):
        assert bar({"tag": TAG, "stage": stage, "percent": None}) == {
            "says": stage,
            "percent": None,
        }


@pytest.mark.node
def test_a_writing_with_no_percentage_the_page_can_read_does_not_count() -> None:
    """esptool has not printed one yet, or the number is not one a bar can be
    drawn at. The stage is still the stage; what goes is the count."""
    for percent in (None, "42", 140, -1, True):
        assert bar({"tag": TAG, "stage": "writing", "percent": percent}) == {
            "says": "writing",
            "percent": None,
        }, f"{percent!r} is drawn as a percentage"


@pytest.mark.node
def test_a_bar_over_no_flash_is_no_bar() -> None:
    """Nothing is running, so there is nothing to draw: a bar left standing
    would say the station was being written."""
    assert bar(None) is None


# -- what the row draws -------------------------------------------------------


@pytest.mark.node
def test_every_word_the_row_says_about_a_flash_is_the_sequence_s() -> None:
    """So that what an operator reads is asserted by running the sequence
    rather than by reading the component, which is the whole reason the
    sentences live in a module a bare node can run."""
    sentences = set(says().values())
    for literal in quoted(LIST.read_text()):
        assert literal not in sentences, f"the row writes {literal!r} out again"


def test_a_second_sequence_is_refused_after_the_controls_have_gone_dead() -> None:
    """A second flash is a second station reset, and what the mirror does with
    one asked for anyway is refuse it rather than queue it (`firmware.py`).

    That there is nothing to press while a step is showing is the mounted
    check's (`ui/test/flash.test.ts`). This is the belt under it: the step is
    set before the sequence's first `await`, so two presses in one turn cannot
    both pass the check — the same reason the mirror reads its own flag where
    nothing is awaited after it. Two presses in one turn is not a gesture a
    mounted check can make, because the first of them takes the control off
    the page.
    """
    drawn = code(LIST.read_text())
    flashing = drawn[drawn.index("async #flashes(") :]
    assert flashing.index("if (this.step !== null)") < flashing.index(
        "await sequence("
    ), "a second sequence starts before the first is looked for"


def test_the_page_hands_the_row_its_stream_and_its_face() -> None:
    """A pane holding a counterparty of its own would be a second answer to
    what the page talks to (the organisation's ADR-0002).

    The stop and the cut go up the same `send` an operator's typing goes up, so
    they are marked as this page's in the monitor and an operator can see what
    the sequence did; the face is asked by the page's own `flash`, through the
    page's own hand — which is what also starts the following of the write
    (ADR-0012 d.3, `tests/ui/test_page.py`).
    """
    app = code(APP.read_text())
    assert 'import { flash, flashing, releases } from "../face.js";' in app
    assert ".sends=${this.#sends}" in app, "the row is handed no stream"
    assert ".writes=${this.#writes}" in app, "the row is handed no face"
    writing = app[app.index("#writes = async (") :]
    assert "await flash(tag)" in writing, "the page asks nobody to write"


# -- what the sequence is -----------------------------------------------------


def test_the_sequence_reaches_nothing_of_its_own() -> None:
    """No socket, no face, no clock and no DOM: everything it does is handed
    to it, which is what lets the ordering above be run with none of them in
    reach (ADR-0009 d.1)."""
    written = code(FLASH.read_text())
    for held in ("fetch(", "WebSocket", "document", "window", "setTimeout"):
        assert held not in written, f"the sequence reaches {held}"


# -- what the page asks -------------------------------------------------------


def test_the_page_asks_its_own_face_to_write_and_names_only_the_tag() -> None:
    """A UI talks to the bus, the store and its own app's face and nothing
    else (the organisation's ADR-0002), and what a caller may name is a
    **tag**: where releases are read from is the app's configuration, and a
    body that named a source would let anyone on the wifi choose what the
    command station is offered to run (control ADR-0042, `firmware.py`)."""
    asking = code(FACE.read_text())
    assert "FLASH_PATH = `${FACE}/flash`" in asking, "the page builds no address"
    writing = asking[asking.index("export async function flash(") :]
    assert "fetch(FLASH_PATH, {" in writing
    assert "method: POST" in writing, "a flash is asked for with a GET"
    assert "JSON.stringify({ [TAG]: tag })" in writing, "the body names more"
    assert (
        'fetch("' not in writing and "fetch(`" not in writing
    ), "the page writes an address of its own rather than building one"


def test_the_page_asks_the_face_how_far_a_flash_has_got() -> None:
    """At the same address a flash is asked for, with a GET (ADR-0012 d.2, d.3).

    Two things on that path and no third: a POST writes the station and a GET
    says what the writing has come to, so a page that asked how far it had got
    cannot write anything by asking. The answer is read by the module a bare
    node runs, as a `releases` document is (`flash.js`'s `progress()`).
    """
    asking = code(FACE.read_text())
    following = asking[asking.index("export async function flashing(") :]
    assert "fetch(FLASH_PATH)" in following, "the page builds the address it asks"
    assert "method:" not in following, "the read is not a plain GET"
    assert "progress(" in following, "the page reads the answer some other way"
    assert (
        'fetch("' not in following and "fetch(`" not in following
    ), "the page writes an address of its own rather than building one"


def test_a_face_that_did_not_say_how_far_reads_as_no_flash_running() -> None:
    """A face that is away, a status that is not a 200, an answer this page
    cannot read: `null`, and no bar is drawn.

    Nothing running and nothing said read alike, which is the one place the
    page draws that line the short way: what it does with either is draw no
    bar, and whether a write of its own is in flight is what the POST's answer
    says (`flash.js`'s `progress()`, ADR-0009 d.2).
    """
    asking = code(FACE.read_text())
    following = asking[asking.index("export async function flashing(") :]
    assert "Promise<Flashing | null>" in asking, "a face that is away raises"
    assert "} catch {" in following, "a face that is away takes the page with it"
    assert following.count("return null;") >= 2


@pytest.mark.node
def test_a_flash_the_face_refused_is_said_in_the_face_s_own_words() -> None:
    """The mirror says what it turned a flash down for, and a page that wrote
    its own sentence over that would be guessing at an answer it was given
    (control ADR-0050, `face.py`)."""
    asking = code(FACE.read_text())
    writing = asking[asking.index("export async function flash(") :]
    assert "REASON" in writing, "the refusal the face gave is dropped"
    assert says()["UNANSWERED"] not in writing, "every refusal reads as no answer"


def test_a_face_that_did_not_answer_reads_as_nothing_said() -> None:
    """A face that is away, or an answer this page cannot read: the sequence
    says the mirror could not be asked rather than that the station was not
    written, because a page that could not read an answer did not get one
    (ADR-0009 d.2)."""
    asking = code(FACE.read_text())
    writing = asking[asking.index("export async function flash(") :]
    assert "Promise<Wrote>" in writing, "a face that is away raises"
    assert "} catch {" in writing, "a face that is away takes the page with it"
    assert writing.count("UNANSWERED") >= 2
