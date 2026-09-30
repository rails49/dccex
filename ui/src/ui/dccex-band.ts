/**
 * The band: the UI's name and the **build** on the left, and on the right the
 * **link** and the power button.
 *
 * What it draws is `readings.js`'s `band()` — the build the station says it is
 * running, whether the station is answering, the words that go with a link that
 * is down, and what the power button is, says and sends. Every one of them is
 * made of what the station said on the **stream**, decoded on the page and
 * handed down by it (ADR-0008 d.2); this component is given them and draws
 * them.
 *
 * **It presses power** (ADR-0011, superseding ADR-0008 d.5). `control`'s band
 * presses it because `layout` checks the railroad is drained first, and that
 * check never guarded the station: any client of the mirror's port sends `<0>`
 * or `<1>`, the box at the foot of the monitor included, and the guard is the
 * operator (ADR-0006). So the button is a reading and a control at once —
 * green where any track is on and a press cuts the power, red where every one
 * is off and a press turns it on — and it goes up the stream the way anything
 * typed does, through the `sends` the page hands down. It is the only control
 * on this chrome and the only press on the page that commands power outside
 * the flash sequence's own step (ADR-0011 d.3). The page asks for no
 * confirmation (ADR-0011 d.4).
 *
 * **It presses nothing while the link is down** (ADR-0011 d.2): the button is
 * grey and disabled, because power is then unknown and a press would reach a
 * station that is not answering.
 *
 * **The link says so when the station stops answering**, rather than leaving
 * the page looking merely idle — which is the difference between a dead
 * station and a quiet one, and the reason any of this exists. It is a dot, red
 * with `dcc-ex offline` beside it while the station is not answering and green
 * alone while it is: a fault is owed a sentence, and a station that is
 * answering is owed a glance (issue 168, and issue 138 for the red). The words
 * are the dot's label in either state, so a reader who cannot see it is told
 * which reading it is. The build goes blank with the link, and the power button
 * greys: what the station last said is not a reading once the station has
 * stopped talking.
 */

import { mdiPower } from "@mdi/js";
import { LitElement, html, nothing, type TemplateResult } from "lit";

import { QUIET, asOf, band, type Readings } from "../readings.js";
import { bandStyles } from "./dccex-band.styles.js";
import "./dccex-icon.js";

export class DccexBand extends LitElement {
  static override readonly styles = bandStyles;

  static override readonly properties = {
    readings: { attribute: false },
    sends: { attribute: false },
  };

  /** What the page has read off the station.
   *
   * A band nobody has handed readings to reads a station that has said
   * nothing, which is what it is: the link is down, the build is blank and the
   * power button presses nothing. It is not a blank band and not a hedge.
   */
  readings: Readings = asOf(QUIET, 0);

  /** What puts a message up the **stream**, as the page hands it down.
   *
   *  A band nobody handed one to presses nothing: the stream is the page's, and
   *  a pane that opened one of its own would be a second client of the mirror's
   *  port for one page (`dccex-app.ts`).
   */
  sends: (typed: string) => string | null = () => null;

  override render(): TemplateResult {
    const { build, answering, says, power } = band(this.readings);
    return html`
      <div class="about">
        <span class="name">dcc-ex</span>
        <span class="build">${build}</span>
      </div>
      <div class="readings">
        <span class="link" role="img" aria-label=${says}>
          <span class="dot ${answering ? "on" : "off"}"></span>
          ${answering ? nothing : html`<span class="says">${says}</span>`}
        </span>
        <button
          type="button"
          class="power ${power.hot === null ? "" : power.hot ? "on" : "off"}"
          title=${power.does}
          aria-label=${power.does}
          ?disabled=${power.sends === null}
          @click=${() => {
            this.#presses(power.sends);
          }}
        >
          <dccex-icon .path=${mdiPower}></dccex-icon>
        </button>
      </div>
    `;
  }

  /** Send what a press of the power button sends.
   *
   *  Nothing where there is nothing to send. A disabled button fires no click,
   *  so this is the same answer said twice — and the one that does not rest on
   *  the browser honouring an attribute.
   */
  #presses(sends: string | null): void {
    if (sends !== null) {
      this.sends(sends);
    }
  }
}

customElements.define("dccex-band", DccexBand);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-band": DccexBand;
  }
}
