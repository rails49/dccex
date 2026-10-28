import { css, unsafeCSS } from "lit";

/** Where the log goes from below the editor to beside it. The script view's
 *  sheet lays the two out on the same query (`dccex-script.styles.ts`). */
export const ACROSS = "(min-width: 1100px)";

/**
 * The divider between the editor and the log: a bar to grab, across the room
 * below the editor and down it beside the editor. It is drawn in the theme's
 * neutral ink, and in the primary ink while it has the keyboard.
 */
export const dividerStyles = css`
  :host {
    flex: none;
    box-sizing: border-box;
    height: 0.75rem;
    margin: 0.125rem 0;
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-200);
    cursor: row-resize;
    touch-action: none;
  }

  @media ${unsafeCSS(ACROSS)} {
    :host {
      width: 0.75rem;
      height: auto;
      margin: 0 0.125rem;
      cursor: col-resize;
    }
  }

  :host(:hover) {
    background: var(--sl-color-neutral-300);
  }

  :host(:focus-visible) {
    outline: 2px solid var(--sl-color-primary-600);
  }
`;
