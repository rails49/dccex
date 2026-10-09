# ADR-0020 — the band has a STOP press

- **Status:** accepted, 2026-10-09
- **Ticket:** #208
- **Related:** ADR-0017 (the band asks `layout` for power), `control` ADR-0062

## Context

ADR-0017 gave the band one power button: `on`, `off`, and a red `stopped`
whose press sends `on`. Nothing on this page stops every locomotive. `layout`
applies `power_wanted: stopped` whatever the run, and holds it until an `on`.

## Decision

**d.1** The band has a STOP button right of the power button: a red chip
(`--stop`/`--stop-ink`) with the word `STOP`.

**d.2** A press publishes `{"power":"stopped"}` to `tc49/layout/power_wanted`
at once. No confirmation.

**d.3** It is disabled only while the bus is unreachable. Its title is
`stop every locomotive where it stands`, or `no bus` while disabled.

**d.4** It does not change with the state. A press while `stopped` publishes
again.

## Consequences

- The power button stays the way out of `stopped`: red, and a press sends `on`.
- A STOP while the station is silent is held by `layout` and reaches the
  station when it answers.

## Considered

- **A long press on the power button.** Not discoverable.
- **A confirmation.** Slows the one press that must be fast; a wrong STOP
  costs one `on`.
- **The power button's disabled rules** (no station, no layout). Refuses a
  stop `layout` would hold.
- **A hardware button.** Later, from a microcontroller on the bus; not this
  page.
