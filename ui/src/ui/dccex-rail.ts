/**
 * The rail: what the current view offers.
 *
 * It offers nothing. What is here is the column itself, one button wide, and
 * the run the first buttons land in. The flash's are not them: a flash is a
 * gesture about one **release**, so it is pressed on that release's row where
 * the tag it names is, and a button here would be one with no release named
 * (#9, `dccex-releases.ts`). A rail with no buttons is still the rail: it is
 * half of the chrome every rails49 UI wears, and it is what turns into a strip
 * on a short window.
 */

import { LitElement, html, type TemplateResult } from "lit";

import { railStyles } from "./dccex-rail.styles.js";

export class DccexRail extends LitElement {
  static override readonly styles = railStyles;

  override render(): TemplateResult {
    return html`<div class="group"></div>`;
  }
}

customElements.define("dccex-rail", DccexRail);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-rail": DccexRail;
  }
}
