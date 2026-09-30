import { css } from "lit";

/**
 * The icon: a square the size of the text around it, in the colour of it.
 *
 * It paints nothing of its own. The shape takes `currentColor`, so an icon
 * inside a control is the colour that control already is and the chrome's six
 * colours stay where they are written (`ui/look/README.md`). The size is `em`
 * for the same reason: a caller sets the font size and the icon follows, so
 * there is no second place a control's size is decided.
 */
export const iconStyles = css`
  :host {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 0;
  }

  svg {
    width: 1.5em;
    height: 1.5em;
  }
`;
