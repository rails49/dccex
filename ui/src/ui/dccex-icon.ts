/**
 * One icon: the path it is handed, drawn at the size and in the colour of
 * whatever it sits in.
 *
 * The paths are `@mdi/js`'s (Apache-2.0), which is a module of strings and no
 * components — so what is imported is the two or three a control names and the
 * bundler leaves the rest. Nothing here knows an icon's name: the caller names
 * the path, which keeps the set the page draws readable at the controls rather
 * than in a table here.
 *
 * It is hidden from the accessibility tree. An icon is a picture of what a
 * control does and the control carries the word — a tooltip and an aria-label
 * — so a shape read out beside it would be the same thing said twice
 * (`dccex-monitor.ts`).
 *
 * It says nothing about the station and holds no state. A component with a
 * property and a template is not worth mounting twice over, and the reason it
 * exists at all is that the alternative is an inline `<svg>` in every control
 * that wants one.
 */

import { LitElement, html, nothing, svg, type TemplateResult } from "lit";

import { iconStyles } from "./dccex-icon.styles.js";

export class DccexIcon extends LitElement {
  static override readonly styles = iconStyles;

  static override readonly properties = {
    path: {},
  };

  /** The shape to draw, as an SVG path on the 24-by-24 grid `@mdi/js` uses.
   *
   *  An icon nobody handed one to draws nothing at all, rather than a box or a
   *  question mark: a control whose icon did not arrive is a bug to see in the
   *  gap and not a shape to guess at. */
  path = "";

  /** The shape is Lit's `svg` template and not its `html` one: a `<path>` put
   *  through the HTML parser comes out an unknown element in the HTML
   *  namespace, which reads the same off a shadow root and draws nothing. */
  override render(): TemplateResult {
    return html`
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        ${this.path === "" ? nothing : svg`<path d=${this.path}></path>`}
      </svg>
    `;
  }
}

customElements.define("dccex-icon", DccexIcon);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-icon": DccexIcon;
  }
}
