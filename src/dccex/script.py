"""A railroad's **script**, loaded from its text: the handlers, and the event
each one is keyed on.

The script is where this railroad's `<…>` that the bus has no word for is
written — which mode a track is set to, what current it may draw, what a
turnout throwing does to a track or a signal (ADR-0013, ADR-0015). It is a
railroad's document in `control`'s store, one per railroad, and what is here
is the loading of it: text in, a `Script` out, or whatever the text raised.

**Text and never a path.** Loading takes what the store answered, so the
tests hand over the sample directly and nothing here reaches a store or a
file (ADR-0015 d.2, `store.py`).

**The names a script is written with are injected and not imported.** `on` is
the only one, put in the globals the text runs in, so a railroad's document
is the handlers and nothing above them — no import line, and no name of this
package in a document a person edits on a page.

Pure: no socket, no bus and no clock. What a handler is handed when it runs is
the translator's (`translator.Event`), which is where `default()`, `send()`
and the two pictures are, and a handler that raises is the translator's
business as well (ADR-0013 d.8, as amended by ADR-0015 d.4).
"""

from collections.abc import Callable
from typing import Any, cast

ROW_POWER = "power"
ROW_POINT = "point"
ROW_SIGNAL = "signal"
ROW_TRACTION = "traction"
ROW_FUNCTION = "function"

REPORTED_POWER = "reported_power"
REPORTED_POINT = "reported_point"

DESIRED_ROWS = (ROW_POWER, ROW_POINT, ROW_SIGNAL, ROW_TRACTION, ROW_FUNCTION)
"""The desired values a handler may be keyed on, in the script's own words. A
handler on one of these runs **in place of** the translator's command for it
(ADR-0013 d.2).

`power` is the track's, which the bus carries on `wanted/track`: what a
script is about is the railroad's power and the row's name on the bus is the
translator's business (`translator.SCRIPT_ROW`)."""

REPORTED_ROWS = (REPORTED_POWER, REPORTED_POINT)
"""What the station reported, which a handler runs after the fact of and
replaces nothing. Power and turnouts are the two; others are added when a
script needs one (ADR-0013 d.3)."""

ROWS = DESIRED_ROWS + REPORTED_ROWS

Handler = Callable[[Any], None]
"""A function in the script. It takes one argument — the event, which is
`translator.Event` when the translator runs it — and returns nothing; what it
returns is read nowhere."""

_Registration = tuple[str, str | None, Handler]


class Script:
    """The handlers one script's text registered, in the order it registered
    them.

    A script with no handlers at all is an ordinary script: a railroad whose
    document is empty, or has none for the value that fired, is one the
    translator sends its own commands for (ADR-0013 d.2).
    """

    def __init__(self) -> None:
        self._registered: list[_Registration] = []

    def on(self, row: str, address: str | None = None) -> Callable[[Handler], Handler]:
        """Register a handler on one event: the row, and the address on it.

        The name a script is written with, and the only one. The function is
        handed back unchanged, so two of these stack on one function and a
        handler stays a function the script's own code may call.

        `address` is left out where the row has one thing in it — `power` is
        the railroad's — and where a handler is to run for **every** address
        of its row. Given, it is the string the bus carries and the hardware
        answers to, as an address is everywhere else (control ADR-0059).

        A row this translator has no event for, or an address that is not a
        string, **raises**: a script that names one is a script that does not
        load, which the translator says on its link row rather than running
        with a handler that would never fire (ADR-0015 d.4).
        """
        if row not in ROWS:
            raise ValueError(f"'{row}' is no event: the rows are {', '.join(ROWS)}")
        # The call is a document's and not this package's, so the address is
        # read and never trusted whatever the signature says (BUS.md, rule 4).
        given = cast(object, address)
        if given is not None and not isinstance(given, str):
            raise TypeError(f"an address is a string, and {given!r} is not")

        def registers(handler: Handler) -> Handler:
            self._registered.append((row, address, handler))
            return handler

        return registers

    def handlers(self, row: str, address: str | None = None) -> list[Handler]:
        """Every handler one event fires, in the order the script registered
        them: those keyed on that address, and those keyed on the row with no
        address.

        All of them and not the first: two handlers on one turnout are two
        things that turnout does, and a script that registers both wants both
        (ADR-0013 d.5 — a handler sets everything it depends on and relies on
        no other).
        """
        return [
            handler
            for keyed, on, handler in self._registered
            if keyed == row and on in (None, address)
        ]


def load(text: str) -> Script:
    """The script that text is, or whatever the text raised.

    The text runs whole, once: a script is a Python document and its handlers
    are what running it registers. Nothing is caught here — a document that
    raises on load is one the translator has no handlers from, and it is the
    translator that says so on its link row and goes on asking (ADR-0015 d.4).

    The globals the text runs in are this script's own and carry `on` alone.
    They are what the script's module-level names land in, so a handler may
    call a helper written beside it, which is how one turnout's mode and a
    power-on's set the same thing from the same lines (the sample).
    """
    script = Script()
    names: dict[str, Any] = {"on": script.on}
    # The whole of what a script is: a person's Python, run once.
    exec(compile(text, "<script>", "exec"), names)  # noqa: S102
    return script
