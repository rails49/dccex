/**
 * The **script**: a railroad's Python document, opened in an editor on a
 * **view** of its own and applied to `control`'s store through the **face**.
 *
 * The railroad is the one `control` has loaded, which the page reads off the
 * bus and hands down: its script opens in the editor, and Apply sends it
 * (ADR-0015 d.5 as amended, the organisation's ADR-0014, issue 185, issue
 * 238). There is no list and nothing to pick — a script nothing is running
 * cannot be edited here. A railroad the store has no script for opens on the
 * translator's sample, commented out, so that what is in front of somebody
 * writing their first one is the shape a script has — and applying it
 * unchanged is a railroad whose script does nothing rather than one running
 * values a page suggested (`script.ts`).
 *
 * **Edits stay in the page until Apply.** Nothing is sent as it is typed:
 * applying a script stands the railroad down, so there is no version of this
 * that saves while somebody thinks. What that costs is edits that can be lost,
 * which is what the two warnings are for — the page being closed on them, and
 * the railroad they were written for being unloaded under them, which is a
 * thing that happens to a person rather than one they do. Neither writes
 * anything: the text stays in the editor until somebody says to discard it.
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
 * with no script opens with, and whether what is in the editor is what was
 * applied — so those are run rather than read (`ui/test/script.test.ts`).
 * What is decided here is the drawing: where the name sits, where the warnings
 * open, and where the editor goes.
 *
 * **The editor is CodeMirror and it is not Lit's** (ADR-0019). What it is made
 * of is `editor.ts`'s; what is here is one of them, made over the place the
 * template leaves and kept across every draw, because the document, the
 * selection and the undo history are in it — and so is the mark a refused
 * Apply leaves on the line it named (ADR-0019 d.4).
 */

import { EditorView } from "@codemirror/view";
import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  APPLIES,
  CANCELS,
  CONFIRMS,
  DISCARDS,
  GONE,
  STOPS,
  UNANSWERED,
  UNAPPLIED,
  UNLOADED,
  type Applied,
  type Opened,
  refusal,
  unapplied,
} from "../script.js";
import { scriptStyles } from "./dccex-script.styles.js";
import { editing, mark } from "./editor.js";

/** What the view is called. The word is the glossary's (CONTEXT.md,
 *  **script**): a railroad's document in the store, which the translator loads
 *  and this page edits. */
const HEADING = "script";

export class DccexScript extends LitElement {
  static override readonly styles = scriptStyles;

  static override readonly properties = {
    loaded: { attribute: false },
    opens: { attribute: false },
    applies: { attribute: false },
    railroad: { state: true },
    opened: { state: true },
    edited: { state: true },
    warning: { state: true },
    applying: { state: true },
    became: { state: true },
  };

  /** Which railroad `control` has loaded, as the page hands it down, or `null`
   *  where none is and where the page has not reached the broker (`bus.ts`,
   *  `readings.js`'s `named`).
   *
   *  It is what this view edits, and the whole of what says which script is
   *  open: a name that changes opens another script, and `null` leaves nothing
   *  to edit (ADR-0015 d.5 as amended, issue 238). */
  loaded: string | null = null;

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

  /** The editor, or `null` where there is nothing to edit.
   *
   *  It is not Lit's. CodeMirror holds its own DOM, its own selection and its
   *  own undo history, and a template that drew it would make a second one on
   *  every draw — which is the history this view was losing (ADR-0019). So the
   *  template draws a place for it and `updated` puts one there. */
  #editor: EditorView | null = null;

  /** The railroad the editor is open on, or `null` where no editor is. It is
   *  what says when to open a new document: another railroad loaded is a new
   *  script and a new history, and an Apply is neither. */
  #open: string | null = null;

  /** The editor, for a check to read the document off.
   *
   *  happy-dom lays CodeMirror out nowhere, so what is asserted on a mounted
   *  pane is the editor's state and never a rectangle (ADR-0019,
   *  `ui/test/mounted.ts`). */
  get editor(): EditorView | null {
    return this.#editor;
  }

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
    this.#editor?.destroy();
    this.#editor = null;
    this.#open = null;
  }

  override render(): TemplateResult {
    return html`
      <h2>${HEADING}</h2>
      ${this.#names()} ${this.#unloaded()} ${this.#says()} ${this.#editing()}
      ${this.#controls()}
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

  /** The railroad whose script is in the editor, named above it, or that none
   *  is loaded.
   *
   * It is the railroad `control` has loaded, which is the one this view edits
   * and the only one it opens (ADR-0015 d.5 as amended, the organisation's
   * ADR-0014). The two differ in one state and one only — the railroad
   * unloaded with unapplied edits in the editor — and there the name is the
   * editor's railroad, because what a person is looking at is that railroad's
   * text and the sentence under it says it is no longer loaded (issue 238).
   */
  #names(): TemplateResult {
    return html`<p class="loaded">${this.railroad ?? UNLOADED}</p>`;
  }

  /** What is said where the railroad in the editor has been unloaded with
   *  edits in it that were not applied, and the one control on it.
   *
   * One control, because there is nothing else to offer: the railroad these
   * edits were written for is not the one `control` is running, so there is no
   * Apply to make and no other railroad to keep editing instead. The text
   * stays where it is until somebody says to discard it, and then this view is
   * the loaded railroad's again — or says none is (`script.ts`).
   */
  #unloaded(): TemplateResult | typeof nothing {
    if (!this.#gone()) {
      return nothing;
    }
    return html`
      <div class="unloaded">
        <p class="warns" role="alert">${GONE}</p>
        <button class="discards" type="button" @click=${this.#discards}>
          ${DISCARDS}
        </button>
      </div>
    `;
  }

  /** Whether the editor is open on a railroad `control` no longer has loaded.
   *
   * Worked out rather than kept, because it is the two names disagreeing and
   * nothing else: everything that opens a script sets both, so a flag of its
   * own would be a second answer to a question the names already answer.
   */
  #gone(): boolean {
    return this.railroad !== null && this.railroad !== this.loaded;
  }

  /** What is said about the script in the editor: that a railroad has none and
   *  the sample is what is there, that it could not be read, or nothing. */
  #says(): TemplateResult | typeof nothing {
    const says = this.opened === null ? "" : this.opened.says;
    return says === "" ? nothing : html`<p class="says">${says}</p>`;
  }

  /** Where the editor goes: an empty element, and `updated` below puts one in
   *  it.
   *
   * The editor is not drawn here because Lit owns what it draws, and what
   * CodeMirror holds is a document, a selection and an undo history that must
   * outlive a draw (ADR-0019 d.1, `editor.ts`).
   *
   * There is no place for one where no railroad is loaded and none for a
   * script that could not be read: an editor offering the sample for a
   * railroad whose script this page never saw would be inviting somebody to
   * overwrite a document it does not know the contents of (ADR-0009 d.2).
   */
  #editing(): TemplateResult | typeof nothing {
    if (this.opened === null || this.opened.text === null) {
      return nothing;
    }
    return html`<div class="editing"></div>`;
  }

  /** The editor, put where the draw left a place for it, or taken away where
   *  the draw left none.
   *
   * Three cases, and they are the three states above. Nothing to edit lets the
   * editor go. A railroad that is not the one it was open on opens a new
   * document in it, which is a new history: an undo that reached back into
   * another railroad's script would be an edit nobody made. Anything else — an
   * Apply, a warning opening, the railroad being unloaded under the edits —
   * leaves it alone, because what is in it is what somebody typed.
   *
   * It is opened on `edited` and not on `opened.text`. The two are the same
   * text when a railroad opens, and where they differ it is because there are
   * edits nothing else in the system is holding a copy of (ADR-0015 d.5).
   */
  protected override updated(): void {
    const into = this.renderRoot.querySelector(".editing");
    if (into === null) {
      this.#editor?.destroy();
      this.#editor = null;
      this.#open = null;
      return;
    }
    if (this.#editor === null) {
      this.#editor = new EditorView({
        parent: into,
        state: editing(this.edited, HEADING, this.#typed),
      });
    } else if (this.#open !== this.railroad) {
      this.#editor.setState(editing(this.edited, HEADING, this.#typed));
    }
    this.#open = this.railroad;
  }

  /** Apply, and the warning it opens under.
   *
   * The control is dead while an Apply is in flight, while there is nothing to
   * apply, and on a railroad that has been unloaded under the edits — there is
   * no railroad to stand down for that text — and it says what the gesture
   * does before it is pressed a second time: the operator is the guard on a
   * railroad standing down, and a person can only be one if they are told
   * (ADR-0006 d.2, ADR-0015 d.3, issue 238).
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
          ?disabled=${this.applying || this.warning || this.#gone()}
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

  /** What the railroad `control` has loaded does to the editor, read before
   *  every draw.
   *
   * Three answers. The railroad the editor is already open on is no answer at
   * all: a rebuild that restamps the row names the railroad that is open, and
   * opening it again would discard what somebody has typed, so the one thing
   * that opens a script is a name this editor is not on (issue 238). A name
   * this editor is not on with unapplied edits in it opens nothing either —
   * the edits stay, with the warning above them, until somebody discards them.
   * Anything else is opened.
   *
   * An Apply in flight is not one of the three: it opens, and the answer that
   * lands is dropped by the guard in `#applied` below. What is on its way to
   * the store is already on its way.
   *
   * It is read here rather than in a setter so that one draw carries both the
   * name and what it opened: the railroad is set before the template is read,
   * and the face is asked after it.
   */
  protected override willUpdate(): void {
    if (this.loaded === this.railroad) {
      return;
    }
    if (
      this.opened !== null &&
      unapplied(this.edited, this.opened.text) &&
      !this.applying
    ) {
      this.warning = false;
      return;
    }
    void this.#shows(this.loaded);
  }

  /** The edits on an unloaded railroad discarded, which opens the railroad
   *  `control` has loaded now — or leaves nothing to edit, where it has loaded
   *  none. Nothing was written to either railroad. */
  readonly #discards = (): void => {
    void this.#shows(this.loaded);
  };

  /** The Apply warning declined. The edits stay in the editor and the railroad
   *  is running what it was running: there is nothing to report about a script
   *  that was not applied. */
  readonly #cancels = (): void => {
    this.warning = false;
  };

  /** One railroad's script opened: what the face says it is, and the editor set
   *  to it. A `null` railroad is the view with nothing to edit, and nobody is
   *  asked for it.
   *
   *  What became of the last Apply goes with it, because it was about another
   *  gesture, and so does the warning.
   */
  async #shows(railroad: string | null): Promise<void> {
    this.railroad = railroad;
    this.warning = false;
    this.became = null;
    this.opened = null;
    this.edited = "";
    if (railroad === null) {
      return;
    }
    const shown = await this.opens(railroad);
    if (this.railroad !== railroad) {
      // Another railroad was loaded while this one was being asked for. The
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
   *
   * **A refusal that names a line marks it** (ADR-0019 d.4). The sentence is
   * shown whole as it came; the line out of it is `script.ts`'s to read and
   * the mark is the editor's to draw, so that nobody is left reading a page of
   * Python for the one line the face named. A refusal that names none marks
   * nothing, and so does an Apply that landed.
   */
  async #applied(): Promise<void> {
    const railroad = this.railroad;
    if (this.applying || railroad === null || this.#gone()) {
      return;
    }
    this.applying = true;
    this.warning = false;
    const applied = this.edited;
    try {
      const became = await this.applies(railroad, applied);
      if (this.railroad !== railroad) {
        // Another railroad was loaded while this one was applied: the answer
        // is about a railroad nobody is looking at, as in `#shows`.
        return;
      }
      this.became = became;
      if (this.#editor !== null) {
        mark(this.#editor, became.applied ? null : refusal(became.says));
      }
      if (became.applied) {
        this.opened = { text: applied, stored: true, says: "" };
      }
    } finally {
      this.applying = false;
    }
  }

  /** What was typed, kept where the page keeps it. The editor says this after
   *  every change it makes — the indent keys' and an undo's as well as a
   *  keystroke's (`editor.ts`). */
  readonly #typed = (text: string): void => {
    this.edited = text;
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
