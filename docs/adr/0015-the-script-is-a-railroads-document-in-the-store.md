# ADR-0015 — the script is a railroad's document in the store

- **Status:** accepted, 2026-09-30; amended 2026-09-30 (#175): d.3 said a
  railroad change exits, and d.4 did not say what a store outage does to a
  loaded script.
- **Ticket:** #185, #175, rails49/control#586
- **Amends:** ADR-0013 d.1 and d.8
- **Related:** ADR-0014 (the translator on the bus through `control`'s
  package), `control` ADR-0053 (backup), `control` ADR-0060 (the railroad is
  chosen while the apps run)

## Context

ADR-0013 d.1 had the translator read the script from a file named on its
command line. The script is to be edited on the page and backed up with the
railroad. A store holds several railroads, each needing its own script, and
the translator does not follow the railroad today.

## Decision

**d.1** A script is a document in `control`'s store, one per railroad:
`GET`/`PUT /scripts/<railroad>`, as a JSON document carrying the text. The
store backs it up with the rest. A box has one DCC-EX station, so the key is
the railroad alone.

**d.2** The translator takes `--store <url>`, not `--script`. It reads the
retained `tc49/layout/state/railroad`, then fetches that railroad's script.
Loading takes the script's text, so the tests hand it the sample directly.

**d.3** Every few seconds it fetches the script for the current railroad and
compares the text with the one it runs. When the text differs, it exits and
compose restarts it. A railroad change that gives the same text, or no script
both times, changes nothing. The exit stands the railroad down, as every exit
does, so a script takes effect from power off at the next ON.

**d.4** A railroad with no script runs with the defaults. A script that raises
on load, or a store that does not answer, leaves the translator with no
handlers: it carries out OFF, STOP and speeds, refuses power ON, and says why
on its link row. It keeps asking. Once a script is loaded, a fetch that fails
changes nothing. This extends ADR-0013 d.8 from a handler to the whole script.

**d.5** The page edits a script through this repository's face. Apply sends
the text to the face, which compiles it, refuses one that does not compile,
and puts it to the store server-side. The page lists the store's railroads
and the person picks one. Unapplied edits stay in the page, which warns
before they are discarded, and says that Apply stops the railroad.

## Consequences

- The translator reads a document, so it now starts after the store, where in
  `control` it read none.
- A load error shows on the link row in `control`'s UI and in the translator's
  log, not on the page.
- A script sends only to this box's station. Other stations are JMRI's.

## Considered

- **One script per installation.** Railroads need different configurations.
- **One railroad per installation.** A change to `control` ADR-0060 larger
  than following the railroad.
- **The script as `text/x-python` with an `ETag`.** Every other store route
  answers JSON, and headers would have to pass through the store's router.
- **A mounted file with modification-time checks.** File owner and inode
  handling, and a translator tied to the store's host.
- **Reloading in place.** A second way in beside the start.
- **Restarting without standing down.** New modes and limits would wait for
  the next ON with nothing to show it.
- **Refusing to start on a bad script.** `control` could not stop the railroad.
- **Running a bad script's railroad with no handlers and power ON allowed.**
  Current limits and track modes would be missing.
