/**
 * The **rail**, mounted: one button per **view**, and which of them is the
 * view in front of the person.
 *
 * What a press does with the answer is the page's — it writes the hash and
 * the page reads it back (`ui/src/view.ts`, `tests/ui/test_page.py`) — so what
 * is asserted here is that the rail offers every view, says each one's word,
 * marks the one being shown and hands the press on.
 *
 * Nothing here asserts a width or a colour: happy-dom does no layout and has
 * no cascade, so which button wears the chip is held against the stylesheet
 * (`ui/test/mounted.ts`, `tests/ui/test_rail.py`).
 */

import { mdiConsole, mdiFlashAlert, mdiScriptTextOutline } from "@mdi/js";
import { expect, test } from "vitest";

import { type DccexIcon } from "../src/ui/dccex-icon.js";
import { DccexRail } from "../src/ui/dccex-rail.js";
import { type View } from "../src/view.js";
import { mounted, part, press, reads } from "./mounted.js";

/** A rail showing `view`, and what its buttons picked. */
async function rail(view?: View): Promise<{ drawn: DccexRail; picked: View[] }> {
  const picked: View[] = [];
  const drawn = new DccexRail();
  if (view !== undefined) {
    drawn.view = view;
  }
  drawn.picks = (to: View) => {
    picked.push(to);
  };
  return { drawn: await mounted(drawn), picked };
}

/** What the button for `view` is drawn as: the word it carries both ways, the
 *  path of the icon in it, and whether it is the view being shown. */
function button(
  drawn: DccexRail,
  view: View,
): {
  tooltip: string | null;
  label: string | null;
  path: string;
  current: string | null;
} {
  const pressed = part(drawn, `button.${view}`);
  return {
    tooltip: pressed.getAttribute("title"),
    label: pressed.getAttribute("aria-label"),
    path: (part(drawn, `button.${view} dccex-icon`) as DccexIcon).path,
    current: pressed.getAttribute("aria-current"),
  };
}

test("the rail carries one button per view and no others", async () => {
  const { drawn } = await rail();
  // Written out rather than read off `VIEWS`, for the reason the list of views
  // is written out in `ui/test/view.test.ts`: a count taken from the thing
  // being checked would pass on whatever that list happened to say.
  expect(drawn.renderRoot.querySelectorAll("button")).toHaveLength(3);
});

test("each button carries its view's word as a tooltip and as a label", async () => {
  const { drawn } = await rail();
  for (const view of ["monitor", "releases", "script"] as const) {
    expect(button(drawn, view).tooltip).toBe(view);
    expect(button(drawn, view).label).toBe(view);
  }
});

test("each view is drawn as its own shape", async () => {
  const { drawn } = await rail();
  expect(button(drawn, "monitor").path).toBe(mdiConsole);
  expect(button(drawn, "releases").path).toBe(mdiFlashAlert);
  expect(button(drawn, "script").path).toBe(mdiScriptTextOutline);
});

test("a button drawn as an icon says nothing in text", async () => {
  // The word is the tooltip's and the label's, as the monitor's controls do
  // it: a check that asked for the text would pass on a button with both.
  const { drawn } = await rail();
  expect(reads(drawn, "button.monitor")).toBe("");
  expect(reads(drawn, "button.releases")).toBe("");
  expect(reads(drawn, "button.script")).toBe("");
});

test("the view being shown is the one marked, and it is the only one", async () => {
  const { drawn } = await rail("releases");
  expect(button(drawn, "releases").current).toBe("page");
  expect(button(drawn, "monitor").current).toBe(null);
  expect(button(drawn, "script").current).toBe(null);
});

test("a rail nobody told which view is showing marks the one a page opens on", async () => {
  const { drawn } = await rail();
  expect(button(drawn, "monitor").current).toBe("page");
  expect(button(drawn, "releases").current).toBe(null);
  expect(button(drawn, "script").current).toBe(null);
});

test("pressing a button picks that view", async () => {
  const { drawn, picked } = await rail();
  press(drawn, "button.releases");
  press(drawn, "button.script");
  press(drawn, "button.monitor");
  expect(picked).toStrictEqual(["releases", "script", "monitor"]);
});

test("a rail nobody handed a picking to picks nothing", async () => {
  // It draws every button and pressing one does nothing, for the reason a
  // band nobody handed a sending to presses nothing: which view is in front
  // of a person is the page's and not this component's.
  const drawn = await mounted(new DccexRail());
  press(drawn, "button.releases");
  expect(button(drawn, "monitor").current).toBe("page");
});
