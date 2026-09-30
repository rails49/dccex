"""The script the store holds for one railroad, read over its face.

Against a fake store on loopback (`tests/stores.py`): the routes are
`control`'s and a test here runs against a fake of them rather than a copy of
the store (ADR-0014, consequences; rails49/control#586).

What is under test is the one reading the translator makes of an answer — the
text, no script at all, or a store that did not answer — because those three
are what it does three different things about (ADR-0015 d.4).
"""

import pytest

from dccex.store import Scripts, Unanswered
from tests.stores import Store

SCRIPT = '@on("power")\ndef power(t):\n    t.default()\n'


def test_the_script_the_store_holds_is_its_text(store: Store) -> None:
    store.holds("bench", SCRIPT)
    store.opens()
    assert Scripts(store.url).text("bench") == SCRIPT


def test_a_railroad_with_no_script_reads_as_none(store: Store) -> None:
    """`404` is an answer and not an outage: the railroad has no script and
    the translator runs with the defaults (ADR-0015 d.4)."""
    store.opens()
    assert Scripts(store.url).text("bench") is None


def test_a_store_that_is_not_there_is_unanswered(store: Store) -> None:
    """Nothing listening, which is the ordinary state of a box whose store
    has not come up yet."""
    with pytest.raises(Unanswered):
        Scripts(store.url).text("bench")


def test_a_store_that_answers_with_no_text_is_unanswered(store: Store) -> None:
    """A document of a shape this app cannot read is a store that has not
    answered this request: it is read and never trusted, like any payload."""
    store.opens()
    store.scripts["bench"] = 12
    with pytest.raises(Unanswered):
        Scripts(store.url).text("bench")


def test_the_railroad_is_one_level_of_the_route(store: Store) -> None:
    """A railroad called `a/b` is a name the store does not have rather than
    a route of its own, which is what escaping it a level at a time buys."""
    store.opens()
    assert Scripts(store.url).text("a/b") is None
    assert store.asked == ["a%2Fb"]
