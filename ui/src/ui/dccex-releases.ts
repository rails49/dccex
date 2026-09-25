/**
 * The releases: every **release** the **mirror** is configured to read, in a
 * row that opens under the tiles, and the one place on the page one is written
 * onto the **station**.
 *
 * Newest first, each with the day it was published, the one that is on the
 * station now marked as such, and a release there is nothing to write from —
 * no firmware, or none with a digest to check it against — saying so (#8,
 * #81, docs/ui/README.md; the issue that last changed these words is named
 * there and in `releases.js` rather than here, because an issue number in the
 * hundreds is three hex digits and `tests/ui/test_look.py`'s scan reads one
 * in a component as a colour). The ordering, the dates and the mark are the
 * listing module's — a pure function of what the **face** answered and what
 * the station said (`releases.js`) — and this component is handed them and
 * draws them, as the tiles are handed their readings.
 *
 * **It is collapsed.** What the page is when nobody has asked about firmware
 * is the station's particulars and its conversation; the releases are a thing
 * to go and look at, and a list that pushed the monitor down the screen would
 * cost every reader for the sake of the one asking.
 *
 * **And choosing one flashes it** (#9). A release that carries a firmware
 * with a digest to check it against is pressed, the operator is told what flashing does — the station resets, the
 * rails go dead, every throttle loses it, it takes a minute or two — and asked
 * to say so a second time; what follows is `flash.js`'s sequence, and this
 * component shows which step it is on. Nothing behind the page guards any of
 * it: the mirror checks the tag, the release, the digest, the device and
 * whether it is already writing, and it checks nothing about a railroad
 * (ADR-0006). The operator is the guard, and the warning is what lets them be
 * one.
 *
 * **The steps, and every sentence they are said in, are the sequence's**, so
 * what an operator reads is asserted by running it rather than by reading this
 * component (`tests/ui/test_flash.py`). What is decided here is the drawing:
 * where the control sits, where the warning opens, and that the step is shown
 * under the row rather than inside it — the row can be shut while the station
 * is being written, and a minute of nothing at all is what reads as a hang.
 *
 * **A release is chosen once at a time.** While a sequence is running there is
 * nothing to press: a second flash is a second station reset, and what the
 * mirror does with one asked for anyway is refuse it rather than queue it
 * (`firmware.py`). What says one is running is the step being shown, so the
 * controls and the sentence under them cannot disagree.
 *
 * **And nothing here fetches.** The page asks the face and hands the answer
 * down, as it does with the conversation, and what sends a message up the
 * **stream** and what asks the face to write are handed down the same way: a
 * pane of the page holding its own counterparty would be a second answer to
 * what the page knows (the organisation's ADR-0002, `dccex-app.ts`).
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import {
  CANCELS,
  CHOOSES,
  CONFIRMS,
  UNANSWERED,
  WARNS,
  type Wrote,
  sequence,
} from "../flash.js";
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
    sends: { attribute: false },
    writes: { attribute: false },
    asked: { state: true },
    step: { state: true },
    wrote: { state: true },
  };

  /** What the face answered, or `null` where it could not be asked. A row
   *  nobody has handed a list to says the releases could not be read, which is
   *  what a page that has not been told anything has to show. */
  carried: Carried[] | null = null;

  /** What the station says it is running, off the `G-` field of its banner. It
   *  goes with the **link**: a station that is not answering has no build and
   *  nothing is marked (ADR-0008 d.3). */
  build: string | null = null;

  /** What puts one whole message up the stream, as the page hands it down: the
   *  message that went, or `null` where nothing did.
   *
   *  A row nobody handed one to sends nothing, rather than reaching for a
   *  stream of its own — and a sequence whose stop did not go writes nothing
   *  after it, which is the sequence's own rule (`flash.js`). */
  sends: (typed: string) => string | null = () => null;

  /** What asks the face to write a named release, as the page hands it down
   *  (`face.ts`).
   *
   *  A row nobody handed one to says the mirror could not be asked, which is
   *  the true sentence for a page with no way to ask it: nothing said is not
   *  nothing done, and what is on the station is read off the station
   *  (ADR-0006 d.3). */
  writes: (tag: string) => Promise<Wrote> = () =>
    Promise.resolve({ flashed: false, says: UNANSWERED });

  /** The release the warning is open under, or `null` where none is.
   *
   *  Nothing has reached the station while this stands: it is the choice made
   *  and the yes not yet given, and a sequence the operator declines is a
   *  flash that was not asked for rather than one that was refused (ADR-0006
   *  d.2). */
  asked: string | null = null;

  /** Which step of the sequence is running, or `null` where none is. It is
   *  what the row says while the station is away, and it is what says a flash
   *  is in flight. */
  step: string | null = null;

  /** What became of the last flash, or `null` where none has been asked for.
   *  The sentence is the sequence's or the face's and never this component's
   *  (`flash.js`, ADR-0050). */
  wrote: Wrote | null = null;

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
                  ? html`<button
                      class="chooses"
                      ?disabled=${this.step !== null}
                      @click=${() => {
                        this.#chosen(release.tag);
                      }}
                    >
                      ${CHOOSES}
                    </button>`
                  : html`<span class="bare">${NO_FIRMWARE}</span>`}
                ${this.asked === release.tag
                  ? this.#warning(release.tag)
                  : nothing}
              </li>
            `,
          )}
        </ol>
      </details>
      ${this.step === null
        ? nothing
        : html`<p class="step" aria-live="polite">${this.step}</p>`}
      ${this.wrote === null ? nothing : this.#became(this.wrote)}
    `;
  }

  /** What became of the last flash: written, or refused and why.
   *
   * The sentence is the sequence's or the face's own — a page that wrote its
   * own over a refusal it was given would be guessing at an answer it has
   * (ADR-0050) — and what is here is which of the two it is drawn as. */
  #became(wrote: Wrote): TemplateResult {
    return html`<p class=${wrote.flashed ? "became wrote" : "became refused"}>
      ${wrote.says}
    </p>`;
  }

  /** What an operator is told, and the press that answers it.
   *
   * The warning is the sequence's words and the second press is what makes the
   * gesture a thing somebody meant: the guard is the person, and a person can
   * only be one if they are told what the gesture does before they are asked
   * (ADR-0006 d.2).
   */
  #warning(tag: string): TemplateResult {
    return html`
      <div class="warning">
        <p class="warns" role="alert">${WARNS}</p>
        <button
          class="confirms"
          @click=${() => {
            void this.#flashes(tag);
          }}
        >
          ${CONFIRMS}
        </button>
        <button class="cancels" @click=${this.#cancels}>${CANCELS}</button>
      </div>
    `;
  }

  /** A release chosen: the warning opens under it and nothing else happens.
   *  What became of the last flash goes, because it was about another
   *  gesture. */
  #chosen(tag: string): void {
    this.asked = tag;
    this.wrote = null;
  }

  /** The warning declined. A flash that was not asked for leaves no sentence
   *  behind it: there is nothing to report about a station nobody touched. */
  readonly #cancels = (): void => {
    this.asked = null;
  };

  /** The sequence, once the operator has said yes.
   *
   * **A second one cannot start while this is running.** The controls are dead
   * while a step is showing, and this refuses one anyway: the first step is
   * shown before the sequence's first `await`, so two presses in one turn
   * cannot both pass the check — the same reason the mirror's own flag is read
   * where nothing is awaited after it (`firmware.py`).
   *
   * What goes down the cable, in what order, and what is said at each step are
   * the sequence's; what this hands it is the page's stream, the page's face
   * and somewhere to put a step.
   */
  async #flashes(tag: string): Promise<void> {
    if (this.step !== null) {
      return;
    }
    this.asked = null;
    this.wrote = null;
    const wrote = await sequence(tag, {
      sends: (typed: string) => this.sends(typed),
      writes: (chosen: string) => this.writes(chosen),
      shows: (step: string) => {
        this.step = step;
      },
    });
    this.step = null;
    this.wrote = wrote;
  }
}

customElements.define("dccex-releases", DccexReleases);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-releases": DccexReleases;
  }
}
