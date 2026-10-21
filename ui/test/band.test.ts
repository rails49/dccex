/**
 * The **band**, drawn, with a station answering and with one that is not, and
 * with what `layout` says about the railroad's power and which railroad it has
 * loaded.
 *
 * The words are the readings module's and are run through it
 * (`tests/ui/test_readings.py`). The elements are look's (ADR-0023). What is
 * asserted here is what this page puts in them, and that each of the two
 * presses asks `layout` for what ADR-0026 d.2 says, through `asked`.
 */

import { type LookPower } from "@rails49/look";
import { expect, test } from "vitest";

import {
  QUIET,
  UNREACHABLE,
  asOf,
  asked as wanted,
  heard,
  type Kept,
  type Layout,
} from "../src/readings.js";
import { drawBand } from "../src/ui/chrome.js";
import { drawn } from "./mounted.js";

/** When the station spoke, on the page's clock. */
const SPOKE = 1000;

/** A moment the station has spoken within, and one it has been quiet for
 *  longer than `SILENT_MS` before. */
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** The banner a station sends when it comes up. */
const BANNER = "<iDCC-EX V-5.2.76 / MEGA / STANDARD_MOTOR G-9db6d36>";

/** A station that came up and said which build it is running. */
const TALKED: Kept = heard(QUIET, BANNER, SPOKE);

/** The railroad `control` has loaded, as its railroad row names it (#239). */
const YARD = "crossover-yard";

const HOT: Layout = { connected: true, power: "on", railroad: YARD, built: true };
const COLD: Layout = { connected: true, power: "off", railroad: YARD, built: true };
const DRAINING: Layout = {
  connected: true,
  power: "draining",
  railroad: YARD,
  built: true,
};
const UNSAID: Layout = { connected: true, power: null, railroad: null, built: true };
const UNREPORTED: Layout = {
  connected: true,
  power: null,
  railroad: undefined,
  built: true,
};

/** A band drawn from what the page knew at `now` and what the bus said. */
async function band(
  now: number,
  layout: Layout = UNREACHABLE,
): Promise<HTMLElement> {
  return await drawn(drawBand(asOf(TALKED, now), layout));
}

function one<T extends Element>(into: HTMLElement, selector: string): T {
  const found = into.querySelector<T>(selector);
  if (found === null) {
    throw new Error(`nothing matching ${selector} was drawn`);
  }
  return found;
}

/** What pressing the toggle or the stop sign asks `layout` for, as the page
 *  maps look's press word (`dccex-app.ts`). */
function asked(
  into: HTMLElement,
  which: ".power" | ".stop",
): (string | null)[] {
  const power = one<LookPower>(into, "look-power");
  const seen: (string | null)[] = [];
  power.addEventListener("look-power", (e) =>
    seen.push(wanted(e.detail.state)),
  );
  (power.renderRoot.querySelector(which) as HTMLElement).click();
  return seen;
}

test("the UI name is dccex, and nothing else is on the left", async () => {
  const into = await band(SOON, HOT);
  expect(one(into, "look-band").getAttribute("ui")).toBe("dccex");
  expect(into.querySelector("look-about")).toBeNull();
});

test("a station that is answering is a green dot alone", async () => {
  const dot = one(await band(SOON, HOT), "look-dot");
  expect(dot.getAttribute("state")).toBe("up");
  expect(dot.textContent?.trim()).toBe("");
});

test("a station that stopped answering says so", async () => {
  const into = await band(LATER, HOT);
  expect(one(into, "look-dot").getAttribute("state")).toBe("down");
  expect(one(into, "look-dot").textContent?.trim()).toBe("dcc-ex offline");
});

test("the railroad is a reading, and still named with the station silent", async () => {
  expect(one(await band(SOON, HOT), "look-reading").textContent).toBe(YARD);
  expect(one(await band(LATER, HOT), "look-reading").textContent).toBe(YARD);
});

test("a railroad that is not built is named, with a muted not built after it", async () => {
  const reading = one(await band(SOON, { ...HOT, built: false }), "look-reading");
  expect(reading.textContent).toBe(`${YARD} not built`);
  expect(reading.querySelector(".unbuilt")?.textContent).toBe("not built");
  expect(one(await band(SOON, HOT), "look-reading").querySelector(".unbuilt")).toBeNull();
});

test("a railroad layout says none is loaded says so", async () => {
  const reading = one(await band(SOON, UNSAID), "look-reading");
  expect(reading.textContent).toBe("no railroad loaded");
});

test("an unreported railroad, or no broker, draws no reading", async () => {
  for (const layout of [UNREPORTED, UNREACHABLE]) {
    expect((await band(SOON, layout)).querySelector("look-reading")).toBeNull();
  }
});

test("power is the state layout reports", async () => {
  for (const [layout, state] of [
    [HOT, "on"],
    [DRAINING, "draining"],
    [COLD, "off"],
  ] as const) {
    const power = one(await band(SOON, layout), "look-power");
    expect(power.getAttribute("state")).toBe(state);
  }
});

test("the toggle drains when on and asks for on otherwise", async () => {
  expect(asked(await band(SOON, HOT), ".power")).toEqual(["draining"]);
  expect(asked(await band(SOON, COLD), ".power")).toEqual(["on"]);
  expect(asked(await band(SOON, DRAINING), ".power")).toEqual(["on"]);
});

test("STOP asks for off whatever layout reports", async () => {
  for (const layout of [HOT, COLD, DRAINING]) {
    expect(asked(await band(SOON, layout), ".stop")).toEqual(["off"]);
  }
});

test("without the broker or a word from layout, both presses wait", async () => {
  for (const [now, layout] of [
    [SOON, UNREACHABLE],
    [SOON, UNSAID],
    [LATER, UNSAID],
  ] as const) {
    const into = await band(now, layout);
    const power = one(into, "look-power");
    expect(power.getAttribute("reason")).toBe("Waiting for the station");
    expect(asked(into, ".power")).toEqual([]);
    expect(asked(into, ".stop")).toEqual([]);
  }
});

test("both presses are live once layout has reported, station or not", async () => {
  for (const now of [SOON, LATER]) {
    const into = await band(now, HOT);
    expect(one(into, "look-power").getAttribute("reason")).toBe("");
    expect(asked(into, ".power")).toEqual(["draining"]);
    expect(asked(into, ".stop")).toEqual(["off"]);
  }
});
