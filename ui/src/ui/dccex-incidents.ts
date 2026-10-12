/**
 * The **incident**s on the **journal** view: newest first, each opening on the
 * journal lines it is made of.
 *
 * A row is what a person came to the view for — when it happened, which
 * district, which kind, how many times the station cut it, the highest current
 * it printed and how long it was cut for — and pressing it shows the station's
 * own words, so nobody has to read the file to see what the reading was made
 * of (ADR-0022 d.3; the issue these words were written for is named in
 * `docs/ui/README.md` and in `incidents.js` rather than here, because an issue
 * number in the hundreds is three hex digits and `tests/ui/test_look.py`'s
 * scan reads one in a component as a colour). Which lines those are is the
 * reading module's: an incident names them, and the flip a short outlived is
 * one of them.
 *
 * **The reading and every word of it are `incidents.js`'s.** The order, the
 * stamps, the kinds and the numbers come down as strings and this component
 * draws them, as the **tile**s and the **release**s are drawn — so what an
 * operator reads is asserted by running that module and what is asserted here
 * is that it lands on the row it is about (`tests/ui/test_incidents.py`,
 * `ui/test/incidents.test.ts`).
 *
 * **A routine line is a row of the same shape with nothing counted on it.** A
 * flip nothing came of and the power going on and off are the railroad working
 * and are not incidents (CONTEXT.md, **incident**); they are drawn only when a
 * reader asks for them, which is the toggle on the controls, and they carry
 * the station's words where an incident carries its kind.
 *
 * **The instant is on the row and not only in the stamp.** The time is drawn
 * on the reader's own clock, and the stamp the line carries rides on the
 * element's `datetime`, so nothing about when something happened is lost to the
 * formatting — the rule the **monitor** draws a line by (`monitor.js`).
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import { type Entry, type Said } from "../incidents.js";
import { incidentsStyles } from "./dccex-incidents.styles.js";

export class DccexIncidents extends LitElement {
  static override readonly styles = incidentsStyles;

  static override readonly properties = {
    entries: { attribute: false },
  };

  /** The rows, newest first, as the reading module hands them over. A list
   *  nobody has handed rows to draws none: what stands in their place is the
   *  view's own sentence (`dccex-journal.ts`). */
  entries: readonly Entry[] = [];

  override render(): TemplateResult {
    return html`
      <ol class="incidents">
        ${this.entries.map(
          (entry: Entry) => html`
            <li class=${entry.routine ? "incident routine" : "incident"}>
              <details>
                <summary>
                  <time class="when" datetime=${entry.at}>${entry.when}</time>
                  <span class="district">${entry.district}</span>
                  ${entry.routine
                    ? html`<span class="says">${entry.says}</span>`
                    : html`<span class="kind">${entry.kind}</span>
                        <span class="trips">${entry.trips}</span>
                        <span class="milliamps">${entry.milliamps}</span>
                        <span class="cut">${entry.cut}</span>`}
                </summary>
                ${this.#lines(entry)}
              </details>
            </li>
          `,
        )}
      </ol>
    `;
  }

  /** The journal lines the row is made of, as the station wrote them.
   *
   * Verbatim, because the whole point of opening a row is reading what the
   * station said rather than what the page made of it (ADR-0022 d.2). A row
   * with one line in it is its own line, which is what a routine row is.
   */
  #lines(entry: Entry): TemplateResult | typeof nothing {
    if (entry.lines.length === 0) {
      return nothing;
    }
    return html`
      <ol class="lines">
        ${entry.lines.map(
          (line: Said) => html`
            <li class="line">
              <time class="when" datetime=${line.at}>${line.when}</time>
              <span class="said">${line.said}</span>
            </li>
          `,
        )}
      </ol>
    `;
  }
}

customElements.define("dccex-incidents", DccexIncidents);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-incidents": DccexIncidents;
  }
}
