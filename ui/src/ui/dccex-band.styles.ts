import { css } from "lit";

/**
 * The band across the top: the chrome that carries what is true of the whole
 * system the UI is about.
 *
 * Its colours are the look rules' and are the same in every rails49 UI, so it
 * asks `look.css` for them rather than naming one. It is the height of a rail
 * button at least, which is what keeps the two pieces of chrome reading as one
 * edge on a phone and is the size a thumb needs for the power button.
 *
 * **The reds on it are the fault and the stop.** The look rules reserve red on
 * the chrome for stop or a fault: a link that is down is the fault and wears
 * `--stop` with the words on it (issue 138), and the stop is both the STOP
 * press and a railroad `layout` reports as `stopped`, which wear the same two
 * tokens (ADR-0017 d.2, ADR-0020 d.1). Power that is merely off is neither, and
 * is an outlined chip in the band's own ink — a band that drew it red would be
 * saying stop about a railroad nobody stopped. The link still says so in words,
 * because a reader may not see the colour.
 *
 * **The green is the look rules' one green.** `--rail-group` is what this
 * chrome has — LOOK.md gives the dcc-ex UI six colours and no second green —
 * and the dot and a power button `layout` reports as `on` take it. A colour of
 * this page's own would be a seventh, and one of Shoelace's would follow the
 * system's light or dark setting while the chrome around it did not.
 *
 * **Neither of those colours reads on the band's blue**, which is the one
 * measurement in this sheet: `--rail-group` on `--band` is 1.8 to 1 and
 * `--stop-ink` on it is 1.3, where a control needs 3. So the colour is never
 * laid straight on the band — the dot is ringed in the band's ink, the words
 * sit on `--stop`, the green sits on a chip of the band's ink, and the red
 * sits on `--stop`.
 *
 * **Grey is the band's own ink at half strength**, for a press that presses
 * nothing (ADR-0017 d.3, ADR-0020 d.3). None of the six is a dimmer ink. There
 * is no chip with it: a dim glyph or word on the blue is what a control that
 * cannot be pressed looks like, and it is the difference a reader who cannot
 * tell the green from the red is left with.
 *
 * **The two presses are one shape and are written once** (`.press`). They are
 * the same size, they are dead the same way, and the difference between them is
 * what each wears: a glyph the power row colours, and the word STOP in red.
 */
export const bandStyles = css`
  :host {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    box-sizing: border-box;
    min-height: var(--rail-button);
    padding: 0 0.75rem;
    background: var(--band);
    color: var(--band-ink);
  }

  /* What the page is about: the UI's name, and the build the station says it is
     running. */
  .about {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    min-width: 0;
  }

  .name {
    flex: none;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  /* The build, quieter than the name: the name says which UI this is, and the
     build is a fact the station reported. It does not wrap and is cut rather
     than shortening the readings at the other end of the band. Quieter by
     transparency rather than by a second colour, because the chrome holds six
     colours and none of them is a dimmer ink. */
  .build {
    min-width: 0;
    overflow: hidden;
    font-size: 0.8em;
    white-space: nowrap;
    text-overflow: ellipsis;
    opacity: 0.85;
  }

  /* What is true of the whole system, at the end the eye finishes on: the link
     and the two presses. It does not wrap — a band that grew a second line
     would push the work pane down every time the station went quiet. */
  .readings {
    display: flex;
    flex: none;
    align-items: center;
    gap: 0.75rem;
    white-space: nowrap;
  }

  .link {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  /* The link as a light: green while the station is answering and red while it
     is not. The ring is the band's own ink, which is what lifts either colour
     off the blue — both of them are mid-dark and neither reads against it on
     its own. */
  .dot {
    flex: none;
    box-sizing: border-box;
    width: 1rem;
    height: 1rem;
    border: 2px solid var(--band-ink);
    border-radius: 50%;
  }

  .dot.on {
    background: var(--rail-group);
  }

  .dot.off {
    background: var(--stop-ink);
  }

  /* The same reading in words, drawn only while the link is down, which is a
     fault. The padding keeps the words off the edge of the red. */
  .says {
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    background: var(--stop);
    color: var(--stop-ink);
    font-weight: 600;
  }

  /* Either press on this chrome: the power button and STOP (ADR-0017 d.1,
     ADR-0020 d.1). The shape is written once, because the two are the same
     control to a thumb and only what they wear differs. The border is on them
     in every state so the box does not move between them. Each is a thumb wide
     and a thumb high, because they are pressed on the phone at the layout. */
  .press {
    display: inline-flex;
    flex: none;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    min-width: var(--rail-button);
    min-height: var(--rail-button);
    padding: 0;
    border: 2px solid transparent;
    border-radius: 4px;
    background: none;
    color: var(--band-ink);
    cursor: pointer;
  }

  /* The power button. What it wears is the power row layout reports; the
     colour reaches the icon through currentColor, and the font size is what
     the icon is a multiple of (dccex-icon.styles.ts). */
  .power {
    font-size: 1.2em;
  }

  /* Power on: green on a chip of the band's own ink, which is what the green
     reads against. A press asks for off. */
  .power.on {
    background: var(--band-ink);
    color: var(--rail-group);
  }

  /* Power off: the band's own ink, outlined rather than filled. It is a state
     somebody chose and not a fault, so it is neither of the reds, and the
     outline is what keeps it from reading as the dead button below it. A press
     asks for on. */
  .power.off {
    border-color: var(--band-ink);
    color: var(--band-ink);
  }

  /* Stopped: red, the same two tokens the link's words wear, because a
     railroad stopped where it stands is the other thing red is for on this
     chrome (ADR-0017 d.2). A press asks for on, which is the way out of it. */
  .power.stopped {
    background: var(--stop);
    color: var(--stop-ink);
  }

  /* STOP: the press that stops every locomotive where it stands (ADR-0020 d.1,
     d.2). Red, the same two tokens the link's words and a stopped power button
     wear, because a railroad stopped where it stands is the other thing red is
     for on this chrome. The word rather than a glyph, and it keeps its chip in
     every state, because what it does does not change with the state (d.4). */
  .stop {
    padding: 0 0.5rem;
    background: var(--stop);
    color: var(--stop-ink);
    font-weight: 600;
    font-size: 0.8em;
    letter-spacing: 0.04em;
  }

  /* Grey and dead where a press reaches nothing: the power button with no
     broker, no station answering or no word from layout yet, and STOP with no
     broker (ADR-0017 d.3, ADR-0020 d.3). There is then nothing a press could
     reach, and for the power button no state to draw either. No chip and no
     outline, so what is left is a dim glyph or word on the blue. */
  .press:disabled {
    background: none;
    color: var(--band-ink);
    cursor: default;
    opacity: 0.5;
  }

  /* Below the width at which the band cannot carry all of it, the build goes
     first: it is the longest thing on the band, and it is the one reading here
     that does not change while the station is up — what the station is doing is
     on the tiles and what it is running is not (issue 170). 560px is this
     page's own number and not a look rule: it is where the name, the build and
     the readings stop fitting on a phone held upright. */
  @media (max-width: 560px) {
    .build {
      display: none;
    }
  }

  /* Narrower than that, the words go and the link is the dot alone: the dot is
     the reading and the words are the reading a second time, so they are what
     there is to lose. Both presses stay at every width — they are the two
     presses on the page that ask for power, and a thumb has to reach them on
     the phone at the layout. 400px is this page's own number too. */
  @media (max-width: 400px) {
    .says {
      display: none;
    }
  }
`;
