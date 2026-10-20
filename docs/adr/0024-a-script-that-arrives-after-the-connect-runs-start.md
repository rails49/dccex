# ADR-0024 — a script that arrives after the connect runs `start`

- **Status:** accepted, 2026-10-20
- **Amends:** [ADR-0018](0018-the-stations-setup-runs-at-start.md) d.1 (when
  `start` runs)
- **Related:** [ADR-0015](0015-the-script-is-a-railroads-document-in-the-store.md)
  d.3 (a changed text ends the process), d.4 (no store, no handlers),
  [ADR-0021](0021-a-restart-is-a-stash-the-boot-has-cleared.md) (a restart is
  a stash the boot has cleared)

## Context

The box rebooted on 2026-10-20. The translator came up at 09:38, `layout` at
09:51. With no railroad named, the translator connected with no script and ran
`start` with no handler. When `layout` named `gotthard`, the translator loaded
its script in place. `start` did not run, and the station kept the firmware's
modes and limits (`<jG 5000 250 5000 5000>`, C and D `NONE`) until the
translator was restarted by hand.

The stash was set at the connect, so no poll read a restart either.

## Decision

**d.1** A first script that loads while the link is up runs what a connect
runs: the mark, `start`, the journal's two questions, and the replay
(`DccEx._read`, `_started`).

**d.2** A first script is one loaded where none was. A changed text still ends
the process (ADR-0015 d.3). A store that answers no script runs nothing.

## Consequences

- The apps on the box can come up in any order.
- The replay goes out a second time for values already applied with no
  script. Each is a command the station takes again with no change.

## Considered

- **End the process, as a changed text does.** Compose brings it up on the
  script, and the connect runs `start`. The railroad is stood down on the way
  out, so power goes off.
- **Wait for the railroad longer at start.** A box with no railroad chosen is
  an ordinary state (control ADR-0060); no wait is long enough.
