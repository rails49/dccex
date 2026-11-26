import { css } from "lit";

/** Where the log goes from below the editor to beside it. The script view's
 *  sheet lays the two out on the same query (`dccex-script.styles.ts`). */
export const ACROSS = "(min-width: 1100px)";

/**
 * The divider between the editor and the log. Its size and what a pointer
 * does to it are `look-gap`'s. The host is the grey behind the gap at rest.
 * The host is a grid, and the gap fills it.
 */
export const dividerStyles = css`
  :host {
    display: grid;
    flex: none;
    background: var(--sl-color-neutral-200);
  }
`;
