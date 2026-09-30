"""The store's routes as the face reaches them: the railroads there are, and
one railroad's **script** read and written.

Against a fake store on loopback (`tests/stores.py`): the routes are
`control`'s and a test here runs against a fake of them rather than a copy of
the store (ADR-0014, consequences; rails49/control#586). Nothing reaches a
network, and the fake is the same one the translator's own reader is asserted
against — one fake of `control`'s routes for both ends of this repository.

What is under test is the readings the face makes of an answer, because the
face does something different about each: the names, a railroad's text, a
railroad with no script, and a store that did not answer (`face.py`).
"""

import asyncio

import pytest

from dccex_usb.store import Away, Store
from tests.stores import Store as Fake

SCRIPT = '@on("power")\ndef power(t):\n    t.default()\n'


def test_the_railroads_the_store_holds_are_its_drawings(store: Fake) -> None:
    """A railroad's drawing is what the store keeps under its name, so the
    list of drawings is the list of railroads (rails49/control#586)."""
    store.drawings = ["crossover-yard", "bench"]
    store.opens()

    assert asyncio.run(Store(store.url).railroads()) == ["crossover-yard", "bench"]


def test_the_railroads_go_back_in_the_order_the_store_lists_them(store: Fake) -> None:
    """The order is the store's and is passed on as it came, as the releases
    are: which railroad a person wants is a question about the names, and the
    page that draws them is what asks it."""
    store.drawings = ["b", "a", "c"]
    store.opens()

    assert asyncio.run(Store(store.url).railroads()) == ["b", "a", "c"]


def test_an_entry_that_is_not_a_name_is_dropped_and_the_rest_stand(
    store: Fake,
) -> None:
    """A payload is read one field at a time and never trusted. What the store
    carries is what the page is shown, so one odd entry is not a reason to
    show a person no railroads at all."""
    store.drawings = ["bench", 12, "", None, "yard"]
    store.opens()

    assert asyncio.run(Store(store.url).railroads()) == ["bench", "yard"]


def test_a_store_that_answers_with_no_railroads_is_away(store: Fake) -> None:
    """A document of a shape this app cannot read is a store that has not
    answered this ask."""
    store.opens()
    store.drawings = "bench"  # type: ignore[assignment]

    with pytest.raises(Away):
        asyncio.run(Store(store.url).railroads())


def test_the_script_the_store_holds_is_its_text(store: Fake) -> None:
    store.holds("bench", SCRIPT)
    store.opens()

    assert asyncio.run(Store(store.url).text("bench")) == SCRIPT


def test_a_railroad_with_no_script_reads_as_none(store: Fake) -> None:
    """`404` is an answer and not an outage: the railroad has no script, and
    the page opens the sample for it (ADR-0015 d.5)."""
    store.opens()

    assert asyncio.run(Store(store.url).text("bench")) is None


def test_a_store_that_is_not_there_is_away(store: Fake) -> None:
    """Nothing listening, which is the ordinary state of a box whose store has
    not come up yet. One ask is one ask: whether to ask again is the page's,
    and a person editing is watching (`face.py`)."""
    with pytest.raises(Away):
        asyncio.run(Store(store.url).text("bench"))


def test_a_store_that_answers_with_no_script_text_is_away(store: Fake) -> None:
    store.opens()
    store.scripts["bench"] = 12

    with pytest.raises(Away):
        asyncio.run(Store(store.url).text("bench"))


def test_an_applied_script_reaches_the_store_as_its_document(store: Fake) -> None:
    """The document the store's route takes: the railroad it is for and the
    text of it (ADR-0015 d.1)."""
    store.opens()

    asyncio.run(Store(store.url).puts("bench", SCRIPT))

    assert store.saved == [("bench", {"script": "bench", "text": SCRIPT})]
    assert asyncio.run(Store(store.url).text("bench")) == SCRIPT


def test_a_store_that_refuses_a_put_is_away_with_its_own_words(store: Fake) -> None:
    """What the store said, as the page reads it. A refusal the mirror wrote
    over would be this app guessing at an answer it was given
    (control ADR-0050)."""
    store.opens()

    with pytest.raises(Away) as away:
        asyncio.run(Store(store.url).puts("a/b", SCRIPT))

    assert "cannot be saved" in str(away.value)


def test_a_store_that_is_not_there_refuses_nothing_and_is_away(store: Fake) -> None:
    """A put nobody answered is a put that did not happen, which is the
    sentence the page shows."""
    with pytest.raises(Away):
        asyncio.run(Store(store.url).puts("bench", SCRIPT))


def test_the_railroad_is_one_level_of_the_route(store: Fake) -> None:
    """A railroad called `a/b` is a name the store does not have rather than a
    route of its own, which is what escaping it a level at a time buys."""
    store.opens()

    assert asyncio.run(Store(store.url).text("a/b")) is None
    assert store.asked == ["a%2Fb"]


def test_the_store_says_where_it_is(store: Fake) -> None:
    """What the face names in a refusal: the address a person reading the page
    has to go and look at."""
    assert Store(f"{store.url}/").where == store.url
