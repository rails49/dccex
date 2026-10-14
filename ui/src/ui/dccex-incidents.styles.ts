import { css } from "lit";

/**
 * The incidents: one row to a line, each opening on the journal lines under
 * it.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (`look.css`). The chrome's colours stay on the chrome.
 *
 * **A row wraps rather than running off the side**, as a **release** row does
 * and for the same reason: the phone at the layout is where this is read, and a
 * stamp, a kind and three numbers are wider than it. A reading goes onto a
 * second line and is never lost (docs/ui/README.md).
 *
 * **The row is a handle and is sized for a thumb.** `--rail-button` is the
 * look rules' minimum for one, which is what a control pressed on a phone held
 * at the layout asks for (`dccex-monitor.styles.ts`).
 *
 * **A routine line is drawn quietly.** It is in the list because somebody
 * asked for it, and what they came for is the incidents: the station's words
 * are monospaced, as they are on the **monitor**, and the row is the ink the
 * dates are.
 */
export const incidentsStyles = css`
  :host {
    display: block;
    box-sizing: border-box;
    padding: 0.5rem;
  }

  .incidents,
  .lines {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  /* One incident. The border is what divides the list rather than a rule
     between every pair of lines inside a row. */
  .incident {
    border-top: 1px solid var(--sl-color-neutral-100);
  }

  .incident:first-child {
    border-top: none;
  }

  /* The handle: everything a row says before it is opened, on one line where
     there is room and wrapped where there is not. */
  summary {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
    box-sizing: border-box;
    min-height: var(--rail-button);
    padding: 0.25rem 0.5rem;
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
    cursor: pointer;
  }

  /* When it happened, on the reader's own clock. Tabular, because a column of
     stamps a person is reading down is a column. */
  .when {
    flex: none;
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    font-variant-numeric: tabular-nums;
  }

  /* Which district, or the word for the station. */
  .district {
    flex: none;
    color: var(--sl-color-neutral-900);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* What kind of incident it is, which is the reading the row exists to
     carry. */
  .kind {
    flex: none;
    color: var(--sl-color-danger-700);
  }

  /* The numbers: how many cuts, the highest current and how long it was cut
     for. Tabular, and quieter than the kind. */
  .trips,
  .milliamps,
  .cut {
    flex: none;
    color: var(--sl-color-neutral-700);
    font-variant-numeric: tabular-nums;
  }

  /* A line no incident took: the station's own words, where an incident has
     its kind. Monospaced, as the conversation is on the monitor. */
  .says {
    flex: 1 1 12rem;
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

  /* The lines the row is made of, under it and indented to say so. */
  .lines {
    padding: 0.25rem 0.5rem 0.5rem 1.5rem;
  }

  /* One journal line: when it arrived, and what the station said, verbatim. */
  .line {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
    padding: 0.125rem 0;
  }

  .said {
    flex: 1 1 12rem;
    min-width: 0;
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-x-small);
    overflow-wrap: anywhere;
  }
`;
