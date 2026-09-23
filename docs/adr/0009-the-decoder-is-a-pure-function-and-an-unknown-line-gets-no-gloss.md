# ADR-0009 — the decoder is a pure function, and an unknown line gets no gloss

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#1
- **Related:** [ADR-0007](0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)
  (the stream the decoder reads, and the mirror reading nothing on it),
  [ADR-0008](0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)
  (every reading on the page is made of the conversation),
  [control ADR-0050](https://github.com/rails49/control/blob/main/docs/adr/0050-broken-hardware-is-reported-never-worked-around.md)
  (broken hardware is reported, never worked around)

## Context

The **monitor** shows the station's conversation as it arrives. Raw, that
conversation is `<H 12 1>` and `<c CurrentMAIN 0 C Milli 0 0 4000 1000>`, and
an operator standing at the layout with a phone should not have to hold the
DCC-EX command reference in their head to read it. So each line the page
understands gets a **gloss** beside it — one plain sentence, in English.

Two questions, and both have a wrong answer that is easier than the right one.

**Where the glossing lives.** The obvious place is inside the component that
draws a line: it has the line in hand and it has to put the sentence somewhere.
What that costs is that every claim about the protocol then needs a DOM to
assert — a component built, a property assigned, an update awaited — for a
question that has nothing to do with drawing. It also puts the protocol
knowledge next to a clock and a socket, and a gloss that can reach either is a
gloss that can start being about more than the line.

`control` already settled this shape from the other end. `src/tc49/dccex/commands.py`
turns a desired value into the station's bytes and is asserted as
value-and-bytes pairs, with nothing plugged in and no railroad anywhere near
it. This is the same protocol read the other way round, and it deserves the
same seam.

**What to do with a line it does not know.** This fork's firmware answers a
subset of DCC-EX's vocabulary, upstream adds to it, and the station is free to
say something no version of this page has ever seen. A decoder that guesses —
"looks like a turnout" off a leading `H`, or a category off a first character —
reads well right up to the line where it is wrong, and then the page is showing
an operator a sentence about their railroad that nothing observed. That is the
worked-around observation `control` ADR-0050 refuses, drawn in the place a
person is most likely to trust it.

## Decision

**d.1** The decoder is a pure function: one line of the station's conversation
in, one **gloss** out or nothing. No socket, no state carried between calls, no
clock, no DOM, and no import of anything holding one. Given the same line it
returns the same sentence for ever.

**d.2** A line the decoder does not recognise returns nothing, and the monitor
shows that line raw with no gloss beside it. There is no partial gloss, no
hedged one, and no category guessed off a first character. The absence of a
sentence is the page saying it does not know, which is a true thing to say.

**d.3** It lives in a module of its own with no component in it, and it is
asserted as line-and-sentence pairs: every line the page claims to recognise,
and the near misses that have to return nothing — a known letter with the wrong
arity, a truncated line, a line that is not `<…>` at all. This is the seam that
most deserves exhaustive cases and the cheapest one in the repository to write
them at, because a case is two strings.

**d.4** Neither app decodes anything, and this does not change that. The mirror
reads `<` and `>` and no further, in the one direction where it has to frame
what a client sends; the **translator**'s reading is its own bus contract next
door. The decoder is the page's, so gaining one gives the mirror no opinion
about what is on the wire (ADR-0007 d.6).

**d.5** What it knows is allowed to grow, and growing it is adding a pair to
the suite. The decoder is not an authority on the protocol — the firmware is —
so a line it has learned wrongly is a bug in one function with one test, rather
than a wrong sentence spread across the page.

## Consequences

- Every line the page glosses can be asserted on a machine with nothing plugged
  in: no browser, no station, no cable. The suite is strings in and strings out.
- An operator can always tell what the page understood, because understanding
  is visible as a sentence and not-understanding is visible as its absence.
  Nothing has to be trusted that was not observed.
- The raw line is shown either way. A gloss is beside the conversation and
  never instead of it, so nothing the station said is ever hidden behind this
  page's reading of it — which is also what makes a wrong gloss survivable.
- A firmware that starts saying something new degrades to a stream of raw lines
  rather than to a page of confident nonsense, and the fix is a pair of strings.
- The readings the band and the tiles are made of come off the same
  conversation and take the same rule (ADR-0008 d.2): a line that is not
  recognised contributes no reading, and a reading nothing has supplied is
  blank rather than zero.
