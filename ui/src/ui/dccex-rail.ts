/**
 * The rail: what the current view offers.
 *
 * What it offers is the other **view**. There are two — the **monitor** and
 * the releases — and one button each, in a run of their own (CONTEXT.md, issue
 * 166, issue 169). Each is drawn as an icon carrying the view's own word as a
 * tooltip and as a label, so the word is there for a reader who is not reading
 * the shape (issue 167); the word is the glossary's, which is what the page
 * calls the thing everywhere else.
 *
 * The flash's are not them: a flash is a gesture about one **release**, so it
 * is pressed on that release's row where the tag it names is, and a button
 * here would be one with no release named (#9, `dccex-releases.ts`).
 *
 * **It picks nothing itself.** Which view is in front of a person is kept in
 * the page's hash, so a press is handed up and comes back down as `view` when
 * the page has read the hash again (`view.ts`, `dccex-app.ts`). One direction
 * each, and no second answer to which view is showing — a rail that set its
 * own would draw one thing while the work pane drew another for as long as
 * the two disagreed.
 *
 * It is half of the chrome every rails49 UI wears, and it is what turns into a
 * strip on a short window; the buttons lie down with it.
 */

import { mdiConsole, mdiFlashAlert } from "@mdi/js";
import { LitElement, html, nothing, type TemplateResult } from "lit";

import { OPENS, VIEWS, type View } from "../view.js";
import "./dccex-icon.js";
import { railStyles } from "./dccex-rail.styles.js";

/** The shape each view is drawn as: a console for the station's conversation,
 *  and a firmware warning for the releases, which is where one is written onto
 *  the station.
 *
 *  The paths are named here rather than in `dccex-icon`, which knows no icon's
 *  name (issue 167). It is a record over `View`, so a third view is a shape
 *  the type checker asks for rather than a button with nothing on it. */
const DRAWN: Record<View, string> = {
  monitor: mdiConsole,
  releases: mdiFlashAlert,
};

export class DccexRail extends LitElement {
  static override readonly styles = railStyles;

  static override readonly properties = {
    view: { attribute: false },
    picks: { attribute: false },
  };

  /** Which view the work pane is showing, as the page hands it down.
   *
   *  A rail nobody has told reads the view a page opens on, which is what a
   *  page with nothing in its hash is showing. */
  view: View = OPENS;

  /** What picks a view, as the page hands it down.
   *
   *  A rail nobody handed one to picks nothing: the hash is the page's, and a
   *  piece of chrome that wrote it would be a second thing deciding what the
   *  work pane shows. */
  picks: (view: View) => void = () => {};

  override render(): TemplateResult {
    return html`
      <div class="group">
        ${VIEWS.map(
          (view: View) => html`
            <button
              type="button"
              class=${view}
              title=${view}
              aria-label=${view}
              aria-current=${view === this.view ? "page" : nothing}
              @click=${() => {
                this.picks(view);
              }}
            >
              <dccex-icon .path=${DRAWN[view]}></dccex-icon>
            </button>
          `,
        )}
      </div>
    `;
  }
}

customElements.define("dccex-rail", DccexRail);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-rail": DccexRail;
  }
}
