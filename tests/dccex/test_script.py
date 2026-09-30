"""A railroad's script, loaded from its text: the handlers it registers and
the events each is keyed on.

Loading takes the **text** and never a path or a store, which is what lets a
test hand over three lines and the translator hand over what the store
answered (ADR-0015 d.2). What a handler is given is the translator's and is
asserted where the bytes are (`test_translator.py`); here a handler is handed
a list and appends its name to it, so what is under test is the keying alone.
"""

import pytest

from dccex import sample, script

POWER = """\
@on("power")
def power(t):
    t.append("power")
"""


def test_a_handler_is_keyed_on_the_event_its_decorator_names() -> None:
    """`on(row, address)` is the whole of the registration, and the script's
    own word for the track's power is `power`."""
    ran: list[str] = []
    script.load(POWER).handlers("power")[0](ran)
    assert ran == ["power"]


TWO = """\
@on("point", "20")
@on("point", "21")
def signal_5(t):
    t.append("signal_5")
"""


def test_one_handler_takes_two_events() -> None:
    """A signal set from two turnouts is one function keyed twice: the
    decorator hands the function back, so they stack."""
    loaded = script.load(TWO)
    ran: list[str] = []
    loaded.handlers("point", "20")[0](ran)
    loaded.handlers("point", "21")[0](ran)
    assert ran == ["signal_5", "signal_5"]
    assert loaded.handlers("point", "12") == []


EVERY = """\
@on("traction")
def every(t):
    t.append("every")


@on("traction", "460")
def one(t):
    t.append("one")
"""


def test_a_handler_with_no_address_runs_for_every_address_of_its_row() -> None:
    """An address left out is every one of them, and a handler keyed on one
    address does not stop it: two handlers on an event are two things a
    script asked for, in the order it registered them."""
    loaded = script.load(EVERY)
    ran: list[str] = []
    for handler in loaded.handlers("traction", "460"):
        handler(ran)
    assert ran == ["every", "one"]
    other: list[str] = []
    for handler in loaded.handlers("traction", "3"):
        handler(other)
    assert other == ["every"]


def test_a_row_that_is_no_event_does_not_load() -> None:
    """A typo is caught at load, where the translator says it on its link
    row, rather than becoming a handler that never fires."""
    with pytest.raises(ValueError, match="turnout"):
        script.load('@on("turnout", "12")\ndef p(t):\n    pass\n')


def test_an_address_that_is_not_a_string_does_not_load() -> None:
    """An address is the string the bus carries (control ADR-0059), so a
    number is refused rather than quietly matching nothing."""
    with pytest.raises(TypeError, match="12"):
        script.load('@on("point", 12)\ndef p(t):\n    pass\n')


def test_what_the_text_raises_comes_out_of_the_load() -> None:
    """A script is a person's Python and may raise anything at all. Nothing
    is caught here: the translator is what runs with no handlers and says
    why (ADR-0015 d.4)."""
    with pytest.raises(ZeroDivisionError):
        script.load("1 / 0\n")


def test_a_script_with_no_handlers_loads() -> None:
    """A railroad whose document is empty is a railroad the translator sends
    its own commands for."""
    assert script.load("# nothing yet\n").handlers("power") == []


def test_the_sample_registers_the_events_it_names() -> None:
    """The sample is the interface, and loading it is the first thing asked
    of a script: four handlers on five events, one function keyed twice, and
    a helper the handlers call rather than a handler of its own.

    What each one sends is asserted where the bytes are
    (`test_translator.py`).
    """
    loaded = script.load(sample.TEXT)
    assert [handler.__name__ for handler in loaded.handlers("power")] == ["power"]
    assert [handler.__name__ for handler in loaded.handlers("point", "12")] == [
        "point_12"
    ]
    assert [handler.__name__ for handler in loaded.handlers("point", "20")] == [
        "signal_5"
    ]
    assert [handler.__name__ for handler in loaded.handlers("point", "21")] == [
        "signal_5"
    ]
    assert loaded.handlers("point", "5") == []
    assert loaded.handlers("reported_point", "12") == []
