# ADR-0013 — a railroad's own station commands are a script in the translator

- **Status:** accepted, 2026-09-30; d.1 and d.8 amended by
  [ADR-0015](0015-the-script-is-a-railroads-document-in-the-store.md)
- **Related:** `control` ADR-0050 (broken hardware is reported, never worked
  around), `control` ADR-0054 (the railroad comes up at rest and points replay)

## Context

Some of what a railroad needs from its station has no word on the bus: the
mode each track is set to, the current each may draw, a track reversed when a
turnout throws, a signal set from two turnouts. The translator's `startup`
file covers one case: raw commands sent after the first `<1>` of a session.

Three places could hold the rest:

- The translator. It receives the desired values, so it can send something
  other than what it would have sent.
- A new client of the mirror's port. It hears only what the station says, so
  it acts after the station has. It cannot stand in for a `<1>` another
  client sent.
- EXRAIL, in the firmware. It covers turnout and signal cases, including
  throws from JMRI or a throttle. A change is a flash, and per-track current
  limits at power-on are not all expressible.

The mirror is not a candidate: it does not decide or rewrite (CONTEXT.md).

## Decision

**d.1** The translator loads one Python **script**, named on its command line
and read at start. A change takes a restart.

**d.2** A **handler** keyed on a desired value runs in place of the
translator's own command for it. It sends that command too only by calling
`default()`. With no handler, the translator sends what it sends today.

**d.3** A handler keyed on a station report runs after the fact and replaces
nothing. It fires when the reported value differs from the last one heard,
not on every poll answer. Power and turnout reports are events; others are
added when a script needs one.

**d.4** A handler sends raw `<…>`, reads the desired picture and the last
reports, and publishes nothing on the bus. A desired value the bus has not
given reads `None`.

**d.5** A handler sets everything it depends on each time it runs, from the
desired picture, and never relies on what an earlier handler sent. The power
handler sets a track's mode from the points that decide it, even when that
repeats a point handler.

**d.6** The translator does not replay power on connect. After a station or
translator restart the rails stay as the station reports them, and power
comes back when a person presses ON. Every other desired value replays as
before, through its handler.

**d.7** The power handler runs on every ON, not only on a change from off.

**d.8** A handler that raises is logged, and the default runs if the handler
had not called it (`control` ADR-0050).

**d.9** The `startup` file goes. A power handler does the same.

## Consequences

- The work waits for the translator to move here from `control`.
- The translator's rule that a connect applies the retained desired state
  loses power. `layout` still holds power as desired and reads it off, as it
  does for any report of off.
- The translator's tests load a sample script, fire events and assert the
  bytes sent. The sample is also the documentation.
- A throw from JMRI or a throttle reaches a script only as a report, after
  the station has acted.
