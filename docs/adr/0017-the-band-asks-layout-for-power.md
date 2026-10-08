# ADR-0017 — the band asks `layout` for power

- **Status:** accepted, 2026-10-08
- **Ticket:** #205, #206, #208
- **Supersedes:** [ADR-0011](0011-the-band-commands-track-power.md) d.1, d.2
  and d.4
- **Related:** [org ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)
  (a UI talks to the bus, the store and its own app's face), ADR-0004 (the
  face reaches a browser through the door), ADR-0018 (the station's setup
  runs at `start`), `control` ADR-0051, ADR-0054 and ADR-0062

## Context

ADR-0011's button sends `<1>` or `<0>` through the face. That skips `layout`
and the translator. `layout` refuses an OFF while a run is going or a train is
moving, and zeroes every locomotive's speed before a cut (`control`
ADR-0062). The translator runs the script's power handler. `control`'s button
gets both by publishing `tc49/layout/power_wanted`, a row a browser may write.

Org ADR-0002 lets a UI publish those rows. The broker's `/mqtt` is routed only
on `control`'s host, and refuses a page from another origin.

ADR-0011 drew the button red while every track is off. The look rules keep red
on the chrome for a stop or a fault, and `control`'s band draws OFF plainly
(`control` ADR-0054, control#585).

## Decision

**d.1** A press publishes `tc49/layout/power_wanted`: `off` while the button
reads `on`, and `on` otherwise. The band sends no `<1>` or `<0>`.

**d.2** The button reads `tc49/layout/state/power`. `on` is green. `off` is an
outlined chip in the band's ink. `stopped` is red, and a press sends `on`.

**d.3** The button is disabled while the bus is unreachable or the link is
down.

**d.4** An OFF that `layout` drops shows nothing. The button stays green.

**d.5** The page reaches the broker at `/mqtt` on its own origin. This
repository's compose routes it to `control`'s `tc49-mqtt@docker` service and
refuses a foreign origin as `control`'s route does. `control`'s deploy does
not change.

**d.6** A tile's power symbol is grey for a track that is off.

ADR-0011 d.3 stands: the tiles press nothing.

## Consequences

- The page is a client of the bus and of the mirror's face. CONTEXT.md's
  **face** and **band** entries say so.
- The button needs `control`. With no broker or no `layout`, it is disabled
  or nothing answers it. The monitor's command box still sends `<1>`.
- The page depends on the service name `tc49-mqtt` in `control`'s labels.
- There is no STOP on this page (#208).

## Considered

- **Keep `<1>` and `<0>` and move the setup to `start` only** (ADR-0018). No
  check from `layout`.
- **Bus when it is reachable, `<1>` otherwise.** One press, two behaviours,
  chosen by something the operator cannot see.
- **Add this origin to `control`'s `/mqtt` route.** `control`'s deploy would
  name this repository, and the page would go cross-origin.
- **Colour from the station's `<p…>`.** No `stopped`, and it disagrees with
  `control`'s band while a report is on its way.
- **ON, STOP and OFF as in `control`.** Deferred to #208.
- **A grey token in the organisation's `tokens.css`.** An org change for what
  the band's own ink does.
