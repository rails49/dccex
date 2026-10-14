/**
 * The **band**, drawn, with a station answering and with one that is not, and
 * with what `layout` says about the railroad's power and which railroad it has
 * loaded.
 *
 * The words are the readings module's and are run through it
 * (`tests/ui/test_readings.py`). The elements are look's (ADR-0023). What is
 * asserted here is what this page puts in them, and that each of the two
 * presses asks for what it says it will.
 */

import { type LookPower } from "@rails49/look";
import { expect, test } from "vitest";

import {
  QUIET,
  UNREACHABLE,
  asOf,
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

const HOT: Layout = { connected: true, power: "on", railroad: YARD };
const COLD: Layout = { connected: true, power: "off", railroad: YARD };
const HALTED: Layout = { connected: true, power: "stopped", railroad: YARD };
const UNSAID: Layout = { connected: true, power: null, railroad: null };
const UNREPORTED: Layout = { connected: true, power: null, railroad: undefined };

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

/** What pressing the toggle or the stop sign asked for. */
function asked(into: HTMLElement, which: ".power" | ".stop"): string[] {
  const power = one<LookPower>(into, "look-power");
  const seen: string[] = [];
  power.addEventListener("look-power", (e) => seen.push(e.detail.state));
  (power.renderRoot.querySelector(which) as HTMLElement).click();
  return seen;
}

test("the name is dcc-ex and the detail is the build", async () => {
  const about = one(await band(SOON, HOT), "look-about");
  expect(about.getAttribute("name")).toBe("dcc-ex");
  expect(about.getAttribute("detail")).toBe("9db6d36");
});

test("a station that is answering is a green dot and no words", async () => {
  const dot = one(await band(SOON, HOT), "look-dot");
  expect(dot.getAttribute("state")).toBe("up");
  expect(dot.textContent?.trim()).toBe("");
});

test("a station that stopped answering says so, and the build goes", async () => {
  const into = await band(LATER, HOT);
  expect(one(into, "look-dot").getAttribute("state")).toBe("down");
  expect(one(into, "look-dot").textContent?.trim()).toBe("dcc-ex offline");
  expect(one(into, "look-about").getAttribute("detail")).toBe("");
});

test("the railroad is a reading, and still named with the station silent", async () => {
  expect(one(await band(SOON, HOT), "look-reading").textContent).toBe(YARD);
  expect(one(await band(LATER, HOT), "look-reading").textContent).toBe(YARD);
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
    [COLD, "off"],
    [HALTED, "stopped"],
  ] as const) {
    const power = one(await band(SOON, layout), "look-power");
    expect(power.getAttribute("state")).toBe(state);
  }
});

test("the toggle asks for off when on and for on otherwise", async () => {
  expect(asked(await band(SOON, HOT), ".power")).toEqual(["off"]);
  expect(asked(await band(SOON, COLD), ".power")).toEqual(["on"]);
  expect(asked(await band(SOON, HALTED), ".power")).toEqual(["on"]);
});

test("STOP asks for stopped whatever layout reports", async () => {
  for (const layout of [HOT, COLD, HALTED, UNSAID]) {
    expect(asked(await band(SOON, layout), ".stop")).toEqual(["stopped"]);
  }
});

test("without the station or a word from layout, only the toggle is held", async () => {
  for (const [now, layout, why] of [
    [LATER, HOT, "no station"],
    [SOON, UNSAID, "no layout"],
  ] as const) {
    const into = await band(now, layout);
    const power = one(into, "look-power");
    expect(power.getAttribute("reason")).toBe("");
    expect(power.getAttribute("toggle-reason")).toBe(why);
    expect(asked(into, ".power")).toEqual([]);
    expect(asked(into, ".stop")).toEqual(["stopped"]);
  }
});

test("without the broker, both presses are held", async () => {
  const into = await band(SOON);
  expect(one(into, "look-power").getAttribute("reason")).toBe("no bus");
  expect(asked(into, ".power")).toEqual([]);
  expect(asked(into, ".stop")).toEqual([]);
});

test("a live press is held by nothing", async () => {
  const power = one(await band(SOON, HOT), "look-power");
  expect(power.getAttribute("reason")).toBe("");
  expect(power.getAttribute("toggle-reason")).toBe("");
});
