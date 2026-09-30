import { css, unsafeCSS } from "lit";

import { RAIL_TURNS_PX } from "../look.js";

/**
 * The rail down the left: a column one button wide, and what the buttons land
 * in.
 *
 * Its width is the button's, which is the look rules' minimum for a thumb, so
 * the column is that value and the padding either side of it rather than a
 * number of its own. The buttons are that square exactly: the rail is pressed
 * on the phone at the layout, and a button that fitted its icon rather than a
 * thumb would be the one control a person misses.
 *
 * **Which view is showing is a swap and not a shade.** The chrome's one light
 * is `--band-ink`, so the button for the view in front of the person wears it
 * as a chip with the rail's own green on the glyph, and the other is the ink
 * on the group. Both read: white on `--rail-group` is 3.8 to 1 and
 * `--rail-group` on white is the same, where a control needs 3. Dimming the
 * other button was the alternative and says the wrong thing — a view that can
 * be gone to is not a control that cannot be pressed (`dccex-band.styles.ts`,
 * where the dim ink is what a dead button looks like).
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
     which once their labels are gone. The two views are one run — picking
     what the work pane shows is one thing a person does — and the group's
     green is the gap between them. */
  .group {
    display: flex;
    flex-direction: column;
    gap: 2px;
    border-radius: 6px;
    background: var(--rail-group);
  }

  /* One button per view. The colour reaches the shape through currentColor
     and the font size is what dccex-icon is a multiple of
     (dccex-icon.styles.ts). */
  button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    width: var(--rail-button);
    height: var(--rail-button);
    padding: 0;
    border: none;
    border-radius: 6px;
    background: none;
    color: var(--band-ink);
    font-size: 1.2em;
    cursor: pointer;
  }

  /* The view in front of the person: the chip and the glyph swap, which is
     the difference a reader who cannot tell the two greens apart is left
     with. */
  button[aria-current] {
    background: var(--band-ink);
    color: var(--rail-group);
    cursor: default;
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
