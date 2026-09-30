import { css } from "lit";

/**
 * The tiles: one per track in use, in a row across the top of the monitor
 * view, wrapping onto more rows at the width of a phone.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's six colours stay on the chrome.
 *
 * **A tile is a column and it is centred.** The power symbol is the first thing
 * read and the largest, and the three words go under it: what the track is set
 * to, the current it draws, and the most it may draw (issue 170).
 *
 * **The row keeps its height when it is empty.** The tiles go together when the
 * link goes down — a tile is one track and the station is not saying it has any
 * — and a row that collapsed as it happened would move the monitor under the
 * reader's thumb at the moment the station went away. Each reading's line holds
 * its height the same way, so what changes is the reading and never the layout.
 */
export const tilesStyles = css`
  :host {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    box-sizing: border-box;
    min-height: 6.5rem;
    padding: 0.5rem 0.5rem 0;
  }

  /* One track: the power symbol, and its three readings under it, centred. It
     takes an equal share of the width and may shrink, so a handful of tiles are
     one row on a laptop and two or more on a phone rather than a row that runs
     off the side. */
  .tile {
    display: flex;
    flex: 1 1 8rem;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
    min-width: 0;
    box-sizing: border-box;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--sl-color-neutral-200);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-50);
    text-align: center;
  }

  /* Whether the track has power: the one reading on a tile that is a colour
     rather than a word. Larger than the words under it, because it is what the
     eye lands on; the colour reaches the icon through currentColor and the font
     size is what the icon is a multiple of (dccex-icon.styles.ts). */
  .power {
    display: inline-flex;
    flex: none;
    color: var(--sl-color-neutral-400);
    font-size: 1.4rem;
  }

  .power.on {
    color: var(--sl-color-success-600);
  }

  .power.off {
    color: var(--sl-color-danger-600);
  }

  /* What the track is set to: MAIN, PROG, DC… The loudest of the three words,
     because it is what says which track this is. */
  .mode {
    min-height: 1.25rem;
    overflow-wrap: anywhere;
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
    font-weight: var(--sl-font-weight-semibold);
    letter-spacing: 0.04em;
    line-height: 1.25rem;
  }

  /* The current it draws, and under it the most it may. Monospaced and tabular,
     because a current changes under the eye and a column of milliamps that
     jittered would be harder to read than the number is worth. The limit is
     quieter: it is what the station was built with and it does not move, so it
     is there to compare the current against rather than to be read. */
  .draws,
  .most {
    min-height: 1.5rem;
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-medium);
    font-variant-numeric: tabular-nums;
    line-height: 1.5rem;
  }

  .most {
    min-height: 1.25rem;
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    line-height: 1.25rem;
  }
`;
