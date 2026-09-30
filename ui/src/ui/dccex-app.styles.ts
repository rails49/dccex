import { css, unsafeCSS } from "lit";

import { RAIL_TURNS_PX } from "../look.js";

/**
 * The page the whole UI is laid out in: the band across the top, the rail down
 * the left, and the work pane between them (LOOK.md).
 *
 * Below `--rail-turns` the rail lies down along the top of the work, so the
 * grid gives it a row instead of a column. `dccex-rail.styles.ts` turns its own
 * contents at the same height, out of the same number.
 */
export const appStyles = css`
  :host {
    display: grid;
    grid-template-areas:
      "band band"
      "rail work";
    grid-template-columns: auto 1fr;
    grid-template-rows: auto 1fr;
    height: 100vh;
  }

  dccex-band {
    grid-area: band;
  }

  dccex-rail {
    grid-area: rail;
  }

  /* Where everything the page is about goes: one view, which the rail picks
     (issue 169). The rows are the monitor view's, which is the one with two
     things in it — the tiles across the top, and the monitor under them
     taking the rest of it and scrolling its own lines. The tiles take what
     they need and the pane scrolls once there is more in it than fits.

     The monitor's row is minmax(12rem, 1fr) rather than 1fr. A bare 1fr
     grows to fit what is in it, so a long conversation made the pane scroll
     instead of the lines. The floor keeps a few lines in view on a short
     screen, where the pane scrolls to reach it. */
  .work {
    display: grid;
    grid-area: work;
    grid-template-rows: auto minmax(12rem, 1fr);
    min-height: 0;
    overflow: auto;
    background: var(--sl-color-neutral-0);
  }

  /* The releases view is one thing and takes what it needs: a list given the
     height of the pane would put its last row at the foot of the window. */
  .work.releases {
    grid-template-rows: auto;
    align-content: start;
  }

  /* The script view is one thing and takes the whole of the pane: the box in
     it scrolls its own text, so the pane must not scroll instead of it — a
     page of Python under a window that scrolls puts the Apply control below
     the fold. minmax(0, 1fr) rather than 1fr, because a 1fr row grows to fit
     what is in it and a long script is what is in it. */
  .work.script {
    grid-template-rows: minmax(0, 1fr);
    overflow: hidden;
  }

  @media (max-height: ${unsafeCSS(RAIL_TURNS_PX)}px) {
    :host {
      grid-template-areas:
        "band"
        "rail"
        "work";
      grid-template-columns: 1fr;
      grid-template-rows: auto auto 1fr;
    }
  }
`;
