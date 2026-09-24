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

What cannot be run here is Lit. The gate is Python with a bare node in it and
no packages, so nothing in it can mount a component and press a button: the
words and the ordering are asserted here and the drawing of them is held
against the component's source below, which is the cost `tests/ui/test_look.py`
already names.
"""

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from tests.ui.test_look import UI
from tests.ui.test_stream import code

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
    node = shutil.which("node")
    assert node is not None, "no node on this machine to run the sequence with"
    ran = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(list(scenarios)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"the sequence did not run: {ran.stderr.strip()}"
    happened: list[dict[str, Any]] = json.loads(ran.stdout)
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


# -- what the page does -------------------------------------------------------


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


def test_the_stop_is_the_emergency_stop_and_the_cut_is_track_power() -> None:
    """Two whole `<…>` messages of the station's own, sent the way anything
    typed on this page is sent — so they are marked as the page's in the
    monitor and an operator can see what the sequence did (`message.js`,
    `dccex-app.ts`)."""
    assert words()["sends"] == {"STOPS": "<!>", "CUTS": "<0>"}


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


def test_a_step_that_did_not_leave_the_page_stops_the_sequence() -> None:
    """The stream is the only way anything reaches the station from here. A
    stop that did not go is a railroad nobody stopped, and a page that asked
    for a write after one would have done the one dangerous half of this."""
    assert flashed(tag=TAG, sends=0)["order"] == []
    assert flashed(tag=TAG, sends=1)["order"] == ["sent <!>"]


def test_a_sequence_that_stopped_says_so_and_was_not_written() -> None:
    """What an operator is told is that nothing was stopped and nothing was
    written, because a page that said nothing would leave them reading a list
    that had not changed (ADR-0009 d.2)."""
    happened = flashed(tag=TAG, sends=0)

    assert happened["wrote"] == {"flashed": False, "says": says()["UNSENT"]}
    assert "not" in says()["UNSENT"] and "written" in says()["UNSENT"]


def test_a_flash_that_cannot_start_says_why() -> None:
    """The face answers a refusal with a sentence — a tag with no release, a
    source that could not be asked, a release with no asset or no digest, a
    station that is not there, a flash already in flight — and the page says
    that sentence rather than one of its own (#9, `face.py`, ADR-0050)."""
    refused = {"flashed": False, "says": "a flash is already under way"}

    assert flashed(tag=TAG, wrote=refused)["wrote"] == refused


def test_a_flash_that_was_written_is_answered_and_then_observed() -> None:
    """Success is not replied to with a build: what is on the station is read
    off the station, on the banner it sends when it comes back (ADR-0006 d.3,
    ADR-0008 d.3)."""
    happened = flashed(tag=TAG)

    assert happened["wrote"]["flashed"] is True
    assert happened["wrote"]["says"] == says()["WROTE"]
    assert "build" in says()["WROTE"], "the page does not say where to look"


def test_the_operator_is_warned_what_flashing_does() -> None:
    """The guard is the person and a person can only be one if they are told
    what the gesture does (#9, ADR-0006 d.2)."""
    warning = says()["WARNS"]

    assert "resets the station" in warning
    assert "drops every throttle" in warning
    assert "minute" in warning


def test_the_yes_is_a_press_of_its_own() -> None:
    """A sequence the operator declines is a flash that was not asked for
    rather than one that was refused (ADR-0006 d.2), so there is something to
    decline: the choice, the warning, and then the gesture."""
    assert says()["CHOOSES"] and says()["CONFIRMS"] and says()["CANCELS"]
    assert says()["CHOOSES"] != says()["CONFIRMS"]


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
    else (ADR-0002), and what a caller may name is a **tag**: where releases
    are read from is the app's configuration, and a body that named a source
    would let anyone on the wifi choose what the command station is offered to
    run (ADR-0042, `firmware.py`)."""
    asking = code(FACE.read_text())
    assert "FLASH_PATH = `${FACE}/flash`" in asking, "the page builds no address"
    writing = asking[asking.index("export async function flash(") :]
    assert "fetch(FLASH_PATH, {" in writing
    assert "method: POST" in writing, "a flash is asked for with a GET"
    assert "JSON.stringify({ [TAG]: tag })" in writing, "the body names more"
    assert (
        'fetch("' not in writing and "fetch(`" not in writing
    ), "the page writes an address of its own rather than building one"


def test_a_flash_the_face_refused_is_said_in_the_face_s_own_words() -> None:
    """The mirror says what it turned a flash down for, and a page that wrote
    its own sentence over that would be guessing at an answer it was given
    (ADR-0050, `face.py`)."""
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
