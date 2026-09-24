import { css } from "lit";

/**
 * The releases: a row that opens under the tiles, one release to a line.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's four values stay on the chrome.
 *
 * **A release wraps rather than running off the side.** The phone at the
 * layout is where this is read and a **tag** is long: the date and what is
 * said of a release go under the tag when there is no room beside it, so a
 * narrow screen costs a line and never a reading (docs/ui/README.md).
 *
 * **What is on the station is marked twice over.** A word and a weight, not a
 * colour alone: whether the box is up to date is the question the list exists
 * to answer, and a reader who does not see the colour is owed the answer all
 * the same — the same rule the monitor marks the page's own lines by.
 */
export const releasesStyles = css`
  :host {
    display: block;
    box-sizing: border-box;
    padding: 0.5rem;
  }

  details {
    border: 1px solid var(--sl-color-neutral-200);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-50);
  }

  /* What the row is called while it is shut, and the handle that opens it. */
  summary {
    padding: 0.5rem 0.75rem;
    color: var(--sl-color-neutral-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
    cursor: pointer;
  }

  /* What stands in for the rows where there are none: a source that carries
     nothing, or a face that could not be asked. Quiet, because it is the page
     saying what it knows rather than a reading. */
  .says {
    margin: 0;
    padding: 0 0.75rem 0.5rem;
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  .releases {
    margin: 0;
    padding: 0 0.75rem 0.5rem;
    list-style: none;
  }

  /* One release. It wraps: the tag takes what it needs and the date and the
     marks follow it onto the next line at the width of a phone. */
  .release {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
    padding: 0.25rem 0;
    border-top: 1px solid var(--sl-color-neutral-100);
  }

  .release:first-child {
    border-top: none;
  }

  /* The tag: monospaced, because it is a name to be read character by
     character and typed back somewhere else. */
  .tag {
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-small);
    overflow-wrap: anywhere;
  }

  /* When it was published. Quieter than the tag: it is what orders the list
     rather than what a person names a release by. */
  .published {
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
    font-variant-numeric: tabular-nums;
  }

  /* The release the station is running now, and the word saying so. */
  .on .tag {
    font-weight: var(--sl-font-weight-bold);
  }

  .mark {
    color: var(--sl-color-primary-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* A release published with no firmware on it. It is a statement about what
     somebody else published and not a fault of this box's, so it is drawn as
     quietly as the date. */
  .bare {
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
    font-style: italic;
  }
`;
