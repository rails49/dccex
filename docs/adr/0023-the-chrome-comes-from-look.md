# ADR-0023 — the chrome comes from look

- **Status:** accepted, 2026-10-14
- **Ticket:** #281
- **Amends:**
  [ADR-0008](0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)
  (red on the chrome), [ADR-0011](0011-the-band-commands-track-power.md) (the
  band's one control), [ADR-0017](0017-the-band-asks-layout-for-power.md) d.2
  (what the power button wears), [ADR-0020](0020-the-band-has-a-stop-press.md)
  d.1 (what STOP looks like)
- **Related:** [rails49/look#1](https://github.com/rails49/look/issues/1) (one
  shared chrome for rails49's UIs),
  [rails49/look#14](https://github.com/rails49/look/issues/14) (look v0.3.0, the
  toggle reason), `control` ADR-0073 (control's chrome comes from look), [org
  ADR-0016](https://github.com/rails49/.github/blob/main/docs/adr/0016-the-chrome-comes-from-look.md)
  (the organisation's decision, accepted 2026-10-17; supersedes org ADR-0005 and
  ADR-0010 and amends ADR-0003, ADR-0007 and ADR-0012, which this page departed
  from)

## Context

Each rails49 UI drew its own band and rail. This page kept a copy of the
shared colours and sizes in `ui/look/`, pinned to the commit they came from,
and `tests/ui/test_look.py` checked its own styles against them. The UIs drifted
anyway. [`@rails49/look`](https://github.com/rails49/look) is one package that
draws the band, the rail, the dialogs and the Shoelace theme for all of them.

look's `look-power` had one `reason` that held both the toggle and the stop
sign. This page holds them on different facts (ADR-0017 d.3, ADR-0020 d.3), so
look v0.3.0 added `toggle-reason`, which holds the toggle alone.

## Decision

**d.1** The band, the rail, track power, the dialog shell, the Shoelace theme
and the glyphs come from `@rails49/look`, pinned to a release tag in
`ui/package.json`. `dccex-app` draws `look-shell` with the band and the rail
from `ui/src/ui/chrome.ts`, and listens there for `look-view` and
`look-power`.

**d.2** The band is `look-about name="dcc-ex"` with the **build** as its
detail, the railroad `control` has loaded as a `look-reading` (none while it is
unreported), the **link** as a `look-dot` with `dcc-ex offline` beside it while
the station is silent, and `look-power`. There is no gear.

**d.3** `look-power`'s `state` is `layout`'s power row, and `off` before it has
reported. The toggle asks for `off` when on and for `on` otherwise; the stop
sign asks for `stopped`. Both publish to `tc49/layout/power_wanted` as before.
`reason="no bus"` holds both. `toggle-reason` holds only the toggle, with
`no station` or `no layout`, so STOP stays live with the broker alone.

**d.4** The rail is four `look-view`s: Monitor `terminal`, Releases
`lightning-charge`, Script `file-earmark-code`, Journal `journal-text`
(`ui/src/view.ts`). Choosing one writes the hash, as the rail's press did. On a
short window the rail lies along the top; that strip is look's.

**d.5** Glyphs are Bootstrap Icons drawn by Shoelace and served from the page's
own origin. Vite copies Shoelace's assets to `/shoelace` and `main.ts` calls
`setBasePath("/shoelace")`; nginx answers a missing glyph with 404. The work
pane's glyphs move too: the tiles' `power`, and the monitor's `pause-fill`,
`play-fill` and `eraser`.

**d.6** The work pane follows the system's light or dark setting through
`look.css`, which carries both Shoelace themes. Each work-pane component puts
look's `lookTheme` first in its styles.

**d.7** The flash warning is a `look-dialog` titled `Flash <tag>`, with
*cancel* and a red *write it* in its footer. Closing it is the cancel. It is
still the operator's one warning before a flash (ADR-0006 d.2).

**d.8** The gate runs look's `look-check` over `ui/src` and `ui/index.html`
(`scripts/check.sh`). It fails on a selector naming a `look-` element, on
setting a look token or a `--sl-*` property, and on `sl-*::part()` in this
page's code. The `ci` job installs the page's packages for it.

## What is deleted

`dccex-band`, `dccex-rail`, `dccex-icon` and their sheets and tests,
`ui/src/ui/theme.ts`, `ui/src/look.ts`, `ui/src/look.css`, `ui/look/` (the
copied `tokens.css` and its README), `tests/ui/test_look.py`, `@mdi/js`, and
the band and rail rules in `dccex-app.styles.ts`.

## Consequences

- Where ADR-0017 d.2 says green, an outlined chip and red, read look's toggle:
  green when on, dimmed when off, red when stopped.
- Where ADR-0020 d.1 says a red chip with the word `STOP`, read look's red stop
  sign right of the toggle.
- Where ADR-0011 and ADR-0008 speak of the band's button and of red on the
  chrome, read `look-power` and `look-dot`. Nothing else here is red.
- How the band fits a narrow screen, and the size of its presses, are look's.
  The band no longer drops the build, the railroad and the link's words below
  560px and 400px (#208).
- A change to the chrome is a change in look and a new tag. This page takes it
  by moving the tag; look's release workflow opens that pull request.
- The suites draw no glyphs: `ui/test/mounted.ts` registers an icon resolver
  that returns nothing.

## Considered

- **look as it was, one reason for both presses.** STOP would wait on a
  station `layout` holds a stop for, which ADR-0020 d.3 refuses.
- **Keeping `@mdi/js` in the work pane.** Two icon sets on one page, and a
  component of this page's own to draw one of them.
