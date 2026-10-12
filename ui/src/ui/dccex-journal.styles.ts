import { css } from "lit";

/**
 * The journal view: the controls, the counts and the incidents, in that order
 * down the pane.
 *
 * It is the work pane's rather than the chrome's, so its colours are
 * Shoelace's theme tokens and it follows the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's six colours stay on the chrome.
 *
 * **The controls stay where they are and the list scrolls under them.** A
 * journal is as long as the evening was, and a reader at the foot of it still
 * has the reload and the period where they were. Nothing here scrolls
 * sideways: the table is what is wider than a phone and it scrolls inside
 * itself (`dccex-counts.styles.ts`).
 */
export const journalStyles = css`
  :host {
    display: grid;
    grid-template-rows: auto auto 1fr;
    min-height: 0;
    overflow: hidden;
  }

  /* What is read: the rows, under everything that says which rows they are. */
  dccex-incidents {
    min-height: 0;
    overflow-y: auto;
  }

  /* A journal with nothing in it, or one the face would not serve. Quiet,
     because it is the page saying what it knows rather than a reading. */
  .empty {
    margin: 0;
    padding: 0.5rem;
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }
`;
