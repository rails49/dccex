# ADR-0022 — the journal is what the station said

- **Status:** accepted, 2026-10-12
- **Ticket:** #263, #264, #265, #266
- **Related:** ADR-0010 (the page polls, and the mirror originates nothing),
  ADR-0016 (a trip is read from the station's diagnostics), ADR-0009 (the
  decoder is a pure function), ADR-0017 (the UI talks to one face and the
  bus), `control` ADR-0010 (history is the trace)

## Context

The station reports every overload, alert and reversal on USB as a
`<* TRACK X … *>` line (ADR-0016). Nothing keeps them. The translator folds
them into `device/track` and forgets them on a link loss. The page shows them
on the monitor while it is open.

Shorts should not happen on this railroad except where a reverser flips a
district in `MAIN_AUTO`. Finding the ones that do needs a record kept while
nobody is watching, read afterwards with counts per district.

The station prints no flip count and no peak current. A good flip is
`TRACK C INVERT (fast)`; a flip that did not clear the short is followed by
a trip. Telling the two apart needs a window and a rate, and the right
numbers are not known before the record exists.

The page reaches the mirror's face and the bus, and nothing else
(ADR-0017). The translator has no face. `control`'s bus has no word for a
district, and its store takes no writes at run time (`control` ADR-0010).

## Decision

**d.1** The translator keeps the **journal**: one JSON object per line,
appended to a file on a volume the box keeps. It writes whether or not a page
is open.

**d.2** A line is written for every `<* TRACK … *>` and every `<p…>` the
station sends, and for the link going down or up and the station restarting
(ADR-0021). Each carries `at` (when it arrived), `railroad` and `build`. A
station line carries its text verbatim as `said`, and where it names a
district, the district's `mode` and `limit` at that moment.

**d.3** The translator decides nothing about a line. Whether a line is part
of an **incident**, and which kind, is decided by the page when it reads the
journal. A changed rule reads the whole journal again under itself.

**d.4** The mirror mounts the same volume. Its face serves the file as it
is, and truncates it to empty on a request from the page. The translator
opens the file for appending, so a clear loses no line.

**d.5** The page computes incidents and statistics in one pure function from
the whole file: journal lines in, incidents and counts out. No socket and no
clock, as the decoder (ADR-0009).

**d.6** The station's firmware does not change. A current over a district's
limit is the threshold. A spike under it is not seen.

## Consequences

- The face serves a file another app writes. It reads no payload of it.
- Without a page, nothing is lost: the translator is the client that wants
  the record, which is what ADR-0010's last consequence anticipated.
- On a bench with no railroad loaded there is no translator and no journal.
- The journal grows until someone clears it from the page. Nothing caps it.
- The `<* … *>` lines are written to USB only, so the journal depends on the
  mirror, as trips do (ADR-0016).

## Considered

- **The translator writing only incidents.** The flip rule is a guess until
  there is data. A changed rule would not reach lines already dropped.
- **A face on the translator.** A second face for the page to talk to.
- **The bus, or `control`'s store.** The bus has no district, and the store
  takes no run-time writes.
- **Clearing older lines only.** A rewrite races the translator's appends and
  needs the two apps to agree on a reopen.
- **The page recording.** It records nothing while it is closed.
