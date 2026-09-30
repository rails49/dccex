# ADR-0014 — the translator is on the bus through `control`'s package

- **Status:** accepted, 2026-09-30
- **Ticket:** #180
- **Related:** ADR-0001 (the mirror leaves the bus), ADR-0003 (the copy has
  no original left and is fixed here), ADR-0013 (the script),
  [org ADR-0006](https://github.com/rails49/.github/blob/main/docs/adr/0006-the-bus-contract-is-controls-and-travels-when-something-reads-it.md)
  (the bus contract is `control`'s)

## Context

The translator moves here from `control` (#180). Unlike the mirror, it stays
on the bus: it subscribes to `layout`'s desired values and publishes the track
and link rows. It uses `control`'s bus library (`tc49.lib`: `bus`, `mqtt`,
`clock`, `inventory`, `payload`, `layout`, `startup`), which `control` goes on
using and changing.

Org ADR-0006 says the first repository outside `control` to read the bus
copies it and records the commit. A copy of the library would be a second
version of code that `control` keeps changing, and nobody here can keep two
versions in step.

## Decision

**d.1** The translator is on the bus as a client of `control`'s railroad.
It is the one app here that is. The mirror stays off it (ADR-0001).

**d.2** It gets the bus library from `control`'s `tc49` package, a uv git
dependency. `uv.lock` holds the commit. No library code is copied here.

**d.3** The pin moves by hand: `uv lock --upgrade-package tc49` and this
repository's tests. `control` changing the bus files an issue here
(org ADR-0006).

**d.4** The translator's own code, tests and `docs/dccex/` are moved, not
shared. `control` deletes its copy, and a defect is fixed here (ADR-0003).

**d.5** It runs in this repository's stack from `dccex:<commit>`, next to the
mirror. It reaches the broker on the `rails49` network and the station at the
mirror's port on the stack's own network.

**d.6** `control`'s bench no longer builds the translator. A live run against
a station is `layout` and the translator as separate processes on the broker.

## Consequences

- The image carries all of `tc49` and its dependencies, of which the
  translator uses the library.
- Org ADR-0006's rule for the first outside reader is replaced by d.2 for this
  repository. 0006 gets a line pointing here.
- The translator and the face also call the store's face (ADR-0015), and
  org ADR-0006 gives the store's face the bus's rule. The same answer holds: no
  copy. `control` documents the routes, and a test here runs against a fake
  store.
- Until the pin moves past `control`'s deletion, the dependency still ships
  `tc49.dccex`. Nothing runs it.

## Considered

- **Copying the library**, with the commit in SOURCE.md. Two versions of it.
- **A copy checked against `control` in CI.** The package with more steps.
- **A binding of this repository's own**, written to `control`'s `BUS.md`. A
  second implementation of the contract, kept in step by hand.
- **The translator staying in `control`'s compose**, running this image.
  `control`'s deploy would depend on this repository's build.
