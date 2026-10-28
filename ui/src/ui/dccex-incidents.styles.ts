import { css } from "lit";

/**
 * The incidents: one row to a line, each opening on the journal lines under
 * it, in columns under one heading.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (`look.css`). The chrome's colours stay on the chrome.
 *
 * **Every row is laid on the same columns**, `--columns`, so a column of
 * stamps, kinds or numbers reads down the list. The list is wider than a phone
 * and scrolls sideways inside itself, as the table does
 * (`dccex-counts.styles.ts`); the heading stays at the top while it scrolls.
 *
 * **A routine line is drawn quietly.** It is in the list because somebody
 * asked for it, and what they came for is the incidents: the station's words
 * are monospaced, as they are on the **monitor**, and the row is the ink the
 * dates are.
 */
export const incidentsStyles = css`
  :host {
    --columns: 11rem 4rem 9rem 3rem 5rem 5rem 1fr;

    display: block;
    box-sizing: border-box;
    padding: 0 0.5rem 0.5rem;
  }

  .incidents,
  .lines {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  /* The heading and every row: the same columns, at least as wide as the
     pane. */
  .head,
  summary,
  .line {
    display: grid;
    grid-template-columns: var(--columns);
    align-items: baseline;
    column-gap: 0.5rem;
    min-width: max-content;
    box-sizing: border-box;
    padding: 0.125rem 0.5rem;
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* What each column is, quieter than what is under it, and on top of the
     rows as they scroll under it. */
  .head {
    position: sticky;
    top: 0;
    z-index: 1;
    padding-top: 0.5rem;
    border-bottom: 1px solid var(--sl-color-neutral-200);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    font-weight: var(--sl-font-weight-semibold);
  }

  summary {
    cursor: pointer;
  }

  /* The numbers and their headings sit against the right of the column. */
  .heading:nth-child(n + 4),
  .trips,
  .milliamps,
  .cut {
    text-align: right;
  }

  /* When it happened, on the reader's own clock. Tabular, because a column of
     stamps a person is reading down is a column. */
  .when {
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    font-variant-numeric: tabular-nums;
  }

  /* Which district, or the word for the station. */
  .district {
    color: var(--sl-color-neutral-900);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* What kind of incident it is, which is the reading the row exists to
     carry. */
  .kind {
    color: var(--sl-color-danger-700);
  }

  /* The numbers: how many cuts, the highest current and how long it was cut
     for. Tabular, and quieter than the kind. */
  .trips,
  .milliamps,
  .cut {
    color: var(--sl-color-neutral-700);
    font-variant-numeric: tabular-nums;
  }

  /* A line no incident took: the station's own words across the columns an
     incident has its kind and numbers in. Monospaced, as the conversation is
     on the monitor. */
  .says {
    grid-column: 3 / -1;
    min-width: 0;
    color: var(--sl-color-neutral-600);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-x-small);
    overflow-wrap: anywhere;
  }

  /* A routine row is quieter than an incident, because it is in the list for
     somebody who asked for it rather than for everybody. */
  .routine .district {
    color: var(--sl-color-neutral-600);
    font-weight: var(--sl-font-weight-normal);
  }

  /* The lines the row is made of, under it: the stamp in the stamp's column
     and the station's words where a routine row has them. */
  .lines {
    padding-bottom: 0.25rem;
  }

  .said {
    grid-column: 3 / -1;
    min-width: 0;
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-x-small);
    overflow-wrap: anywhere;
  }
`;
