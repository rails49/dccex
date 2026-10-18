"""The readers of the desired half of the device vocabulary, one per row this
app acts on (`control`'s `docs/BUS.md`, *Device vocabulary*).

Each answers `None` where the row cannot be read. A translator answers
nothing, so a frame it cannot read is dropped, and one that raised would be
taken down by whatever published it (`docs/BUS.md`, rule 4).

control ADR-0075 declares `tc49.lib.payload` for no other repository, so
these are copied from `control`'s `src/tc49/lib/payload.py` at 8950c92.
"""

from typing import cast

from tc49.lib.inventory import OFF, ON, STOPPED


def commanded_power(payload: object) -> str | None:
    """The power a `wanted/track` value asks the railroad for: one of `on`,
    `stopped` and `off`, or None where it asks for none."""
    if not isinstance(payload, dict):
        return None
    wanted = cast(dict[str, object], payload).get("power")
    if not isinstance(wanted, str) or wanted not in (ON, STOPPED, OFF):
        return None
    return wanted


def desired_speed(payload: object) -> float | None:
    """The speed a `wanted/traction` value asks a locomotive for, a fraction
    of its maximum signed for direction, or None where it asks for none.

    A boolean is not a speed: JSON `true` is an `int` in Python and would
    otherwise be full speed forward. A fraction past −1.0 … 1.0 is still read;
    what it is worth is the translator's.
    """
    if not isinstance(payload, dict):
        return None
    stated = cast(dict[str, object], payload).get("speed")
    if isinstance(stated, bool) or not isinstance(stated, (int, float)):
        return None
    return float(stated)


def desired_position(payload: object) -> str | None:
    """The position a `wanted/point` value asks a point for, or None where it
    asks for none."""
    return _stated(payload, "position")


def desired_aspect(payload: object) -> str | None:
    """The aspect a `wanted/signal` value asks a signal for, or None where it
    asks for none."""
    return _stated(payload, "aspect")


def desired_function(payload: object) -> bool | None:
    """Whether a `wanted/function` value asks a function on, or None where it
    asks for nothing this can read. Only a JSON boolean is a value; the words
    `on` and `off` are not (control ADR-0063)."""
    if not isinstance(payload, dict):
        return None
    stated = cast(dict[str, object], payload).get("value")
    return stated if isinstance(stated, bool) else None


def _stated(payload: object, field: str) -> str | None:
    """One named string field of a row, or None where the payload states no
    such thing."""
    if not isinstance(payload, dict):
        return None
    stated = cast(dict[str, object], payload).get(field)
    return stated if isinstance(stated, str) else None
