# The inrush after power on

The journal reading has no rule for the inrush after power on. An `ALERT`
that ends in `NORMAL` on a district that is not `PROG` reads as a `spike`,
whether or not the district was just powered.

## Why this is out of scope

The station has not printed one. The journal on the box from 2026-10-12 to
2026-10-20 has 43 power-ons (`<p1 X>` more than 10 s after a trip on that
district). None was followed within 2 s by an `ALERT` that ended in `NORMAL`.
Two were followed by trips: C and D at 2026-10-20T08:57:54Z, `MAIN_AUTO`, a
run of `FAST OVERLOAD … FAULT PIN`. That is a fault, and an inrush rule would
not have matched it.

The line in the old `CONTEXT.md` (#267) was written before the journal
existed. #292 removed it. `ui/src/journal.js` never had the rule.

Being an incident is a reading of the journal (ADR-0022 d.3). A rule added
later is run over the whole record again, so nothing is lost by waiting for
one to show up.

## Prior requests

- #293: "journal: is the inrush after power on an incident?"
