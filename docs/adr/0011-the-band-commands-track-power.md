# ADR-0011 — the band commands track power

- **Status:** accepted, 2026-09-30; d.1, d.2 and d.4 superseded by
  [ADR-0017](0017-the-band-asks-layout-for-power.md)
- **Supersedes:** [ADR-0008](0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md) d.5
- **Related:** [ADR-0006](0006-the-operator-is-the-only-guard-on-a-flash.md)
  (the operator is the only guard on a flash)

## Context

ADR-0008 d.5 kept every power control off the page. `control`'s band may press
power because `layout` checks the railroad first; this page is on no bus, so
nothing checks for it.

That check never guarded the station. Any client of the mirror's port can send
`<1>` or `<0>`: JMRI, a throttle, the monitor's command box. The operator
already switches power at this level when working below `control`. A button on
the band sends the same bytes the command box does.

## Decision

**d.1** The band carries a power button. Green when any track is on; a press
sends `<0>`. Red when every track is off; a press sends `<1>`.

**d.2** The button is disabled while the link is down. Power state is then
unknown and a press would reach nothing.

**d.3** It is the only power control on the page. The per-track readings in the
monitor view show state and press nothing.

**d.4** The guard is the operator, as for a flash (ADR-0006). The page asks for
no confirmation.

## Consequences

- The band is two readings and one control. CONTEXT.md's **band** entry says so.
- A press is a line on the stream like any other client's, and the station's
  `<p…>` answer is what turns the button's colour.
