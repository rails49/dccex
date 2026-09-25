# The look rules' values, copied in

`tokens.css` beside this file is a **verbatim copy** of
[`docs/tokens.css`](https://github.com/rails49/.github/blob/main/docs/tokens.css)
in `rails49/.github`, which is where the look rules' values live. What each
token means and who is bound by it is
[LOOK.md](https://github.com/rails49/.github/blob/main/docs/LOOK.md) beside it
there, and neither page restates the other.

    source   rails49/.github, docs/tokens.css
    commit   eead9fc5afb75a971acb1d3979aad83802a14f16
    copied   2026-09-25, from that repository at eead9fc5

The commit is the pin: the one that last wrote the file, so that diffing this
copy against it is a diff of the same thing. It is the pin a git dependency
would have given, and it is here because nothing is installed
([ADR-0005](https://github.com/rails49/.github/blob/main/docs/adr/0005-the-look-rules-travel-as-a-copied-file-not-a-package.md)):
every consumer copies the file, records the commit, and keeps a check asserting
that the values it draws with equal the copy's.

## What this UI takes

Everything — six colours and two sizes — which is the dcc-ex UI's row in
LOOK.md. The **band** across the top and the rail down the left are both drawn
here, so every token has something on the page that is its colour or its size.
`--stop` and `--stop-ink` are the band's link reading while the station is not
answering, which is a fault (#138).

## The copy is inert

Nothing imports it, no build reads it and the page does not link it. The values
the page draws with are `ui/src/look.css`, a `:root` block of this UI's own,
and every rule that paints chrome asks for one of its custom properties rather
than writing a colour out. ADR-0003 leaves how a consumer expresses a value
free; a second stylesheet the page already has is the cheapest form this one
could take.

A colour written out as a hex is what that rule looks like when it breaks, so
the check looks for one in every file the page draws with: the component
stylesheets, the components themselves, the plain stylesheets beside them, and
`ui/index.html`, where a `style` attribute or a `<style>` block paints as
surely as a rule does. The components are in that list because the markup is
theirs: a `style` attribute on a release row paints the chrome with no
stylesheet anywhere near it (#85). The `:root`
block in `look.css` is the exception, being the one place a colour is meant to
be written; a hex anywhere else in that file is a rule painting past it (#60).

`--rail-turns` is the one value that cannot be read that way. A media query
cannot read a custom property, so the height is written into the two sheets
that turn — `dccex-app.styles.ts` gives the rail a row to lie in and
`dccex-rail.styles.ts` lies its own contents down — and `tests/ui/test_look.py`
asserts the number in both is the one the copy gives. Turning at two different
heights would draw the strip inside a column that is still there.

## The check runs in the gate

`tests/ui/test_look.py` reads this copy and the files beside it and **nothing
else**. A check that fetched the source would go red on somebody else's commit;
this one goes red on an edit here, which is the one thing it is for. A check
that reads only files in the repository it runs in runs in that repository's
own gate
([ADR-0010](https://github.com/rails49/.github/blob/main/docs/adr/0010-the-values-check-runs-in-the-consumers-gate-because-it-fetches-nothing.md)),
so it is red before an edit lands rather than after.

It is a `pytest` and not a test in the UI's own toolchain, because
`scripts/check.sh` is this repository's gate and that gate is Python: it needs
no node on the machine it runs on — the checks that do need one carry the
`node` marker and it does not collect them (#101) — which is the same property
the box has
(`deploy/ui.Dockerfile` — node builds the page inside the image and the box
carries none). `control` writes the same assertions in `vitest` because its
gate is a node one; what ADR-0010 asks for is that the check runs in the
consumer's gate, and this is that gate.

## Taking a change

`.github` announces a change by filing an issue here; nothing is scheduled and
nothing is automated. To take one: replace `tokens.css` with the new file
verbatim, write the new commit above, run `./scripts/check.sh`, and change
whatever it reports. A token that arrives with no expression here fails the
first assertion rather than being quietly ignored.
