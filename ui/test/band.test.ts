/**
 * The **band**, mounted, with a station answering and with one that is not.
 *
 * The words themselves are the readings module's and are run through it
 * (`tests/ui/test_readings.py`); what is asserted here is that they reach a
 * page — that a band drawn from a conversation says what that conversation
 * means, and says it where a reader is looking — and that the one control on
 * it sends what it says it will. Read off the source, the same claim passed on
 * a component that never rendered (#1 seam 2, #126).
 *
 * The facts are the ones a page would hand it: lines the station said, folded
 * in as the page folds them, asked for at a moment. Nothing here asserts a
 * width — which of the three things a narrow band keeps is layout and
 * happy-dom does none (`tests/ui/test_band.py`).
 */

import { expect, test } from "vitest";

import { QUIET, asOf, heard, type Kept } from "../src/readings.js";
import { DccexBand } from "../src/ui/dccex-band.js";
import { mounted, part, press, reads } from "./mounted.js";

/** When the station spoke, on the page's clock. */
const SPOKE = 1000;

/** A moment the station has spoken within, and one it has been quiet for
 *  longer than `SILENT_MS` before. */
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** The banner a station sends when it comes up, and the lines it answers a
 *  power poll with. */
const BANNER = "<iDCC-EX V-5.2.76 / MEGA / STANDARD_MOTOR G-9db6d36>";
const HOT = "<p1>";
const COLD = "<p0>";

/** What the station said, folded in as the page folds it. */
function told(...lines: string[]): Kept {
  return lines.reduce((kept, line) => heard(kept, line, SPOKE), QUIET);
}

/** A station that came up and said its rails are hot, and one that said they
 *  are cold. */
const TALKED = told(BANNER, HOT);
const DEAD = told(BANNER, COLD);

/** A band handed what the page knew at `now`, and what it sent. */
async function band(
  kept: Kept,
  now: number,
): Promise<{ drawn: DccexBand; sent: string[] }> {
  const sent: string[] = [];
  const drawn = new DccexBand();
  drawn.readings = asOf(kept, now);
  drawn.sends = (typed: string) => {
    sent.push(typed);
    return typed;
  };
  return { drawn: await mounted(drawn), sent };
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

test("rails that are hot are a green button that cuts the power", async () => {
  const { drawn, sent } = await band(TALKED, SOON);
  expect(part(drawn, ".power").classList).toContain("on");
  expect(part(drawn, ".power").getAttribute("title")).toBe("power off");
  expect(part(drawn, ".power").getAttribute("aria-label")).toBe("power off");
  press(drawn, ".power");
  expect(sent).toEqual(["<0>"]);
});

test("rails that are cold are a red button that turns the power on", async () => {
  const { drawn, sent } = await band(DEAD, SOON);
  expect(part(drawn, ".power").classList).toContain("off");
  expect(part(drawn, ".power").getAttribute("title")).toBe("power on");
  press(drawn, ".power");
  expect(sent).toEqual(["<1>"]);
});

test("a press of the power button is one message and not a second", async () => {
  const { drawn, sent } = await band(TALKED, SOON);
  press(drawn, ".power");
  press(drawn, ".power");
  expect(sent).toEqual(["<0>", "<0>"]);
});

test("the button presses nothing while the link is down", async () => {
  const { drawn, sent } = await band(TALKED, LATER);
  const power = part(drawn, ".power") as HTMLButtonElement;
  expect(power.disabled).toBe(true);
  expect(power.classList).not.toContain("on");
  expect(power.classList).not.toContain("off");
  expect(power.getAttribute("title")).toBe("power");
  press(drawn, ".power");
  expect(sent).toEqual([]);
});

test("the button is drawn as an icon and not as a word", async () => {
  const { drawn } = await band(TALKED, SOON);
  expect(reads(drawn, ".power")).toBe("");
  expect(part(drawn, ".power dccex-icon")).toBeTruthy();
});

test("a band handed no readings reads a station that said nothing", async () => {
  const drawn = await mounted(new DccexBand());
  expect(reads(drawn, ".says")).toBe("dcc-ex offline");
  expect(reads(drawn, ".build")).toBe("");
  expect((part(drawn, ".power") as HTMLButtonElement).disabled).toBe(true);
});

test("a band nobody handed a sending to presses nothing", async () => {
  const drawn = new DccexBand();
  drawn.readings = asOf(TALKED, SOON);
  press(await mounted(drawn), ".power");
});
