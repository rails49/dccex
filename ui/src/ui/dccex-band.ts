/**
 * The band: the UI's name and the **build** on the left, and on the right the
 * **link** and the power button.
 *
 * What it draws is `readings.js`'s `band()` — the build the station says it is
 * running, whether the station is answering, the words that go with a link that
 * is down, and what the power button reads, is titled and asks for. This
 * component is given all of it and draws it; it works out no reading of its
 * own.
 *
 * **It asks `layout` for power** (ADR-0017, superseding ADR-0011 d.1). A press
 * used to send `<1>` or `<0>` through the **face**, which skipped `layout` and
 * the **translator** — and `layout` is what refuses an OFF while a run is going
 * and zeroes every locomotive's speed before a cut (`control` ADR-0062). So a
 * press publishes `tc49/layout/power_wanted` through the `wants` the page hands
 * down, and the chip the button wears is the row `layout` reports back: green
 * for `on`, an outlined chip for `off`, red for `stopped`. Nothing about power
 * goes up the stream, and this component holds no bus of its own — the
 * connection is the page's (`bus.ts`, `dccex-app.ts`).
 *
 * It is the only control on this chrome and the only press on the page that
 * asks for power outside the flash sequence's own step (ADR-0011 d.3, which
 * stands). The page asks for no confirmation: the guard is `layout` and then
 * the operator (ADR-0006).
 *
 * **It presses nothing without the broker, the station and a word from
 * `layout`** (ADR-0017 d.3, issue 205): the button is a dim glyph with no
 * chip, and its title says which of the three is missing — `no bus`, `no
 * station`, `no layout`.
 *
 * **The link says so when the station stops answering**, rather than leaving
 * the page looking merely idle — which is the difference between a dead
 * station and a quiet one, and the reason any of this exists. It is a dot, red
 * with `dcc-ex offline` beside it while the station is not answering and green
 * alone while it is: a fault is owed a sentence, and a station that is
 * answering is owed a glance (issue 168, and issue 138 for the red). The words
 * are the dot's label in either state, so a reader who cannot see it is told
 * which reading it is. The build goes blank with the link: what the station
 * last said is not a reading once the station has stopped talking.
 */

import { mdiPower } from "@mdi/js";
import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  QUIET,
  UNREACHABLE,
  asOf,
  band,
  type Layout,
  type Readings,
} from "../readings.js";
import { bandStyles } from "./dccex-band.styles.js";
import "./dccex-icon.js";

export class DccexBand extends LitElement {
  static override readonly styles = bandStyles;

  static override readonly properties = {
    readings: { attribute: false },
    layout: { attribute: false },
    wants: { attribute: false },
  };

  /** What the page has read off the station.
   *
   * A band nobody has handed readings to reads a station that has said
   * nothing, which is what it is: the link is down and the build is blank. It
   * is not a blank band and not a hedge.
   */
  readings: Readings = asOf(QUIET, 0);

  /** What the page has read off the bus: whether it has the broker, and what
   *  `layout` reports the railroad's power as (ADR-0017 d.2).
   *
   *  A band nobody has handed one to has not reached the broker, which is what
   *  a page has until it answers (`bus.ts`).
   */
  layout: Layout = UNREACHABLE;

  /** What asks `layout` for power, as the page hands it down.
   *
   *  A band nobody handed one to presses nothing: the connection to the broker
   *  is the page's, and a pane that opened one of its own would be a second
   *  client of `control`'s broker for one page (`dccex-app.ts`).
   */
  wants: (power: string) => void = () => {};

  override render(): TemplateResult {
    const { build, answering, says, power } = band(this.readings, this.layout);
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
          class="power ${power.reads ?? ""}"
          title=${power.title}
          aria-label=${power.title}
          ?disabled=${power.wants === null}
          @click=${() => {
            this.#presses(power.wants);
          }}
        >
          <dccex-icon .path=${mdiPower}></dccex-icon>
        </button>
      </div>
    `;
  }

  /** Ask for what a press of the power button asks for.
   *
   *  Nothing where there is nothing to ask for. A disabled button fires no
   *  click, so this is the same answer said twice — and the one that does not
   *  rest on the browser honouring an attribute.
   */
  #presses(wants: string | null): void {
    if (wants !== null) {
      this.wants(wants);
    }
  }
}

customElements.define("dccex-band", DccexBand);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-band": DccexBand;
  }
}
