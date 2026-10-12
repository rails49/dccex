/**
 * The **journal** view's controls: the period, the toggle, the reload, the
 * file's size, the download and the clear.
 *
 * **It decides nothing.** Which period is read, whether the routine lines are
 * shown and when the journal is asked for again are the view's, kept there and
 * handed down; a press hands the answer up (`dccex-journal.ts`). One direction
 * each, the way the **rail** hands a **view** up — a control that kept its own
 * answer would draw one period while the table counted another.
 *
 * **The periods are one list.** The three spans and every **build** the
 * journal carries are the same kind of answer — which lines are read — so they
 * are one chooser rather than a chooser and a second control beside it
 * (`incidents.js`'s `choices()`).
 *
 * **The download is the browser's own fetch.** It is a link to the face's
 * address with `download` on it, so the file a person keeps is the bytes the
 * mirror served and not something this page rendered (ADR-0022 d.4,
 * `face.ts`).
 *
 * **And the clear says what it does before it does it** (ADR-0006 d.2). The
 * journal is the record of what nobody was watching, nothing keeps a copy and
 * the face guards nothing: so the warning opens under the control, the yes is
 * drawn as the dangerous press it is, and what the face answered is shown as it
 * came (control ADR-0050). The words are `incidents.js`'s and are run rather
 * than read (`tests/ui/test_incidents.py`).
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import { JOURNAL_PATH } from "../face.js";
import {
  CANCELS,
  CLEARS,
  CONFIRMS,
  DOWNLOADS,
  RELOADS,
  ROUTINE,
  WARNS,
  size,
} from "../incidents.js";
import { controlsStyles } from "./dccex-controls.styles.js";

/** What the chooser is labelled. The word is the one the glossary spends on
 *  the thing a reading is made over. */
const PERIOD = "period";

/** What the file the download link points at is called where a browser is left
 *  to name it. The journal is one JSON object per line (ADR-0022 d.1). */
const FILE = "journal.jsonl";

export class DccexControls extends LitElement {
  static override readonly styles = controlsStyles;

  static override readonly properties = {
    choices: { attribute: false },
    choice: { attribute: false },
    picks: { attribute: false },
    routine: { attribute: false },
    toggles: { attribute: false },
    bytes: { attribute: false },
    reloads: { attribute: false },
    empties: { attribute: false },
    says: { attribute: false },
    asked: { state: true },
  };

  /** The periods on offer: the spans, and one per build in the journal. */
  choices: readonly string[] = [];

  /** Which of them is being read, as the view hands it down. */
  choice = "";

  /** What picks one. A control nobody handed one to picks nothing: the period
   *  is the view's, and chrome that wrote it would be a second answer to which
   *  lines are counted. */
  picks: (choice: string) => void = () => {};

  /** Whether the lines no incident took are rows as well. */
  routine = false;

  /** What turns them on and off. */
  toggles: (routine: boolean) => void = () => {};

  /** How big the journal is, or `null` where the face has not served it — a
   *  size drawn for a file nobody read would be a reading nobody took
   *  (ADR-0009 d.2). */
  bytes: number | null = null;

  /** What asks the face for the journal again. */
  reloads: () => void = () => {};

  /** What asks the face to empty it, once the operator has said yes. */
  empties: () => void = () => {};

  /** What became of the last clear, as the view hands it down: the face's own
   *  sentence, or the page's where there was no answer to read. */
  says = "";

  /** Whether the warning the clear opens is open. Nothing has reached the face
   *  while it is: it is the gesture made and the yes not yet given. */
  asked = false;

  override render(): TemplateResult {
    return html`
      <div class="controls">
        <label class="period">
          ${PERIOD}
          <select
            class="choices"
            .value=${this.choice}
            @change=${this.#chosen}
          >
            ${this.choices.map(
              (choice: string) => html`
                <option value=${choice} ?selected=${choice === this.choice}>
                  ${choice}
                </option>
              `,
            )}
          </select>
        </label>
        <label class="shows">
          <input
            class="toggle"
            type="checkbox"
            .checked=${this.routine}
            @change=${this.#toggled}
          />
          ${ROUTINE}
        </label>
        <button class="reloads" type="button" @click=${this.#reloads}>
          ${RELOADS}
        </button>
        <span class="size">${this.bytes === null ? "" : size(this.bytes)}</span>
        <a class="downloads" href=${JOURNAL_PATH} download=${FILE}>
          ${DOWNLOADS}
        </a>
        <button
          class="clears"
          type="button"
          ?disabled=${this.asked}
          @click=${this.#clears}
        >
          ${CLEARS}
        </button>
      </div>
      ${this.#warning()}
      ${this.says === ""
        ? nothing
        : html`<p class="says" aria-live="polite">${this.says}</p>`}
    `;
  }

  /** What an operator is told before the journal is emptied, and the two
   *  presses that answer it.
   *
   * The second press is what makes the gesture a thing somebody meant: the
   * guard is the person, and a person can only be one if they are told what
   * the gesture does before they are asked (ADR-0006 d.2).
   */
  #warning(): TemplateResult | typeof nothing {
    if (!this.asked) {
      return nothing;
    }
    return html`
      <div class="warning">
        <p class="warns" role="alert">${WARNS}</p>
        <button class="confirms" type="button" @click=${this.#confirms}>
          ${CONFIRMS}
        </button>
        <button class="cancels" type="button" @click=${this.#cancels}>
          ${CANCELS}
        </button>
      </div>
    `;
  }

  /** A period chosen, handed up as the word it is. */
  readonly #chosen = (event: Event): void => {
    this.picks((event.target as HTMLSelectElement).value);
  };

  /** The routine lines asked for, or given up. */
  readonly #toggled = (event: Event): void => {
    this.toggles((event.target as HTMLInputElement).checked);
  };

  /** The journal asked for again. What is in front of a person is what the
   *  face last served, so this is the one way to see a line written since
   *  (ADR-0010 d.1: the page asks). */
  readonly #reloads = (): void => {
    this.reloads();
  };

  /** The clear pressed: the warning opens and nothing else happens. */
  readonly #clears = (): void => {
    this.asked = true;
  };

  /** The warning declined. Nothing was asked of the face, so there is nothing
   *  to report about a journal nobody emptied. */
  readonly #cancels = (): void => {
    this.asked = false;
  };

  /** The yes. The warning shuts and the view asks the face. */
  readonly #confirms = (): void => {
    this.asked = false;
    this.empties();
  };
}

customElements.define("dccex-controls", DccexControls);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-controls": DccexControls;
  }
}
