"""The sample **script**, and the shape every script has.

A script is a railroad's document in the store and not a module of this
package, so what is here is its **text**: the sample is loaded the way the
store's answer is loaded (`script.load`), and nothing imports it as Python.
That is also why it is a string rather than a file beside this one — a script
names no module of ours, imports nothing and is written with `on` alone.

It is the documentation as much as the test data (ADR-0013, consequences):
the tests load it, fire events and assert the bytes sent
(`tests/dccex/test_translator.py`), `docs/dccex/README.md` shows it, and it is
what a railroad with no script of its own is offered to start from (#185).

**The values in it are this installation's**, not defaults and not a
recommendation: what a district can take is what is wired to it, and which
track the reversing loop is on is this railroad's wiring.
"""

TEXT = """\
# Handlers for this railroad's DCC-EX station (ADR-0013, ADR-0015).
#
# `on(row, address=None)` keys a handler on an event. The rows are power,
# point, signal, traction, function, and for what the station reported
# reported_power and reported_point.
#
# A handler on a desired value runs in place of the command the translator
# would have sent; `t.default()` sends that command as well. `t.send(text)`
# sends one raw message. `t.desired(row, address=None)` reads the desired
# picture and `t.reported(row, address=None)` the last reports; a value the
# bus has not given reads None.


@on("power")
def power(t):
    t.default()
    for district, ma in {"A": 3000, "B": 3000, "C": 1500, "D": 1500}.items():
        t.send(f"<= {district} LIMIT {ma}>")
    reverser(t)


@on("point", "12")
def point_12(t):
    t.default()
    reverser(t)


def reverser(t):
    # District D is the reversing loop behind point 12.
    mode = "MAIN_INV" if t.desired("point", "12") == "thrown" else "MAIN"
    t.send(f"<= D {mode}>")


@on("point", "20")
@on("point", "21")
def signal_5(t):
    t.default()
    closed = t.desired("point", "20") == t.desired("point", "21") == "closed"
    t.send("<A 5 2>" if closed else "<A 5 0>")
"""
