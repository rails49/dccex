/**
 * The divider between the script view's editor and its **log** (#365).
 *
 * It is the bar between the two, and what it holds is the log's share of the
 * room they are in: dragged, or moved with the arrow keys, it says the new
 * share in a `divided` event, and the view lays the two out by it. It says the
 * share it opens with as well, when it is put in the page.
 *
 * Wider than `ACROSS` the log is to the right of the editor and the divider
 * moves sideways; narrower, the log is below and it moves up and down. The
 * view's sheet lays the two out on the same query.
 *
 * Dragged to the log's edge the share is `0`, which hides the log, and the
 * divider stays at the edge to be dragged back. The browser remembers the
 * share in `localStorage`. A store that refuses is a share that is not
 * remembered, and the divider opens on `SHARE`.
 */

import { LitElement, nothing } from "lit";

import { ACROSS, dividerStyles } from "./dccex-divider.styles.js";

export { ACROSS };

/** The log's share where none is remembered. */
export const SHARE = 0.4;

/** Where the share is remembered. */
export const REMEMBERED = "dccex.log.share";

/** A share under this is the log dragged to its edge, and hidden. */
const EDGE = 0.05;

/** The most of the room the log takes. The editor keeps the rest. */
const MOST = 0.9;

/** How far an arrow key moves the divider. */
const STEP = 0.05;

/** `share` as the divider takes it: `0` near the edge, no more than `MOST`,
 *  and `SHARE` for anything that is not a number. */
export function held(share: number): number {
  if (!Number.isFinite(share)) {
    return SHARE;
  }
  if (share < EDGE) {
    return 0;
  }
  return Math.min(share, MOST);
}

/** The share the browser remembers, or `SHARE`. */
export function remembered(): number {
  try {
    const kept = localStorage.getItem(REMEMBERED);
    return kept === null ? SHARE : held(Number(kept));
  } catch {
    return SHARE;
  }
}

/** Remember `share`, where the browser lets the page. */
function remember(share: number): void {
  try {
    localStorage.setItem(REMEMBERED, String(share));
  } catch {
    // A store that refuses forgets the share. The divider still moves.
  }
}

export class DccexDivider extends LitElement {
  static override readonly styles = dividerStyles;

  static override readonly properties = {
    share: { state: true },
    across: { state: true },
  };

  /** The log's share of the room, `0` where it is hidden. */
  share = remembered();

  /** Whether the log is beside the editor rather than below it. */
  across = false;

  #media: MediaQueryList | null = null;

  #dragging = false;

  override connectedCallback(): void {
    super.connectedCallback();
    this.#media = matchMedia(ACROSS);
    this.across = this.#media.matches;
    this.#media.addEventListener("change", this.#turned);
    this.addEventListener("pointerdown", this.#pressed);
    this.addEventListener("pointermove", this.#dragged);
    this.addEventListener("pointerup", this.#released);
    this.addEventListener("pointercancel", this.#released);
    this.addEventListener("keydown", this.#keyed);
    this.tabIndex = 0;
    this.setAttribute("role", "separator");
    this.setAttribute("aria-label", "log");
    this.#says();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#media?.removeEventListener("change", this.#turned);
    this.#media = null;
    this.removeEventListener("pointerdown", this.#pressed);
    this.removeEventListener("pointermove", this.#dragged);
    this.removeEventListener("pointerup", this.#released);
    this.removeEventListener("pointercancel", this.#released);
    this.removeEventListener("keydown", this.#keyed);
  }

  override render(): typeof nothing {
    return nothing;
  }

  /** The separator's state for assistive technology: which way it lies, and
   *  where it is as the editor's share. */
  protected override updated(): void {
    this.setAttribute(
      "aria-orientation",
      this.across ? "vertical" : "horizontal",
    );
    this.setAttribute(
      "aria-valuenow",
      String(Math.round(100 - 100 * this.share)),
    );
  }

  /** Move the divider to `share`, and say so. */
  moves(share: number): void {
    this.share = held(share);
    this.#says();
  }

  #says(): void {
    this.dispatchEvent(new CustomEvent("divided", { detail: this.share }));
  }

  readonly #turned = (): void => {
    this.across = this.#media?.matches ?? false;
  };

  readonly #pressed = (event: PointerEvent): void => {
    this.#dragging = true;
    this.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  };

  /** The share is what lies between the pointer and the log's edge of the
   *  room the divider is in. */
  readonly #dragged = (event: PointerEvent): void => {
    const room = this.parentElement?.getBoundingClientRect();
    if (!this.#dragging || room === undefined) {
      return;
    }
    const share = this.across
      ? (room.right - event.clientX) / room.width
      : (room.bottom - event.clientY) / room.height;
    this.moves(share);
  };

  readonly #released = (): void => {
    if (this.#dragging) {
      this.#dragging = false;
      remember(this.share);
    }
  };

  /** The arrow keys move the divider toward the way they point. */
  readonly #keyed = (event: KeyboardEvent): void => {
    const grows = this.across ? "ArrowLeft" : "ArrowUp";
    const shrinks = this.across ? "ArrowRight" : "ArrowDown";
    if (event.key !== grows && event.key !== shrinks) {
      return;
    }
    event.preventDefault();
    this.moves(this.share + (event.key === grows ? STEP : -STEP));
    remember(this.share);
  };
}

customElements.define("dccex-divider", DccexDivider);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-divider": DccexDivider;
  }
}
