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
 * `--stop` with the words on it (issue 138), and rails with no power is the
 * stop, which is what the power button says in `--stop-ink` while every track
 * is off (ADR-0011 d.1). The link still says so in words, because a reader may
 * not see the colour.
 *
 * **The green is the look rules' one green.** `--rail-group` is what this
 * chrome has — LOOK.md gives the dcc-ex UI six colours and no second green —
 * and the dot and a power button with the rails hot take it. A colour of this
 * page's own would be a seventh, and one of Shoelace's would follow the
 * system's light or dark setting while the chrome around it did not.
 *
 * **Grey is the band's own ink at half strength**, for a power button that
 * presses nothing while the link is down (ADR-0011 d.2). None of the six is a
 * dimmer ink.
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
     and the one control. It does not wrap — a band that grew a second line
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

  /* The power button: the one control on this chrome (ADR-0011 d.1). It paints
     no ground of its own — the colour is the reading and it reaches the icon
     through currentColor — and it is a thumb wide and a thumb high, because
     it is pressed on the phone at the layout. */
  .power {
    display: inline-flex;
    flex: none;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    min-width: var(--rail-button);
    min-height: var(--rail-button);
    padding: 0;
    border: none;
    background: none;
    color: var(--band-ink);
    font-size: 1.2em;
    cursor: pointer;
  }

  /* Green while any track is on, where a press cuts the power; red while every
     one is off, where a press turns it on. */
  .power.on {
    color: var(--rail-group);
  }

  .power.off {
    color: var(--stop-ink);
  }

  /* Grey and dead while the link is down: power is then unknown and a press
     would reach a station that is not answering (ADR-0011 d.2). */
  .power:disabled {
    color: var(--band-ink);
    cursor: default;
    opacity: 0.5;
  }

  /* Below the width at which the band cannot carry all of it, the build goes
     first: it is the longest thing on the band and it is on a tile beside the
     releases as well, where the release it gets compared against is. 560px is
     this page's own number and not a look rule: it is where the name, the
     build and the readings stop fitting on a phone held upright. */
  @media (max-width: 560px) {
    .build {
      display: none;
    }
  }

  /* Narrower than that, the words go and the link is the dot alone: the dot is
     the reading and the words are the reading a second time, so they are what
     there is to lose. The power button stays at every width — it is the one
     control on the page that commands power, and a thumb has to reach it on
     the phone at the layout. 400px is this page's own number too. */
  @media (max-width: 400px) {
    .says {
      display: none;
    }
  }
`;
