# ADR-0029 — a script posts a widget's text and hears what the station says

- **Status:** accepted, 2026-10-22; d.1 amended by
  [ADR-0030](0030-a-script-reports-where-a-point-lies.md)
- **Ticket:** #342
- **Related:** [control
  ADR-0087](https://github.com/rails49/control/blob/main/docs/adr/0087-a-widget-is-on-the-drawing-and-control-carries-its-payload-without-reading-it.md)
  (a widget is on the drawing, and control carries its payload without
  reading it),
  [ADR-0013](0013-a-railroads-own-station-commands-are-a-script-in-the-translator.md)
  d.3 and d.4, which this amends,
  [ADR-0016](0016-a-trip-is-read-from-the-stations-diagnostics.md) (a trip is
  read from the station's diagnostics)

## Context

Control ADR-0087 adds text widgets to the drawing. A widget shows whatever is
posted on `tc49/ui/state/text/<name>`: raw UTF-8, retained, any writer, no
`at`. A person wants a widget beside each district saying whether it is on,
off, tripped or near its limit, which way an auto-reverse district is set, and
whether a joined PROG track is carrying MAIN.

ADR-0013 d.4 says a handler publishes nothing on the bus. d.3 makes power and
turnout reports events and adds others "when a script needs one". A report of
on or off says nothing about a trip, an alert, a mode or a limit, and each new
need would be a new row and a code change here.

The translator already folds trips and alerts (ADR-0016) and reads every
district's mode and limit for the journal (ADR-0022 d.2).

## Decision

**d.1** A handler may post a widget's text: `t.text(name, value)` publishes
`value` on `tc49/ui/state/text/<name>`, retained, and on no other topic. A
name that is empty or holds `/`, `+` or `#` raises. It is posted only where it
differs from the last text posted under that name. This amends ADR-0013 d.4:
the text row is the one thing a handler publishes.

**d.2** `reported_district` is an event, by district. Its value is a record
with `state` (`on`, `off`, `tripped`, `alert` or `unknown`), `mode` (the word
`<=` takes, so `MAIN_AUTO_INV` carries the polarity and a joined PROG track
reads `MAIN`) and `limit` (mA). Each is `None` where the station has not said.
It fires on a change of the record. When the link goes and when the railroad
stands down it fires `unknown` for every district it has reported.

**d.3** `reported_message` is an event with no address. It fires on every
message the station sends, the poll's answers included, and `t.message` is the
message verbatim. This amends ADR-0013 d.3: a need the rows do not cover is a
script that reads the station's own words, not a new row.

**d.4** A handler runs on the translator's loop, which also sends the `<G 3>`
the station needs every 3 s. A handler must return quickly. Nothing enforces
it.

## Consequences

- control's `Bus` gets `publish_text` (rails49/control#941), and the `tc49`
  pin moves.
- A widget's text outlives a translator that is killed, saying what it said
  last.
- A handler on `reported_message` that posts on every message publishes only
  when its text changes, because d.1 drops a repeated text.
- The current each district draws is not in the poll. Asking for it is #345.

## Considered

- **Widen `reported_power` to the five states.** Its values are the bus's
  `on` and `off`, and handlers compare against them.
- **`reported_message` alone.** Every script would fold trips again, and a
  trip ends on `NORMAL`, a `<p1>`, a commanded OFF or a lost link.
- **The translator posting a status row of its own.** The widget's name and
  the words are the railroad's, which is what the script is for.
- **A second MQTT client in this app for text rows.** It would bypass the
  binding the rest of the app is tested through.
