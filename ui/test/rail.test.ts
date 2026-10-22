/**
 * The **rail**, drawn: one `look-view` per **view**, and which of them is the
 * view in front of the person.
 *
 * What a choice does with the answer is the page's — it writes the hash and
 * the page reads it back (`ui/src/view.ts`, `tests/ui/test_page.py`) — so
 * what is asserted here is that the rail offers every view, names and draws
 * each one, marks the one being shown and hands the choice on.
 */

import { expect, test } from "vitest";

import { drawRail } from "../src/ui/chrome.js";
import { type View } from "../src/view.js";
import { drawn } from "./mounted.js";

/** The views a rail showing `view` offers, as name, label, glyph and whether
 *  each is current. */
async function rail(view: View): Promise<HTMLElement> {
  return await drawn(drawRail(view));
}

function offered(into: HTMLElement): string[][] {
  return [...into.querySelectorAll("look-view")].map((each) => [
    each.getAttribute("name") ?? "",
    each.getAttribute("label") ?? "",
    each.getAttribute("icon") ?? "",
    each.hasAttribute("current") ? "current" : "",
  ]);
}

test("the rail offers the four views in order, each named and drawn", async () => {
  // Written out rather than read off `VIEWS`, for the reason the list of views
  // is written out in `ui/test/view.test.ts`: a list taken from the thing
  // being checked would pass on whatever that list happened to say.
  expect(offered(await rail("monitor"))).toStrictEqual([
    ["monitor", "Monitor", "terminal", "current"],
    ["releases", "Releases", "lightning-charge", ""],
    ["script", "Script", "file-earmark-code", ""],
    ["journal", "Journal", "journal-text", ""],
  ]);
});

test("the view being shown is the one marked, and it is the only one", async () => {
  const marked = offered(await rail("releases")).filter(
    ([, , , current]) => current === "current",
  );
  expect(marked.map(([name]) => name)).toStrictEqual(["releases"]);
});

test("choosing another view hands its name on, and the current one nothing", async () => {
  const into = await rail("monitor");
  const chosen: string[] = [];
  into.addEventListener("look-view", (e) => chosen.push(e.detail.name));
  for (const name of ["releases", "monitor", "journal"]) {
    const view = into.querySelector(`look-view[name=${name}]`) as HTMLElement & {
      renderRoot: ShadowRoot;
    };
    (view.renderRoot.querySelector("button") as HTMLElement).click();
  }
  expect(chosen).toStrictEqual(["releases", "journal"]);
});
