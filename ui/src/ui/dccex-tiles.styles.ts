import { css } from "lit";

/**
 * The tiles: four readings in a row across the top of the work pane, wrapping
 * onto a second line at the width of a phone.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's four values stay on the chrome.
 *
 * **A blank tile keeps its shape.** Three of the four blank together when the
 * link goes down, and a row that collapsed as it happened would move the
 * monitor under the reader's thumb at the moment the station went away. The
 * reading's line holds its height whether there is anything in it or not, so
 * what changes is the reading and never the layout.
 */
export const tilesStyles = css`
  :host {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    box-sizing: border-box;
    padding: 0.5rem 0.5rem 0;
  }

  /* One reading: what it is called, and what it reads under it. It takes an
     equal share of the width and may shrink, so four tiles are one row on a
     laptop and two on a phone rather than a row that runs off the side. */
  .tile {
    display: flex;
    flex: 1 1 8rem;
    flex-direction: column;
    gap: 0.125rem;
    min-width: 0;
    box-sizing: border-box;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--sl-color-neutral-200);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-50);
  }

  /* What the reading is called. Quieter and smaller than the reading itself:
     the label says which of the four this is, and the answer is what is being
     read. */
  .of {
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
  }

  /* The reading. Monospaced, because a build is a commit and a current is a
     number that changes under the eye, and tabular so that a column of
     milliamps does not jitter. It keeps its height while it is blank, so the
     row does not collapse when the link goes. */
  .reads {
    min-height: 1.5rem;
    overflow-wrap: anywhere;
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-medium);
    font-variant-numeric: tabular-nums;
    line-height: 1.5rem;
  }
`;
