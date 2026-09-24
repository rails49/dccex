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

  /* Where everything the page is about goes: the tiles across the top, the
     releases under them, and the monitor under those, which takes the rest of
     it and scrolls its own lines. The first two take what they need and the
     pane scrolls once there is more in it than fits. */
  .work {
    display: grid;
    grid-area: work;
    grid-template-rows: auto auto 1fr;
    min-height: 0;
    overflow: auto;
    background: var(--sl-color-neutral-0);
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
