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
# Handlers for this railroad's DCC-EX station (ADR-0013, ADR-0015, ADR-0018).

'''
Event listeners:
* `on(row, address=None)` keys a handler on an event.
* Valid rows are
    start, (connected, or the station restarted)
    power,
    point,
    signal,
    traction,
    function,
    reported_power, (reported by station)
    reported_point,
    reported_district, (a district's state, mode and limit)
    reported_message. (every message the station sends)

Handlers:
* ordinary Python functions
* run in place of the command the translator would have sent;
  `t.default()` sends that command as well.
* `t.send(text)` sends one raw message.
* `t.text(name, value)` sets the text the widget `name` shows.
* `t.desired(row, address=None)` reads the desired value.
* `t.reported(row, address=None)` the last reports;
* `t.message` is the message on reported_message.
* a value the bus has not given reads None.
* return quickly: a handler that blocks holds up the translator.
'''


@on("start")
def configure(t):
    # configure tracks:
    #      A Claro
    #      B Programming
    #      C Auto reverse section in ramp
    #      D Airolo (switches polarity depending on how wx310 crossing is set)
    for district, mode in {"A": "MAIN", "B": "PROG", "C": "MAIN_AUTO", "D": "MAIN_AUTO"}.items():
        t.send(f"<= {district} {mode}>")
    # set current limits
    # B at 250 mA is NMRA's limit for service mode (S-9.2.3)
    for district, ma in {"A": 2000, "B": 250, "C": 500, "D": 1500}.items():
        t.send(f"<JG {district} {ma}>")


@on("point", "12")
def wx310_crossing(t):
    # set correct track polarity depending on turnout position
    t.default()
    if t.desired("point", "12") == "thrown":
        t.send("<= D MAIN_AUTO_INV>")
    else:
        t.send("<= D MAIN_AUTO>")


@on("reported_district")
def show_district(t):
    # show each district on the text widget track-<district>:
    #      green on, amber near its limit, bold red tripped
    d = t.reported("district", t.address)
    state = "?" if d.state in (None, "unknown") else d.state
    shown = f"{t.address} {state}"
    if d.mode and d.mode.endswith("_INV"):
        shown += " inverted"
    colour = {"on": "32", "alert": "33", "tripped": "1;31"}.get(d.state)
    if colour:
        shown = f"{chr(27)}[{colour}m{shown}{chr(27)}[0m"
    t.text(f"track-{t.address}", shown)


# @on("point", "20")
# @on("point", "21")
# def signal_5(t):
#     t.default()
#     closed = t.desired("point", "20") == t.desired("point", "21") == "closed"
#     t.send("<A 5 2>" if closed else "<A 5 0>")
"""
