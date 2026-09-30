# ADR-0012 — a flash says how far it has got

- **Status:** accepted, 2026-09-30
- **Related:** [ADR-0006](0006-the-operator-is-the-only-guard-on-a-flash.md)
  (the operator is the only guard on a flash),
  [ADR-0010](0010-the-page-polls-and-the-mirror-originates-nothing.md)
  (the page polls, and the mirror originates nothing)

## Context

POST `/flash` answers when esptool has finished, a minute or two later. Until
then the page knows only that it asked. esptool prints its own progress while
it writes; the mirror collects that output and reads it only after esptool
exits (`firmware.py`).

The answer could be streamed on the POST, or asked for on a second route. A
streamed answer reaches only the tab that pressed flash. A second route
reaches any tab, including one opened or reloaded mid-flash, and keeps the
page the side that asks (ADR-0010).

## Decision

**d.1** The mirror reads esptool's output as it runs and keeps the flash's
stage and, while writing, its percentage.

**d.2** GET `/flash` answers `{tag, stage, percent}` while a flash runs, and
that no flash is running otherwise. Stages: `fetching`, `checking`,
`writing`, `verifying`. `percent` is set only while `writing`.

**d.3** The page polls GET `/flash` about twice a second while a flash runs,
and on load, so a tab opened mid-flash shows it.

**d.4** After the POST answers, the page shows "waiting for the station" until
the link is back. A build that differs from the tag is shown as a failure.
That last step is read off the station, not the mirror (ADR-0006 d.3).

## Consequences

- POST `/flash` is unchanged. Its answer is still what became of the flash.
- `firmware.py`'s runner reads output line by line instead of waiting for
  exit. The suite's fake runner has to produce progress lines.
