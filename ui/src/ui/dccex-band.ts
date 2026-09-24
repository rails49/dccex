/**
 * The band: the UI's name on the left, and the readings on the right.
 *
 * Two readings and nothing else: whether the station is answering — the
 * **link** — and whether the rails are hot. Both are made of what the station
 * said on the **stream**, decoded on the page and handed down by it (ADR-0008
 * d.2); this component is given them and draws them.
 *
 * **It presses nothing.** `control`'s band commands track power because
 * `layout` checks the railroad is drained before anything reaches the wire,
 * and this page is on no bus for anything to check, so a press here would go
 * down the cable with nothing behind it having checked (ADR-0008 d.5). There
 * is no button on this band and no emergency stop on this chrome, which is why
 * the red token LOOK.md reserves for the first UI to draw one stays unclaimed.
 * The one place a command is typed at the station is the box at the foot of
 * the monitor, and that is an operator typing rather than the chrome
 * commanding a railroad.
 *
 * **The link says so when the station stops answering**, rather than leaving
 * the page looking merely idle — which is the difference between a dead
 * station and a quiet one, and the reason any of this exists. The rails go to
 * `unknown` with it: what the station last said about power is not a reading
 * once the station has stopped talking.
 */

import { LitElement, html, type TemplateResult } from "lit";

import {
  QUIET,
  asOf,
  band,
  type Readings,
  type Shown,
} from "../readings.js";
import { bandStyles } from "./dccex-band.styles.js";

export class DccexBand extends LitElement {
  static override readonly styles = bandStyles;

  static override readonly properties = {
    readings: { attribute: false },
  };

  /** What the page has read off the station.
   *
   * A band nobody has handed readings to reads a station that has said
   * nothing, which is what it is: the link is down and the rails are unknown.
   * It is not a blank band and not a hedge.
   */
  readings: Readings = asOf(QUIET, 0);

  override render(): TemplateResult {
    return html`
      <span class="name">dcc-ex</span>
      <div class="readings">
        ${band(this.readings).map(
          (shown: Shown) => html`
            <span class="reading ${shown.of}">
              <span class="of">${shown.of}</span>
              <span class="reads">${shown.reads}</span>
            </span>
          `,
        )}
      </div>
    `;
  }
}

customElements.define("dccex-band", DccexBand);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-band": DccexBand;
  }
}
