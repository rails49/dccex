/**
 * The **script**: a railroad's Python document, opened in an editor on a
 * **view** of its own and applied to `control`'s store through the **face**.
 *
 * The person picks a railroad off the list the face answers, the text opens in
 * the editor, and Apply sends it (ADR-0015 d.5, issue 185). A railroad the
 * store has no script for opens on the translator's sample, commented out, so
 * that what is in front of somebody writing their first one is the shape a
 * script has — and applying it unchanged is a railroad whose script does
 * nothing rather than one running values a page suggested (`script.ts`).
 *
 * **Edits stay in the page until Apply.** Nothing is sent as it is typed:
 * applying a script stands the railroad down, so there is no version of this
 * that saves while somebody thinks. What that costs is edits that can be lost,
 * which is what the two warnings are for — leaving the railroad or the page
 * with unapplied edits asks first, and both questions are drawn here.
 *
 * **Apply says what it does before it does it** (ADR-0006 d.2, ADR-0015 d.3).
 * The translator exits on a text that differs from the one it is running, which
 * cuts track power and stands the railroad down, and nothing behind the page
 * guards that: the store stores what it is given and the face compiles and no
 * more. So the operator is told, and asked a second time, exactly as they are
 * for a flash (`dccex-releases.ts`).
 *
 * **The compiling is the face's and so is the sentence.** A text that is not
 * Python comes back refused with the line and the message and is shown as it
 * came: a page that wrote its own words over a refusal it was given would be
 * guessing at an answer it has (control ADR-0050). Nothing is compiled here —
 * there is no Python in a browser, and a second opinion about what compiles is
 * exactly the disagreement that would put a broken script in the store.
 *
 * **And nothing here fetches.** The page asks the face and hands the answers
 * down, as it does with the conversation and the releases: a pane holding its
 * own counterparty would be a second answer to what the page talks to (the
 * organisation's ADR-0002, `dccex-app.ts`).
 *
 * **What it works out without drawing is `script.ts`'s** — the text a railroad
 * with no script opens with, whether what is in the editor is what was applied,
 * and what a Tab does to it — so those are run rather than read
 * (`ui/test/script.test.ts`). What is decided here is the drawing: where the
 * list sits, where the warnings open, and that the editor is monospace and
 * takes a Tab.
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  APPLIES,
  CANCELS,
  CONFIRMS,
  DISCARDS,
  KEEPS,
  NO_RAILROADS,
  PICK,
  STOPS,
  UNANSWERED,
  UNAPPLIED,
  UNLISTED,
  type Applied,
  type Opened,
  tabbed,
  unapplied,
} from "../script.js";
import { scriptStyles } from "./dccex-script.styles.js";

/** What the view is called. The word is the glossary's (CONTEXT.md,
 *  **script**): a railroad's document in the store, which the translator loads
 *  and this page edits. */
const HEADING = "script";

export class DccexScript extends LitElement {
  static override readonly styles = scriptStyles;

  static override readonly properties = {
    railroads: { attribute: false },
    opens: { attribute: false },
    applies: { attribute: false },
    railroad: { state: true },
    opened: { state: true },
    edited: { state: true },
    leaving: { state: true },
    warning: { state: true },
    applying: { state: true },
    became: { state: true },
  };

  /** The railroads the face answered, or `null` where it could not be asked —
   *  which is also where it has not been asked yet, and the list says the
   *  railroads could not be read until it has (`face.ts`). */
  railroads: string[] | null = null;

  /** What asks the face for one railroad's script, as the page hands it down.
   *
   *  A pane nobody handed one to opens nothing: there is no text to edit, which
   *  is what a page with no way to ask has to show (ADR-0009 d.2). */
  opens: (railroad: string) => Promise<Opened> = () =>
    Promise.resolve({ text: null, stored: false, says: UNANSWERED });

  /** What asks the face to apply one, as the page hands it down.
   *
   *  A pane nobody handed one to says the mirror could not be asked, which is
   *  the true sentence for a page with no way to ask it: nothing said is not
   *  nothing stored. */
  applies: (railroad: string, text: string) => Promise<Applied> = () =>
    Promise.resolve({ applied: false, says: UNANSWERED });

  /** The railroad whose script is open, or `null` where none is. */
  railroad: string | null = null;

  /** What that railroad's script opened as, or `null` where no railroad is
   *  open. Its `text` is the one answer to what was last applied, so it is what
   *  the editor is compared against and it is what an Apply that landed
   *  replaces. */
  opened: Opened | null = null;

  /** What is in the editor. It is the page's copy and the editor's document
   *  at once: what a person typed is here and nowhere else until Apply
   *  (ADR-0015 d.5). */
  edited = "";

  /** The railroad a person is picking with unapplied edits in the editor, or
   *  `null` where none is. Nothing has been opened while this stands: it is the
   *  choice made and the answer not yet given. */
  leaving: string | null = null;

  /** Whether the warning Apply opens is open. Nothing has reached the face
   *  while it is: the railroad is still running whatever it was running. */
  warning = false;

  /** Whether an Apply is in flight. One at a time, so two presses cannot
   *  store two texts. */
  applying = false;

  /** What the face said the last Apply came to, or `null` where none has been
   *  asked for. The sentence is the face's or `script.ts`'s and never this
   *  component's (control ADR-0050). */
  became: Applied | null = null;

  override connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener("beforeunload", this.#unloading);
  }

  /** Stop asking about unapplied edits when the pane goes.
   *
   * The page keeps this pane in the document and hides it, so the listener
   * lives as long as the page does — which is the point of it. A pane that is
   * taken away lets it go, because a question about an editor nobody can see is
   * a page refusing to close for edits it is no longer holding.
   */
  override disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener("beforeunload", this.#unloading);
  }

  override render(): TemplateResult {
    return html`
      <h2>${HEADING}</h2>
      ${this.#railroads()} ${this.#says()} ${this.#edited()} ${this.#controls()}
      ${this.became === null
        ? nothing
        : html`<p
            class=${this.became.applied ? "became applied" : "became failed"}
            aria-live="polite"
          >
            ${this.became.says}
          </p>`}
    `;
  }

  /** The railroads the store holds, one button each, the open one marked.
   *
   * None of them is marked as the one that is running: which railroad that is
   * is the bus's to say and is a row in `control`'s UI (ADR-0015 d.5). What is
   * marked here is which one this editor is showing.
   *
   * A list that could not be read and a store with no railroads in it are
   * different sentences, and neither is an empty list drawn as if it were an
   * answer (ADR-0009 d.2, `script.ts`).
   */
  #railroads(): TemplateResult {
    if (this.railroads === null) {
      return html`<p class="unlisted">${UNLISTED}</p>`;
    }
    if (this.railroads.length === 0) {
      return html`<p class="unlisted">${NO_RAILROADS}</p>`;
    }
    return html`
      <ul class="railroads">
        ${this.railroads.map(
          (railroad: string) => html`
            <li>
              <button
                class="railroad"
                type="button"
                aria-current=${railroad === this.railroad ? "true" : nothing}
                @click=${() => {
                  this.#picks(railroad);
                }}
              >
                ${railroad}
              </button>
              ${this.leaving === railroad ? this.#warns(railroad) : nothing}
            </li>
          `,
        )}
      </ul>
    `;
  }

  /** What is said about the script in the editor: that a railroad has none and
   *  the sample is what is there, that it could not be read, or nothing. */
  #says(): TemplateResult | typeof nothing {
    if (this.railroad === null) {
      return html`<p class="says">${PICK}</p>`;
    }
    const says = this.opened === null ? "" : this.opened.says;
    return says === "" ? nothing : html`<p class="says">${says}</p>`;
  }

  /** The editor: the text, monospace, and a Tab that puts spaces in it.
   *
   * There is no editor before a railroad is picked and none for a script that
   * could not be read: an editor offering the sample for a railroad whose
   * script this page never saw would be inviting somebody to overwrite a
   * document it does not know the contents of (ADR-0009 d.2).
   */
  #edited(): TemplateResult | typeof nothing {
    if (this.opened === null || this.opened.text === null) {
      return nothing;
    }
    return html`
      <textarea
        class="script"
        spellcheck="false"
        autocapitalize="off"
        aria-label=${HEADING}
        .value=${this.edited}
        @input=${this.#typed}
        @keydown=${this.#key}
      ></textarea>
    `;
  }

  /** Apply, and the warning it opens under.
   *
   * The control is dead while an Apply is in flight and while there is nothing
   * to apply, and it says what the gesture does before it is pressed a second
   * time: the operator is the guard on a railroad standing down, and a person
   * can only be one if they are told (ADR-0006 d.2, ADR-0015 d.3).
   */
  #controls(): TemplateResult | typeof nothing {
    if (this.opened === null || this.opened.text === null) {
      return nothing;
    }
    return html`
      <div class="controls">
        <button
          class="applies"
          type="button"
          ?disabled=${this.applying || this.warning}
          @click=${() => {
            this.warning = true;
          }}
        >
          ${APPLIES}
        </button>
        ${unapplied(this.edited, this.opened.text)
          ? html`<span class="unapplied">${UNAPPLIED}</span>`
          : nothing}
      </div>
      ${this.warning
        ? html`
            <div class="warning">
              <p class="warns" role="alert">${STOPS}</p>
              <button
                class="confirms"
                type="button"
                ?disabled=${this.applying}
                @click=${() => {
                  void this.#applied();
                }}
              >
                ${CONFIRMS}
              </button>
              <button class="cancels" type="button" @click=${this.#cancels}>
                ${CANCELS}
              </button>
            </div>
          `
        : nothing}
    `;
  }

  /** What an operator is asked before edits that were not applied are
   *  discarded: leaving this railroad for another one.
   *
   *  The same shape the page is left with, and the same words: what is being
   *  left is an editor that nothing else in the system is holding a copy of
   *  (`script.ts`).
   */
  #warns(railroad: string): TemplateResult {
    return html`
      <div class="leaving">
        <p class="warns" role="alert">${UNAPPLIED}</p>
        <button
          class="discards"
          type="button"
          @click=${() => {
            void this.#shows(railroad);
          }}
        >
          ${DISCARDS}
        </button>
        <button class="keeps" type="button" @click=${this.#keeps}>
          ${KEEPS}
        </button>
      </div>
    `;
  }

  /** A railroad picked: the one that is open is nothing, a different one with
   *  unapplied edits in the editor opens the question above it, and any other
   *  one is opened. */
  #picks(railroad: string): void {
    if (railroad === this.railroad) {
      return;
    }
    if (
      this.opened !== null &&
      unapplied(this.edited, this.opened.text) &&
      !this.applying
    ) {
      this.leaving = railroad;
      return;
    }
    void this.#shows(railroad);
  }

  /** The question declined, which is staying where the edits are. */
  readonly #keeps = (): void => {
    this.leaving = null;
  };

  /** The Apply warning declined. The edits stay in the editor and the railroad
   *  is running what it was running: there is nothing to report about a script
   *  that was not applied. */
  readonly #cancels = (): void => {
    this.warning = false;
  };

  /** One railroad's script opened: what the face says it is, and the editor set
   *  to it.
   *
   *  What became of the last Apply goes with it, because it was about another
   *  gesture, and so does either question.
   */
  async #shows(railroad: string): Promise<void> {
    this.railroad = railroad;
    this.leaving = null;
    this.warning = false;
    this.became = null;
    this.opened = null;
    this.edited = "";
    const shown = await this.opens(railroad);
    if (this.railroad !== railroad) {
      // Another railroad was picked while this one was being asked for. The
      // answer is about a railroad nobody is looking at, and writing it into
      // the editor would put one railroad's script under another's name.
      return;
    }
    this.opened = shown;
    this.edited = shown.text ?? "";
  }

  /** The text applied, once the operator has said yes.
   *
   * **A second one cannot start while this is running.** The controls are dead
   * while it is, and this refuses one anyway: the flag is set before the
   * `await`, so two presses in one turn cannot both pass the check — the same
   * reason the mirror's own flag is read where nothing is awaited after it
   * (`firmware.py`).
   *
   * What comes back is the face's answer, and where it landed the text becomes
   * what was applied: the editor is then not unapplied, which is what the two
   * warnings are keyed on.
   */
  async #applied(): Promise<void> {
    const railroad = this.railroad;
    if (this.applying || railroad === null) {
      return;
    }
    this.applying = true;
    this.warning = false;
    const applied = this.edited;
    try {
      const became = await this.applies(railroad, applied);
      if (this.railroad !== railroad) {
        // Another railroad was picked while this one was applied: the answer
        // is about a railroad nobody is looking at, as in `#shows`.
        return;
      }
      this.became = became;
      if (became.applied) {
        this.opened = { text: applied, stored: true, says: "" };
      }
    } finally {
      this.applying = false;
    }
  }

  /** What was typed, kept where the page keeps it. */
  readonly #typed = (event: Event): void => {
    this.edited = (event.target as HTMLTextAreaElement).value;
  };

  /** A Tab in the editor: spaces, and the caret after them.
   *
   * Tab in a text area is a browser moving to the next control, which in a
   * page of Python is the key an editor needs most. What it puts in and where
   * the caret goes are `script.ts`'s; what is here is taking the key and
   * putting the caret back, which needs a text area.
   */
  readonly #key = (event: KeyboardEvent): void => {
    if (event.key !== "Tab") {
      return;
    }
    event.preventDefault();
    const area = event.target as HTMLTextAreaElement;
    const put = tabbed(area.value, area.selectionStart, area.selectionEnd);
    area.value = put.text;
    area.selectionStart = put.caret;
    area.selectionEnd = put.caret;
    this.edited = put.text;
  };

  /** The page being closed with unapplied edits in the editor.
   *
   * Refusing is the whole of what a page may do here: what a browser then says
   * is the browser's own sentence and no page's, so the words above the editor
   * are where this page says what is at stake (`script.ts`'s `UNAPPLIED`).
   */
  readonly #unloading = (event: BeforeUnloadEvent): void => {
    if (this.opened !== null && unapplied(this.edited, this.opened.text)) {
      event.preventDefault();
    }
  };
}

customElements.define("dccex-script", DccexScript);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-script": DccexScript;
  }
}
