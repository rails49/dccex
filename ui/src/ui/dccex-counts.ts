/**
 * The statistics table at the top of the **journal** view: one row per
 * district, and one for the station.
 *
 * What the numbers are and what words they are drawn in is `incidents.js`'s —
 * a pure function of the journal and the period (ADR-0022 d.5) — and this
 * component is handed a heading and a row of words and draws them, as the
 * **tile**s are handed their readings. A cell is one string: a table that
 * decided which number went in which column would be a second answer to what
 * a column means.
 *
 * **The station has a row of its own** because the link going down and the
 * station restarting are about no district (CONTEXT.md, **station**). It is
 * the two counts in words rather than numbers under the district columns:
 * there is no trip, no peak and no rate to put there, and a zero in those
 * columns would be a reading nobody took (ADR-0009 d.2).
 *
 * **It presses nothing.** The period, the toggle, the reload and the clear are
 * the controls' (`dccex-controls.ts`), and a table that offered one of them
 * would be a second place this view is driven from.
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import { HEADINGS, type Row, type Standing } from "../incidents.js";
import { countsStyles } from "./dccex-counts.styles.js";

/** How many columns the station's two sentences lie across: everything after
 *  the first of them, so the row ends where the districts' rows do. */
const SPANNED = HEADINGS.length - 2;

export class DccexCounts extends LitElement {
  static override readonly styles = countsStyles;

  static override readonly properties = {
    districts: { attribute: false },
    station: { attribute: false },
  };

  /** One row per district the journal names, A first, as the reading module
   *  hands them over. A table nobody has handed rows to draws the headings and
   *  no rows, which is what a page that has read nothing has to show. */
  districts: readonly Row[] = [];

  /** The station's own row: the link losses and the restarts, in words. */
  station: Standing | null = null;

  override render(): TemplateResult {
    return html`
      <table>
        <thead>
          <tr>
            ${HEADINGS.map(
              (heading: string) =>
                html`<th scope="col" class="heading">${heading}</th>`,
            )}
          </tr>
        </thead>
        <tbody>
          ${this.districts.map(
            (row: Row) => html`
              <tr class="district">
                <th scope="row" class="name">${row.district}</th>
                ${row.cells.map(
                  (cell: string) => html`<td class="count">${cell}</td>`,
                )}
              </tr>
            `,
          )}
          ${this.#station()}
        </tbody>
      </table>
    `;
  }

  /** The station's row, where there is one to draw. */
  #station(): TemplateResult | typeof nothing {
    const station = this.station;
    if (station === null) {
      return nothing;
    }
    const [links, restarts] = station.says;
    return html`
      <tr class="station">
        <th scope="row" class="name">${station.district}</th>
        <td class="says links">${links}</td>
        <td class="says restarts" colspan=${SPANNED}>${restarts}</td>
      </tr>
    `;
  }
}

customElements.define("dccex-counts", DccexCounts);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-counts": DccexCounts;
  }
}
