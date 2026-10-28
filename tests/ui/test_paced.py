"""What the box at the foot sends, and when (#357).

The station handles one PROG command at a time. While a `<W>`, `<V>`, `<B>`,
`<R>` or `<r>` waits for its ack it answers any other one of these with `<X>`
(`stashBusy`, `CommandStation-EX/DCCEXParser.cpp`), so a list of CV writes
sent at once loses every command after the first.

How typing is split into a list, what goes next, and when a list stops are
`ui/src/paced.js`'s, a pure function of what it is handed. The cases go
through it under `node`, by way of `tests/ui/paced.mjs`, as `message.js`'s do
(`tests/ui/test_message.py`). The page holds the state and the clock
(`dccex-app.ts`).
"""

from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import HELD, ran
from tests.ui.paths import UI
from tests.ui.test_stream import code

#: The rules.
PACED = UI / "src" / "paced.js"

#: What puts the cases through them.
RUNNER = Path(__file__).resolve().parent / "paced.mjs"

#: The list from the issue, pasted into an `<input>` as Chrome joins it.
PASTED = "<W 32 0><W 263 128><W 271 128><W 279 128><W 287 128>"

#: Typing, and the messages it is split into.
LISTED: dict[str, list[str]] = {
    "<W 32 0> <W 263 128> <W 271 128>": ["<W 32 0>", "<W 263 128>", "<W 271 128>"],
    PASTED: [
        "<W 32 0>",
        "<W 263 128>",
        "<W 271 128>",
        "<W 279 128>",
        "<W 287 128>",
    ],
    " <s>  <R> ": ["<s>", "<R>"],
    "<s><>< ><R>": ["<s>", "<R>"],
    # Not a list: one message, through `message()` as before.
    "s": ["<s>"],
    "<s>": ["<s>"],
    "<W 32 0": ["<W 32 0>"],
    # No brackets: never split.
    "W 32 0 W 263 128": ["<W 32 0 W 263 128>"],
    # A `>` then `<` inside, but not opened and closed: not a list.
    "s> <R": ["<s> <R>"],
    "<s> <R": ["<s> <R>"],
    # Nothing.
    "": [],
    "<>": [],
    "<> <>": [],
}

#: Typing, and what ↑ brings back for it: the whole typed text for a list.
RECALLED: dict[str, str | None] = {
    "s": "<s>",
    " <s> ": "<s>",
    PASTED: PASTED,
    " <W 32 0> <W 263 128> ": "<W 32 0> <W 263 128>",
    "": None,
    "<>": None,
}


def asked(asks: list[Any]) -> list[Any]:
    """What the rules answer to `asks`, in one running of them."""
    return ran(RUNNER, asks, "the box's pacing")


def run(*steps: dict[str, Any]) -> list[dict[str, str]]:
    """What went up, and the notes put in, for `steps`."""
    return asked([{"run": list(steps)}])[0]


def sent(*messages: str) -> list[dict[str, str]]:
    return [{"sent": message} for message in messages]


@pytest.mark.node
def test_typing_is_split_into_a_list_only_where_it_is_one() -> None:
    answers = asked([{"listed": typed} for typed in LISTED])
    assert dict(zip(LISTED, answers, strict=True)) == LISTED


@pytest.mark.node
def test_up_recalls_the_whole_typed_text_as_one_entry() -> None:
    answers = asked([{"recalled": typed} for typed in RECALLED])
    assert dict(zip(RECALLED, answers, strict=True)) == RECALLED


@pytest.mark.node
def test_a_list_of_writes_goes_up_one_reply_at_a_time() -> None:
    assert run(
        {"typed": PASTED},
        {"heard": "<p1>"},
        {"heard": "<r 32 0>"},
        {"heard": "<r 263 128>"},
        {"heard": "<r 271 128>"},
        {"heard": "<r 279 128>"},
    ) == sent("<W 32 0>", "<W 263 128>", "<W 271 128>", "<W 279 128>", "<W 287 128>")


@pytest.mark.node
def test_a_command_that_waits_for_nothing_is_followed_right_away() -> None:
    assert run({"typed": "<s> <1 MAIN> <V 1 3> <s>"}) == sent(
        "<s>", "<1 MAIN>", "<V 1 3>"
    )


@pytest.mark.node
@pytest.mark.parametrize("command", ["<W 1 3>", "<V 1 3>", "<B 1 2 1>", "<R>", "<r 1>"])
def test_every_prog_command_waits_for_its_reply(command: str) -> None:
    assert run({"typed": f"{command} <s>"}) == sent(command)
    assert run({"typed": f"{command} <s>"}, {"heard": "<v 1 3>"}) == sent(
        command, "<s>"
    )


@pytest.mark.node
def test_a_reply_ending_in_minus_one_stops_the_list() -> None:
    assert run(
        {"typed": "<W 32 0> <W 263 128> <W 271 128> <W 279 128>"},
        {"heard": "<r 32 0>"},
        {"heard": "<r 263 -1>"},
        {"heard": "<r 271 128>"},
    ) == [
        *sent("<W 32 0>", "<W 263 128>"),
        {"note": "2 commands not sent: the station answered <r 263 -1>"},
    ]


@pytest.mark.node
def test_an_x_stops_the_list() -> None:
    assert run({"typed": "<W 32 0> <W 263 128>"}, {"heard": "<X>"}) == [
        *sent("<W 32 0>"),
        {"note": "1 command not sent: the station answered <X>"},
    ]


@pytest.mark.node
def test_no_reply_stops_the_list() -> None:
    assert run({"typed": "<R> <W 1 3> <s>"}, {"silent": True}) == [
        *sent("<R>"),
        {"note": "2 commands not sent: no reply within 10 s"},
    ]


@pytest.mark.node
def test_the_stream_closing_stops_the_list() -> None:
    assert run({"typed": "<R> <W 1 3>"}, {"closed": True}) == [
        *sent("<R>"),
        {"note": "1 command not sent: the stream closed"},
    ]


@pytest.mark.node
def test_a_stop_with_nothing_left_says_nothing_and_the_next_typing_goes() -> None:
    assert run(
        {"typed": "<W 32 0>"},
        {"heard": "<r 32 -1>"},
        {"typed": "<R>"},
    ) == sent("<W 32 0>", "<R>")


@pytest.mark.node
def test_a_reply_that_comes_while_nothing_waits_stops_nothing() -> None:
    assert run({"heard": "<X>"}, {"typed": "<s> <R>"}) == sent("<s>", "<R>")


@pytest.mark.node
def test_typing_while_a_list_runs_waits_behind_it() -> None:
    assert run(
        {"typed": "<W 32 0> <W 263 128>"},
        {"typed": "s"},
        {"heard": "<r 32 0>"},
        {"heard": "<r 263 128>"},
    ) == sent("<W 32 0>", "<W 263 128>", "<s>")


@pytest.mark.node
def test_typing_behind_a_list_that_stops_is_not_sent_either() -> None:
    assert run(
        {"typed": "<W 32 0> <W 263 128>"},
        {"typed": "<W 1 3>"},
        {"heard": "<X>"},
    ) == [
        *sent("<W 32 0>"),
        {"note": "2 commands not sent: the station answered <X>"},
    ]


def test_the_rules_hold_nothing() -> None:
    """No clock, no timer and no DOM: the ten seconds are the page's."""
    source = code(PACED.read_text())
    for held in HELD:
        assert held not in source, f"the rules reach {held}"
