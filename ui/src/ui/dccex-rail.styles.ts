import { css, unsafeCSS } from "lit";

import { RAIL_TURNS_PX } from "../look.js";

/**
 * The rail down the left: a column one button wide, and what the buttons land
 * in.
 *
 * Its width is the button's, which is the look rules' minimum for a thumb, so
 * the column is that value and the padding either side of it rather than a
 * number of its own.
 *
 * Below `--rail-turns` the window is too short for a column at all — a phone
 * held sideways — and the rail lies down along the top of the work instead.
 * `dccex-app.styles.ts` gives it the row to lie in and this turns its own
 * contents; the height is one number interpolated into both (`look.ts`),
 * because turning at two heights would draw the strip inside a column that is
 * still there.
 */
export const railStyles = css`
  :host {
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 4px;
    width: calc(var(--rail-button) + 8px);
    background: var(--rail);
  }

  /* A run of buttons that belong together: what says which commands go with
     which once their labels are gone. The rail has nothing on it yet, and a
     run with nothing in it takes no room and shows nothing. */
  .group {
    display: flex;
    flex-direction: column;
    gap: 2px;
    border-radius: 6px;
    background: var(--rail-group);
  }

  @media (max-height: ${unsafeCSS(RAIL_TURNS_PX)}px) {
    :host {
      flex-direction: row;
      width: auto;
      height: calc(var(--rail-button) + 8px);
    }

    .group {
      flex-direction: row;
    }
  }
`;
