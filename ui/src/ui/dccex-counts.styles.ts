import { css } from "lit";

/**
 * The statistics table: a column per count and a row per district.
 *
 * It is the work pane's rather than the chrome's, so its colours are
 * Shoelace's theme tokens and it follows the system's light or dark setting
 * (`look.css`). The chrome's colours stay on the chrome.
 *
 * **It scrolls sideways inside itself and never takes the page with it.** The
 * columns are the kinds and the counts and there are a dozen of them, which is
 * wider than the phone at the layout: a table that made the page scroll would
 * put the **rail** off the side of the screen (docs/ui/README.md; the issue
 * that holds the widths is named there rather than here, because an issue
 * number in the hundreds is three hex digits and the colour scan
 * (`tests/ui/paths.py`) reads one in a sheet as a colour).
 *
 * **The numbers are tabular and the headings are quiet.** A column a person
 * reads down is a column, and what they are reading down is the counts rather
 * than the words over them.
 */
export const countsStyles = css`
  :host {
    display: block;
    box-sizing: border-box;
    max-width: 100%;
    padding: 0.5rem;
    overflow-x: auto;
  }

  table {
    border-collapse: collapse;
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* What each column is. Quieter than the counts under it, and it wraps at
     nothing: a kind on two lines is two columns to a reader
     glancing at the head of the table. */
  .heading {
    padding: 0.25rem 0.5rem;
    border-bottom: 1px solid var(--sl-color-neutral-200);
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    font-weight: var(--sl-font-weight-semibold);
    text-align: right;
    white-space: nowrap;
  }

  .heading:first-child {
    text-align: left;
  }

  /* The district's letter, or the word for the station: what the row is
     about. */
  .name {
    padding: 0.25rem 0.5rem;
    border-top: 1px solid var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
    font-weight: var(--sl-font-weight-semibold);
    text-align: left;
    white-space: nowrap;
  }

  /* One count. Tabular, so a column of them lines up, and right-aligned
     against the heading it is under. */
  .count {
    padding: 0.25rem 0.5rem;
    border-top: 1px solid var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
    font-variant-numeric: tabular-nums;
    text-align: right;
    white-space: nowrap;
  }

  /* The station's two sentences. Words rather than counts, so they read from
     the left like the name beside them. */
  .says {
    padding: 0.25rem 0.5rem;
    border-top: 1px solid var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-700);
    text-align: left;
    white-space: nowrap;
  }
`;
