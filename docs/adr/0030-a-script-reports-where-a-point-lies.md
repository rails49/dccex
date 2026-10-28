# ADR-0030 — a script reports where a point lies

- **Status:** accepted, 2026-10-27
- **Ticket:** #352
- **Related:** [control
  ADR-0097](https://github.com/rails49/control/blob/main/docs/adr/0097-a-reported-point-lies-where-device-point-says-and-a-train-waits-for-it.md)
  (a reported point lies where `device/point` says, and a train waits for it),
  [ADR-0029](0029-a-script-posts-text-and-hears-what-the-station-says.md) d.1
  and
  [ADR-0013](0013-a-railroads-own-station-commands-are-a-script-in-the-translator.md)
  d.4, which this amends

## Context

This railroad's turnouts have no feedback, and the station's answer to a
throw is one it faked (control ADR-0022), so this app publishes no
`device/point`. Control ADR-0097 d.2 lets a translator publish, for an address
the drawing lists as `reported`, the position it last put the hardware in,
whether from `wanted/point` or from its own logic.

Logic of its own is a script's. Gotthard's closes point 104 when 105 is
thrown, and the reverse, so `wanted/point` for 104 is not where 104 lies. Which
addresses are `reported` is on the drawing, which this app does not read.

## Decision

**d.1** A handler may report where a point lies: `t.point(address, position)`
publishes `{addr, position}` on `tc49/layout/state/device/point/<address>`,
retained. `position` is `closed` or `thrown`. An address that is not a string,
is empty, or holds `/`, `+` or `#` raises, and so does any other position. It
is published only where it differs from the last position reported for that
address. This amends ADR-0029 d.1: the text row and the point row are the two
things a handler publishes.

**d.2** It sends nothing to the station. A script throws a point with
`t.send` or `t.default()` and reports it with `t.point`.

**d.3** It is not a report of the station's. `t.reported("point", …)` and
`reported_point` stay what the station said.

**d.4** The value stays when the link goes and when the railroad stands down.
It is where the hardware was last put. `start` reports again on a connect and
after a restart.

## Consequences

- A script that never calls `t.point` publishes no `device/point`.
- A script that reports an address the drawing does not list as `reported`
  publishes a row no app reads, against control ADR-0097 d.3. Nothing here
  can tell.

## Considered

- **Publish every point this app throws.** It would publish for addresses that
  are not `reported`, and miss a point a script throws with `t.send`.
- **`t.point` also throws the point.** A script already throws it, with the
  command its hardware takes.
