/**
 * The band and the rail, as look's elements (ADR-0023).
 *
 * Templates and not components: look draws them, and what this page decides
 * is what goes in them. `dccex-app` puts both in its `look-shell` and listens
 * there for `look-view` and `look-power`.
 */

import "@rails49/look";
import { html, nothing, type TemplateResult } from "lit";

import { band, type Layout, type Readings } from "../readings.js";
import { DRAWN, VIEWS, type View } from "../view.js";

/** The band: the UI name, the railroad `control` has loaded, the **link**
 *  and track power (docs/ui/README.md). The **build** is the releases view's
 *  and not the band's (ADR-0027).
 *
 *  What it says is `readings.js`'s `band()`. Power is `layout`'s row. Both
 *  presses are dead on one rule, so one `reason` holds both and is their
 *  tooltip (ADR-0026 d.4). */
export function drawBand(readings: Readings, layout: Layout): TemplateResult {
  const { railroad, answering, says, stop } = band(readings, layout);
  return html`
    <look-band ui="dccex">
      ${railroad === ""
        ? nothing
        : html`<look-reading>${railroad}</look-reading>`}
      <look-dot state=${answering ? "up" : "down"}
        >${answering ? nothing : says}</look-dot
      >
      <look-power
        state=${layout.power ?? "off"}
        reason=${stop.wants === null ? stop.title : ""}
      ></look-power>
    </look-band>
  `;
}

/** The rail: one `look-view` per **view**, the one showing marked current.
 *  Choosing another fires `look-view`; the page writes the hash, and the view
 *  comes back down from it (`view.ts`). */
export function drawRail(view: View): TemplateResult {
  return html`
    <look-rail>
      ${VIEWS.map(
        (each: View) => html`
          <look-view
            name=${each}
            icon=${DRAWN[each].icon}
            label=${DRAWN[each].label}
            ?current=${each === view}
          ></look-view>
        `,
      )}
    </look-rail>
  `;
}
