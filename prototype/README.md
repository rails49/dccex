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

## Open questions it surfaces

1. **The band's right.** LOOK.md says it holds the UI's *controls*. All three
   variants put *status* there — link, build, track. Either the rule means
   something wider than it says, or this status belongs in the work and the
   band's right is empty, which LOOK.md explicitly allows.
2. **Red on the chrome.** B and C draw an emergency stop on the rail. LOOK.md
   says the first UI that draws one adds the token to `tokens.css` and its
   line to the table. Nothing has yet.
3. **Whether the page should have a stop at all**, given the flash sequence
   already stops the locomotives on its own.
4. **C repeats itself.** Its tiles say what the band says. That is either the
   band being wrong or the tiles being redundant, and it is the clearest
   evidence for question 1.

## Not checked

Narrow widths. The rules are written — the band drops two readouts below
560px, the release rows wrap — and were not confirmed in a browser.
