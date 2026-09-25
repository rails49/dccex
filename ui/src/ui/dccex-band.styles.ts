import { css } from "lit";

/**
 * The band across the top: the chrome that carries what is true of the whole
 * system the UI is about.
 *
 * Its colours are the look rules' and are the same in every rails49 UI, so it
 * asks `look.css` for them rather than naming one. It is the height of a rail
 * button at least, which is what keeps the two pieces of chrome reading as one
 * edge on a phone.
 *
 * **The one red on it is a fault.** The look rules reserve red on the chrome
 * for stop or a fault. This band draws no control at all (ADR-0008 d.5), so
 * no stop, but a link that is down is a fault and wears `--stop` (issue 138).
 * It still says so in words, because a reader may not see the colour.
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

  .name {
    flex: none;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  /* What is true of the whole system, at the end the eye finishes on. */
  .readings {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    min-width: 0;
  }

  /* One reading: what it is called, then what it reads. It does not wrap —
     a band that grew a second line would push the work pane down every time
     the station went quiet. */
  .reading {
    display: flex;
    align-items: baseline;
    gap: 0.35rem;
    white-space: nowrap;
  }

  /* What the reading is called, quieter than the reading itself: the word is
     there to say which of the two this is, and the answer is what is being
     read. Quieter by transparency rather than by a second colour, because the
     chrome holds six colours and none of them is a dimmer ink. */
  .of {
    opacity: 0.75;
    font-size: 0.8em;
  }

  .reads {
    font-weight: 600;
  }

  /* A reading that is a fault: today only a link that is down. The padding
     keeps the words off the edge of the red. */
  .fault {
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    background: var(--stop);
    color: var(--stop-ink);
  }

  /* Below the width at which the band cannot carry both readings, the one
     that survives is whether the station is answering. A station that is not
     answering makes the other reading meaningless, and a band that kept the
     rails instead would be showing a power state nothing has confirmed since
     the link went. 560px is this page's own number and not a look rule: it is
     where the name, the link and the rails stop fitting on a phone held
     upright. */
  @media (max-width: 560px) {
    .rails {
      display: none;
    }
  }
`;
