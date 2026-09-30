/**
 * The icon, mounted: the path it was handed, drawn and read by nobody.
 *
 * Which path a control is drawn with is that control's check
 * (`ui/test/monitor.test.ts`); what is asserted here is that a path reaches the
 * shape and that the shape is out of the accessibility tree, so the words a
 * reader is given are the control's own.
 *
 * How big it is and what colour it takes are the stylesheet's — happy-dom does
 * no layout and has no cascade (`ui/test/mounted.ts`).
 */

import { mdiPause } from "@mdi/js";
import { expect, test } from "vitest";

import { DccexIcon } from "../src/ui/dccex-icon.js";
import { mounted, part } from "./mounted.js";

/** The icon, handed `path`. */
async function icon(path?: string): Promise<DccexIcon> {
  const drawn = new DccexIcon();
  if (path !== undefined) {
    drawn.path = path;
  }
  return await mounted(drawn);
}

test("the icon draws the path it was handed", async () => {
  const drawn = await icon(mdiPause);
  expect(part(drawn, "path").getAttribute("d")).toBe(mdiPause);
});

test("the shape is an SVG element and not an unknown one named path", async () => {
  // A `<path>` put through the HTML parser reads the same off a shadow root
  // and draws nothing, so the namespace is the assertion.
  const drawn = await icon(mdiPause);
  expect(part(drawn, "path").namespaceURI).toBe("http://www.w3.org/2000/svg");
});

test("an icon nobody handed a path to draws no shape", async () => {
  const drawn = await icon();
  expect(drawn.renderRoot.querySelector("path")).toBeNull();
});

test("the icon is not read out, because the control beside it says the word", async () => {
  const drawn = await icon(mdiPause);
  expect(part(drawn, "svg").getAttribute("aria-hidden")).toBe("true");
});

test("the icon takes the colour of whatever it is drawn in", async () => {
  const drawn = await icon(mdiPause);
  expect(part(drawn, "svg").getAttribute("fill")).toBe("currentColor");
});
