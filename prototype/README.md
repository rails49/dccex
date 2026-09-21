# Prototype — the dcc-ex UI's screens

**Throwaway. Not the UI.** Lives on the `prototype/screens` branch and does not
go to `main`.

## The question

What should the dcc-ex UI look like, now that its content is settled: a
firmware release list, a flash, and a two-way decoding serial monitor, with
`dccex-usb`'s face as the only counterparty.

## Running it

    python3 -m http.server 8777 --bind 127.0.0.1

then `http://127.0.0.1:8777/screens.html`. `?variant=A|B|C` picks a variant,
the bar at the bottom and the ← → keys cycle, and `?theme=dark|light` forces a
theme — that last one is prototype-only, because the real UI has no toggle and
`prefers-color-scheme` decides (LOOK.md, **Theme**).

The station is fake: a timer emits plausible DCC-EX chatter, the release list
is made up, and flashing walks its six steps on a timer without writing
anything.

## What varies, and what does not

The band and the rail do not vary. LOOK.md binds them and the dcc-ex UI takes
everything, so putting them up for grabs would be prototyping a decision that
is already made. What varies is the work pane.

- **A — two views on the rail.** The rail switches the work between firmware
  and the monitor, the way `control`'s rail switches between its views. One
  thing on screen at a time, and the house style.
- **B — the monitor is the page.** The conversation never goes away, because
  it is the subject. Firmware is rare, so it arrives as a sheet over the
  stream instead of taking it.
- **C — state above, evidence below.** Nothing hides anything. The station's
  state reads at arm's length, the stream underneath is the evidence for it,
  and the releases sit in the same column.

## The answer

**C won**, 2026-09-21. State above, evidence below.

C is also the variant that forced the two questions below, and both are now
settled. C in this branch has been amended to the settled form; A and B have
not, so their bands still carry a build they would not carry.

**The band's right carries status, and LOOK.md is narrower than the
practice.** LOOK.md says it holds the UI's *controls*. `control`'s band
already carries which railroad is loaded, whether it holds unsaved edits and
whether what the app talks to is answering, and `tc-header.ts` records why:
*the line is what it is about, not whether it is pressable*. So status on the
band is right and C's tiles were the redundancy. The band now carries two
things — the station answers, the rails are hot — and the build moved to a
tile beside the releases it gets compared against.

**The band is read-only here, and that is a departure from `control`.**
`control`'s band presses ON, STOP and OFF because track power is a fact about
the whole railroad. This page is not on the bus, so its press would go down
the wire as `<0>` with nothing checking that the railroad is drained — which
is the rule `layout` holds (ADR-0062). So nothing on this page commands power.
The flash sequence is the one caller that cuts it, and it sequences itself.
The command box can still type `<0>`; that is what a raw monitor is, and it is
not a named control on the page.

Consequently C's rail carries Pause and Clear and nothing else, and **no
emergency stop is drawn on the chrome** — so the red token LOOK.md reserves
for the first UI that draws one is still unclaimed. That last part is an
assumption from the power decision rather than something asked; say so if an
emergency stop belongs here anyway.

## Still open

- Whether the release list belongs in a collapsed row inside the state column,
  as C has it, or as a view of its own once it grows past four entries.
- What the tiles say while the link is down. Build clears with the link
  (ADR-0066 d.5), so three of the four go blank at once.

## Not checked

Narrow widths. The rules are written — the band drops the track reading below
560px, the release rows wrap — and were not confirmed in a browser.
