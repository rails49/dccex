/**
 * The **band**, mounted, with a station answering and with one that is not.
 *
 * The words themselves are the readings module's and are run through it
 * (`tests/ui/test_readings.py`); what is asserted here is that they reach a
 * page — that a band drawn from a conversation says what that conversation
 * means, and says it where a reader is looking. Read off the source, the same
 * claim passed on a component that never rendered (#1 seam 2, #126).
 *
 * The facts are the ones a page would hand it: lines the station said, folded
 * in as the page folds them, asked for at a moment. Nothing here asserts a
 * width — the reading that survives a narrow band is layout and happy-dom does
 * none (`tests/ui/test_band.py`).
 */

import { expect, test } from "vitest";

import { QUIET, asOf, heard } from "../src/readings.js";
import { DccexBand } from "../src/ui/dccex-band.js";
import { mounted, part, reads } from "./mounted.js";

/** When the station spoke, on the page's clock. */
const SPOKE = 1000;

/** A moment the station has spoken within, and one it has been quiet for
 *  longer than `SILENT_MS` before. */
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** The banner a station sends when it comes up, and the line it answers a
 *  power poll with. */
const BANNER = "<iDCC-EX V-5.2.76 / MEGA / STANDARD_MOTOR G-9db6d36>";
const HOT = "<p1>";

/** A station that came up and said its rails are hot. */
const TALKED = heard(heard(QUIET, BANNER, SPOKE), HOT, SPOKE);

/** A band handed what the page knew at `now`. */
async function band(now: number): Promise<DccexBand> {
  const drawn = new DccexBand();
  drawn.readings = asOf(TALKED, now);
  return await mounted(drawn);
}

test("a station that is answering reads as answering, rails hot", async () => {
  const drawn = await band(SOON);
  expect(reads(drawn, ".reading.link .reads")).toBe("answering");
  expect(reads(drawn, ".reading.rails .reads")).toBe("hot");
});

test("a station that stopped answering says so, in words and in red", async () => {
  const drawn = await band(LATER);
  expect(reads(drawn, ".reading.link .reads")).toBe("not answering");
  expect(part(drawn, ".reading.link").classList).toContain("fault");
});

test("the rails go unknown with the link, not held at what was said", async () => {
  expect(reads(await band(SOON), ".reading.rails .reads")).toBe("hot");
  expect(reads(await band(LATER), ".reading.rails .reads")).toBe("unknown");
});

test("the fault is the link and nothing else on the band", async () => {
  const drawn = await band(LATER);
  expect([...drawn.renderRoot.querySelectorAll(".fault")]).toHaveLength(1);
  expect(part(drawn, ".reading.rails").classList).not.toContain("fault");
});

test("a reading says which one it is beside what it reads", async () => {
  const drawn = await band(SOON);
  expect(reads(drawn, ".reading.link .of")).toBe("link");
  expect(reads(drawn, ".reading.rails .of")).toBe("rails");
});

test("a band handed no readings reads a station that said nothing", async () => {
  const drawn = await mounted(new DccexBand());
  expect(reads(drawn, ".reading.link .reads")).toBe("not answering");
  expect(reads(drawn, ".reading.rails .reads")).toBe("unknown");
});
