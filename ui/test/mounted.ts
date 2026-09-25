/**
 * Mounting one component of the page and reading what it drew.
 *
 * The checks beside this hand a component the facts a page would hand it and
 * assert what an operator reads back, in a DOM rather than against the source
 * that would produce it (#1 seam 2, #126). What every one of them needs is the
 * same few lines — make the element, put it in a document, wait for it to
 * draw, read something out of its shadow root — so they are here once rather
 * than once per file, for the reason `tests/ui/node.py` is one file: a shape
 * copied five times guarantees the sixth (#98).
 *
 * It is also the suite's setup file (`vitest.config.ts`), which is what empties
 * the document between checks. A component left mounted goes on answering
 * events, and the next check would be reading a page with two bands on it.
 *
 * **There is no layout here.** happy-dom draws no boxes, so nothing in these
 * checks may assert a width, a wrap or a height; a rule that is about the
 * shape of the page is still held against the stylesheet it is written in
 * (`tests/ui/test_look.py`, `tests/ui/test_band.py`).
 */

import { type LitElement } from "lit";
import { afterEach } from "vitest";

/** `element`, in a document and drawn once.
 *
 *  Handed back so that a check reads `const band = await mounted(...)` and
 *  goes on to ask what it drew. */
export async function mounted<T extends LitElement>(element: T): Promise<T> {
  document.body.append(element);
  await element.updateComplete;
  return element;
}

/** What the one part of `element` matching `selector` reads, or `null` where
 *  it drew none of them.
 *
 *  `null` and `""` are different answers and both are asserted: a gloss the
 *  decoder had nothing to say about is not drawn at all, and a tile the link
 *  took away is drawn with nothing in it (ADR-0009 d.2, ADR-0008 d.3). */
export function reads(element: LitElement, selector: string): string | null {
  const drew = element.renderRoot.querySelector(selector);
  return drew === null ? null : (drew.textContent ?? "").replace(/\s+/g, " ").trim();
}

/** What every part of `element` matching `selector` reads, in the order they
 *  were drawn. */
export function all(element: LitElement, selector: string): string[] {
  return [...element.renderRoot.querySelectorAll(selector)].map((drew) =>
    (drew.textContent ?? "").replace(/\s+/g, " ").trim(),
  );
}

/** The one part of `element` matching `selector`, asserted to be there.
 *
 *  What a check wants a node for is a class, an attribute or a press, and a
 *  `null` reaching one of those reads as the wrong answer rather than as a
 *  component that drew nothing. */
export function part(element: LitElement, selector: string): Element {
  const drew = element.renderRoot.querySelector(selector);
  if (drew === null) {
    throw new Error(`nothing matching ${selector} was drawn`);
  }
  return drew;
}

/** Press what `element` drew at `selector`. */
export function press(element: LitElement, selector: string): void {
  (part(element, selector) as HTMLElement).click();
}

/** Draw `element` now rather than at the end of the turn.
 *
 *  Lit draws once per turn, and `flash.js`'s sequence says its first two steps
 *  and sends the two messages between them without awaiting anything
 *  (`ui/src/flash.js`) — so a check that only awaited would see the last step
 *  and never the two before it. This is what lets the steps be read off the
 *  page in the order they are shown rather than off the sequence that shows
 *  them.
 *
 *  `performUpdate` is Lit's own synchronous draw. It is reached through a cast
 *  because Lit declares it for subclasses rather than for callers, and the one
 *  place that cast is written is here. */
export function drawnNow(element: LitElement): void {
  (element as unknown as { performUpdate: () => void }).performUpdate();
}

afterEach(() => {
  document.body.replaceChildren();
});
