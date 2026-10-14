/**
 * The **journal** view: what the station said about power, read afterwards.
 *
 * The **translator** keeps the journal on the box whether or not anyone is
 * watching, and the mirror's **face** serves the file as it stands (ADR-0022
 * d.1, d.4). This view is where it is read: the controls above, the counts per
 * district under them, and the **incident**s below that, newest first, each
 * opening on the lines it is made of.
 *
 * **It asks on opening and on the reload, and never on a schedule.** The page
 * takes this pane out of the document when another **view** is showing, so
 * coming to the journal is what asks the face for it (`dccex-app.ts`). A record
 * read afterwards is not a reading that moves under the eye, and a view polling
 * for a file that grows all evening would be asking the box for a megabyte a
 * minute to redraw the same rows (ADR-0010).
 *
 * **What it draws is one reading of the whole file** (ADR-0022 d.5,
 * `incidents.js`). The lines, the period, the counts, the rows and every word
 * on them come out of one call, so the table and the list cannot disagree about
 * what happened. The period is the reader's: the last day, the last week, the
 * whole file, or one **build** the journal carries — and the two spans are
 * counted back from when the face answered rather than from the draw, so the
 * rows do not move under somebody reading them.
 *
 * **A journal with nothing in it and a journal nobody could read are different
 * sentences** (ADR-0009 d.2). The first is a railroad that has said nothing
 * about power — an ordinary state of a box that has just come up — and the
 * second is a page that has not been told. Neither draws a table: a row of
 * zeros for a file nobody read would be a count nobody made.
 *
 * **Nothing here changes the file.** The translator keeps it to a size
 * itself (ADR-0022 d.4).
 *
 * **And nothing here fetches.** The page asks the face and hands this pane the
 * two asks, as it does with the releases and the **script**: a pane holding its
 * own counterparty would be a second answer to what the page talks to (the
 * organisation's ADR-0002).
 */

import { lookTheme } from "@rails49/look";
import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  ALL,
  EMPTY,
  UNREADABLE,
  type Served,
  choices,
  over,
  shown,
} from "../incidents.js";
import "./dccex-controls.js";
import "./dccex-counts.js";
import "./dccex-incidents.js";
import { journalStyles } from "./dccex-journal.styles.js";

export class DccexJournal extends LitElement {
  static override readonly styles = [lookTheme, journalStyles];

  static override readonly properties = {
    reads: { attribute: false },
    served: { state: true },
    answered: { state: true },
    choice: { state: true },
    routine: { state: true },
  };

  /** What asks the face for the journal, as the page hands it down (`face.ts`).
   *
   *  A pane nobody handed one to reads nothing, which is what a page with no
   *  way to ask has to show: the journal could not be read (ADR-0009 d.2). */
  reads: () => Promise<Served | null> = () => Promise.resolve(null);

  /** What the face served, or `null` where it did not. */
  served: Served | null = null;

  /** Whether an ask has come back at all. It is what tells a journal nobody
   *  has asked for yet from one the face would not serve: the first is a view
   *  that has nothing to say, and the second is a sentence. */
  answered = false;

  /** Which period is read. The whole file to begin with, which is the question
   *  somebody opening the view is asking. */
  choice: string = ALL;

  /** Whether the lines no incident took are rows as well. */
  routine = false;

  /** When the face answered, on the page's clock.
   *
   *  It is what the last day and the last week are counted back from, and it
   *  is taken once per ask rather than at every draw: a span measured from the
   *  draw would drop a line out of the bottom of the list while somebody was
   *  reading it. It is not reactive — what a draw reads is `served`, which
   *  arrives with it. */
  #at = 0;

  /** Whether an ask is out already. One at a time, so two answers cannot
   *  arrive out of order and leave the older one on the page — the defect the
   *  count of **client**s had (#88, `dccex-app.ts`). */
  #asking = false;

  override connectedCallback(): void {
    super.connectedCallback();
    void this.#shows();
  }

  override render(): TemplateResult {
    const lines = this.served?.lines ?? [];
    const drawn = shown(lines, over(this.choice, this.#at), this.routine);
    return html`
      <dccex-controls
        .choices=${choices(lines)}
        .choice=${this.choice}
        .picks=${this.#picks}
        .routine=${this.routine}
        .toggles=${this.#toggles}
        .bytes=${this.served === null ? null : this.served.bytes}
        .reloads=${this.#reloads}
      ></dccex-controls>
      ${this.#nothing()}
      ${lines.length === 0
        ? nothing
        : html`
            <dccex-counts
              .districts=${drawn.districts}
              .station=${drawn.station}
            ></dccex-counts>
            <dccex-incidents .entries=${drawn.entries}></dccex-incidents>
          `}
    `;
  }

  /** What stands where the rows would be: a journal with nothing in it, or one
   *  the face would not serve.
   *
   * And nothing at all until the first ask has come back, because a page that
   * has not been told anything yet has nothing to report (ADR-0009 d.2).
   */
  #nothing(): TemplateResult | typeof nothing {
    if (!this.answered || (this.served?.lines.length ?? 0) > 0) {
      return nothing;
    }
    return html`<p class="empty">
      ${this.served === null ? UNREADABLE : EMPTY}
    </p>`;
  }

  /** The period read, as the controls hand it up. What that period means is
   *  `incidents.js`'s, read at the next draw. */
  readonly #picks = (choice: string): void => {
    this.choice = choice;
  };

  /** The routine lines asked for, or given up. */
  readonly #toggles = (routine: boolean): void => {
    this.routine = routine;
  };

  /** The journal asked for again: the one way to see a line written since the
   *  view was opened. */
  readonly #reloads = (): void => {
    void this.#shows();
  };

  /** The journal as the face has it now.
   *
   * One ask at a time. A reader pressing the reload twice is one ask and the
   * answer to it, rather than two in flight whose order a browser decides
   * (#88).
   */
  async #shows(): Promise<void> {
    if (this.#asking) {
      return;
    }
    this.#asking = true;
    try {
      const served = await this.reads();
      this.#at = Date.now();
      this.served = served;
      this.answered = true;
    } finally {
      this.#asking = false;
    }
  }
}

customElements.define("dccex-journal", DccexJournal);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-journal": DccexJournal;
  }
}
