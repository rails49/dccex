/**
 * The **band**, mounted, with a station answering and with one that is not,
 * and with what `layout` says about the railroad's power.
 *
 * The words themselves are the readings module's and are run through it
 * (`tests/ui/test_readings.py`); what is asserted here is that they reach a
 * page — that a band drawn from a conversation and a bus says what the two of
 * them mean, and says it where a reader is looking — and that each of the two
 * presses on it asks for what it says it will. Read off the source, the same
 * claim passed on a component that never rendered (#1 seam 2, #126).
 *
 * The facts are the ones a page would hand it: lines the station said, folded
 * in as the page folds them, asked for at a moment, and the bus reading the
 * page holds beside them (ADR-0017). What the connection behind that reading
 * does is driven on its own (`ui/test/bus.test.ts`). Nothing here asserts a
 * width — what a narrow band keeps is layout and happy-dom does none
 * (`tests/ui/test_band.py`).
 */

import { expect, test } from "vitest";

import {
  QUIET,
  UNREACHABLE,
  asOf,
  heard,
  type Kept,
  type Layout,
} from "../src/readings.js";
import { DccexBand } from "../src/ui/dccex-band.js";
import { mounted, part, press, reads } from "./mounted.js";

/** When the station spoke, on the page's clock. */
const SPOKE = 1000;

/** A moment the station has spoken within, and one it has been quiet for
 *  longer than `SILENT_MS` before. */
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** The banner a station sends when it comes up. */
const BANNER = "<iDCC-EX V-5.2.76 / MEGA / STANDARD_MOTOR G-9db6d36>";

/** What the station said, folded in as the page folds it. */
function told(...lines: string[]): Kept {
  return lines.reduce((kept, line) => heard(kept, line, SPOKE), QUIET);
}

/** A station that came up and said which build it is running. */
const TALKED = told(BANNER);

/** What the STOP press is titled while it can be pressed (ADR-0020 d.3). */
const STOPS = "stop every locomotive where it stands";

/** What the bus says: the broker and each of the three rows `layout`
 *  publishes, and the broker with nothing reported on it yet. */
const HOT: Layout = { connected: true, power: "on" };
const COLD: Layout = { connected: true, power: "off" };
const HALTED: Layout = { connected: true, power: "stopped" };
const UNSAID: Layout = { connected: true, power: null };

/** A band handed what the page knew at `now` and what the bus said, and what
 *  it asked `layout` for. */
async function band(
  kept: Kept,
  now: number,
  layout: Layout = UNREACHABLE,
): Promise<{ drawn: DccexBand; asked: string[] }> {
  const asked: string[] = [];
  const drawn = new DccexBand();
  drawn.readings = asOf(kept, now);
  drawn.layout = layout;
  drawn.wants = (power: string) => {
    asked.push(power);
  };
  return { drawn: await mounted(drawn), asked };
}

test("a station that is answering reads as answering, with its build", async () => {
  const { drawn } = await band(TALKED, SOON);
  expect(part(drawn, ".dot").classList).toContain("on");
  expect(reads(drawn, ".build")).toBe("9db6d36");
});

test("a station that stopped answering says so in words, and the build goes", async () => {
  const { drawn } = await band(TALKED, LATER);
  expect(reads(drawn, ".says")).toBe("dcc-ex offline");
  expect(part(drawn, ".dot").classList).toContain("off");
  expect(reads(drawn, ".build")).toBe("");
});

test("a station that is answering is the dot and no words", async () => {
  const { drawn } = await band(TALKED, SOON);
  expect(drawn.renderRoot.querySelector(".says")).toBeNull();
  expect(part(drawn, ".link").getAttribute("aria-label")).toBe("answering");
});

test("the link says which reading it is to a reader who cannot see it", async () => {
  const { drawn } = await band(TALKED, LATER);
  expect(part(drawn, ".link").getAttribute("aria-label")).toBe("dcc-ex offline");
});

test("power layout reports as on is a green button that asks for off", async () => {
  const { drawn, asked } = await band(TALKED, SOON, HOT);
  expect(part(drawn, ".power").classList).toContain("on");
  expect(part(drawn, ".power").getAttribute("title")).toBe("power off");
  expect(part(drawn, ".power").getAttribute("aria-label")).toBe("power off");
  press(drawn, ".power");
  expect(asked).toEqual(["off"]);
});

test("power layout reports as off is an outlined button that asks for on", async () => {
  const { drawn, asked } = await band(TALKED, SOON, COLD);
  expect(part(drawn, ".power").classList).toContain("off");
  expect(part(drawn, ".power").getAttribute("title")).toBe("power on");
  press(drawn, ".power");
  expect(asked).toEqual(["on"]);
});

test("a railroad layout reports as stopped is red and asks for on", async () => {
  const { drawn, asked } = await band(TALKED, SOON, HALTED);
  expect(part(drawn, ".power").classList).toContain("stopped");
  expect(part(drawn, ".power").getAttribute("title")).toBe("power on");
  press(drawn, ".power");
  expect(asked).toEqual(["on"]);
});

test("a press of the power button is one ask and not a second", async () => {
  const { drawn, asked } = await band(TALKED, SOON, HOT);
  press(drawn, ".power");
  press(drawn, ".power");
  expect(asked).toEqual(["off", "off"]);
});

test("the button presses nothing while the bus is unreachable", async () => {
  const { drawn, asked } = await band(TALKED, SOON);
  const power = part(drawn, ".power") as HTMLButtonElement;
  expect(power.disabled).toBe(true);
  expect(power.getAttribute("title")).toBe("no bus");
  press(drawn, ".power");
  expect(asked).toEqual([]);
});

test("the button presses nothing while the link is down", async () => {
  const { drawn, asked } = await band(TALKED, LATER, HOT);
  const power = part(drawn, ".power") as HTMLButtonElement;
  expect(power.disabled).toBe(true);
  expect(power.getAttribute("title")).toBe("no station");
  press(drawn, ".power");
  expect(asked).toEqual([]);
});

test("the button presses nothing until layout has reported", async () => {
  const { drawn, asked } = await band(TALKED, SOON, UNSAID);
  const power = part(drawn, ".power") as HTMLButtonElement;
  expect(power.disabled).toBe(true);
  expect(power.getAttribute("title")).toBe("no layout");
  press(drawn, ".power");
  expect(asked).toEqual([]);
});

test("a button that presses nothing wears no chip", async () => {
  const { drawn } = await band(TALKED, LATER, HALTED);
  const power = part(drawn, ".power") as HTMLButtonElement;
  for (const chip of ["on", "off", "stopped"]) {
    expect(power.classList).not.toContain(chip);
  }
});

test("the button is drawn as an icon and not as a word", async () => {
  const { drawn } = await band(TALKED, SOON, HOT);
  expect(reads(drawn, ".power")).toBe("");
  expect(part(drawn, ".power dccex-icon")).toBeTruthy();
});

test("a band handed nothing reads a station and a bus it has not reached", async () => {
  const drawn = await mounted(new DccexBand());
  expect(reads(drawn, ".says")).toBe("dcc-ex offline");
  expect(reads(drawn, ".build")).toBe("");
  const power = part(drawn, ".power") as HTMLButtonElement;
  expect(power.disabled).toBe(true);
  expect(power.getAttribute("title")).toBe("no bus");
});

test("a band nobody handed a way to ask presses nothing", async () => {
  const drawn = new DccexBand();
  drawn.readings = asOf(TALKED, SOON);
  drawn.layout = HOT;
  press(await mounted(drawn), ".power");
});

test("a STOP press asks layout to stop every locomotive where it stands", async () => {
  const { drawn, asked } = await band(TALKED, SOON, HOT);
  const stop = part(drawn, ".stop") as HTMLButtonElement;
  expect(reads(drawn, ".stop")).toBe("STOP");
  expect(stop.disabled).toBe(false);
  expect(stop.getAttribute("title")).toBe(STOPS);
  expect(stop.getAttribute("aria-label")).toBe(STOPS);
  press(drawn, ".stop");
  expect(asked).toEqual(["stopped"]);
});

test("STOP is the same press whatever layout reports", async () => {
  for (const layout of [HOT, COLD, HALTED, UNSAID]) {
    const { drawn, asked } = await band(TALKED, SOON, layout);
    const stop = part(drawn, ".stop") as HTMLButtonElement;
    expect(stop.disabled).toBe(false);
    expect(stop.getAttribute("title")).toBe(STOPS);
    expect(stop.className).toBe("press stop");
    press(drawn, ".stop");
    expect(asked).toEqual(["stopped"]);
  }
});

test("STOP is pressed with the link down and with nothing reported", async () => {
  const { drawn, asked } = await band(TALKED, LATER, UNSAID);
  expect((part(drawn, ".stop") as HTMLButtonElement).disabled).toBe(false);
  press(drawn, ".stop");
  expect(asked).toEqual(["stopped"]);
});

test("STOP presses nothing while the bus is unreachable", async () => {
  const { drawn, asked } = await band(TALKED, SOON);
  const stop = part(drawn, ".stop") as HTMLButtonElement;
  expect(stop.disabled).toBe(true);
  expect(stop.getAttribute("title")).toBe("no bus");
  press(drawn, ".stop");
  expect(asked).toEqual([]);
});

test("a press of STOP is one ask and not a second", async () => {
  const { drawn, asked } = await band(TALKED, SOON, HALTED);
  press(drawn, ".stop");
  press(drawn, ".stop");
  expect(asked).toEqual(["stopped", "stopped"]);
});

test("STOP is right of the power button", async () => {
  const { drawn } = await band(TALKED, SOON, HOT);
  const pressed = [...drawn.renderRoot.querySelectorAll("button")].map(
    (button) => button.className,
  );
  expect(pressed).toHaveLength(2);
  expect(pressed[0]).toContain("power");
  expect(pressed[1]).toContain("stop");
});
