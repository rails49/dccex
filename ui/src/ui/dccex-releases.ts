/**
 * The releases: every **release** the box is configured to read, in a row that
 * opens under the tiles.
 *
 * Newest first, each with the day it was published, the one that is on the
 * station now marked as such, and a release with no firmware on it saying so
 * (#8, docs/ui/README.md). The ordering, the dates and the mark are the
 * listing module's — a pure function of what the **face** answered and what
 * the station said (`releases.js`) — and this component is handed them and
 * draws them, as the tiles are handed their readings.
 *
 * **It is collapsed.** What the page is when nobody has asked about firmware
 * is the station's particulars and its conversation; the releases are a thing
 * to go and look at, and a list that pushed the monitor down the screen would
 * cost every reader for the sake of the one asking.
 *
 * **Nothing here flashes anything** (#8). Choosing a release cuts track power
 * and resets the station, and the page asks the operator through that sequence
 * first, because nothing behind the page guards a railroad (ADR-0006). That is
 * its own ticket's, and what may not exist before it is a control on this row
 * that writes a station.
 *
 * **And nothing here fetches.** The page asks the face and hands the answer
 * down, as it does with the conversation: a pane of the page holding its own
 * counterparty would be a second answer to what the page knows (ADR-0002,
 * `dccex-app.ts`).
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  NO_FIRMWARE,
  ON_STATION,
  type Carried,
  type Listed,
  listing,
} from "../releases.js";
import { releasesStyles } from "./dccex-releases.styles.js";

/** What the row is called while it is shut. The word is the glossary's
 *  (CONTEXT.md, **release**): what is published elsewhere and can be written
 *  onto the station, which is not what the station is running now — that is
 *  the **build**, and it is a tile. */
const HEADING = "releases";

export class DccexReleases extends LitElement {
  static override readonly styles = releasesStyles;

  static override readonly properties = {
    carried: { attribute: false },
    build: { attribute: false },
  };

  /** What the face answered, or `null` where it could not be asked. A row
   *  nobody has handed a list to says the releases could not be read, which is
   *  what a page that has not been told anything has to show. */
  carried: Carried[] | null = null;

  /** What the station says it is running, off the `G-` field of its banner. It
   *  goes with the **link**: a station that is not answering has no build and
   *  nothing is marked (ADR-0008 d.3). */
  build: string | null = null;

  override render(): TemplateResult {
    const shown = listing(this.carried, this.build);
    return html`
      <details>
        <summary>${HEADING}</summary>
        ${shown.says === ""
          ? nothing
          : html`<p class="says">${shown.says}</p>`}
        <ol class="releases">
          ${shown.rows.map(
            (release: Listed) => html`
              <li class=${release.onStation ? "release on" : "release"}>
                <span class="tag">${release.tag}</span>
                <span class="published">${release.published}</span>
                ${release.onStation
                  ? html`<span class="mark">${ON_STATION}</span>`
                  : nothing}
                ${release.flashable
                  ? nothing
                  : html`<span class="bare">${NO_FIRMWARE}</span>`}
              </li>
            `,
          )}
        </ol>
      </details>
    `;
  }
}

customElements.define("dccex-releases", DccexReleases);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-releases": DccexReleases;
  }
}
