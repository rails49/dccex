/**
 * The **tile**s, mounted: one per track in use, and the row emptying when the
 * **link** drops.
 *
 * Which words a set of facts produces is the readings module's and is run
 * through it (`tests/ui/test_readings.py`); what is asserted here is what
 * reaches the page. It is the one of the five #1 named that a source-text check
 * could never have made: a row of three tiles going at the same moment is a
 * property of a rendered row and not of a template (#126).
 *
 * The row keeps its height while it is empty, so the monitor does not move
 * under the reader's thumb as the station goes (ADR-0008 d.3). That half is the
 * stylesheet's `min-height` and is still held there — happy-dom does no layout.
 */

import { expect, test } from "vitest";

import { QUIET, asOf, heard } from "../src/readings.js";
import { DccexTiles } from "../src/ui/dccex-tiles.js";
import { all, mounted, part } from "./mounted.js";

/** When the station spoke, on the page's clock, and two moments to ask at:
 *  one it has spoken within, one it has been quiet past `SILENT_MS` for. */
const SPOKE = 1000;
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** What two tracks are set to, what they are drawing, the most they may draw,
 *  and the power on each: A on, B off. C is set to NONE and is not in use. */
const MODES = ["<= A MAIN>", "<= B PROG>", "<= C NONE>"];
const CURRENTS = "<jI 250 12 0>";
const LIMITS = "<jG 1233 250 250>";
const POWER = ["<p1 A>", "<p0 B>"];

/** A station that came up, said what its tracks are and what they are doing. */
const TALKED = [...MODES, CURRENTS, LIMITS, ...POWER].reduce(
  (kept, line) => heard(kept, line, SPOKE),
  QUIET,
);

/** The tiles, handed what the page knew at `now`. */
async function tiles(now: number): Promise<DccexTiles> {
  const drawn = new DccexTiles();
  drawn.readings = asOf(TALKED, now);
  return await mounted(drawn);
}

test("a talking station is a tile per track in use, in letter order", async () => {
  const drawn = await tiles(SOON);
  expect(all(drawn, ".tile .mode")).toStrictEqual(["MAIN", "PROG"]);
  expect(all(drawn, ".tile .draws")).toStrictEqual(["250 mA", "12 mA"]);
  expect(all(drawn, ".tile .most")).toStrictEqual(["1233 mA", "250 mA"]);
});

test("the power symbol is the track's power, in colour and in words", async () => {
  const drawn = await tiles(SOON);
  const [on, off] = [...drawn.renderRoot.querySelectorAll(".power")];
  expect(on?.classList).toContain("on");
  expect(on?.getAttribute("aria-label")).toBe("track A power is on");
  expect(off?.classList).toContain("off");
  expect(off?.getAttribute("aria-label")).toBe("track B power is off");
});

test("a track the station has said nothing about the power of is neither", async () => {
  const drawn = new DccexTiles();
  drawn.readings = asOf(heard(QUIET, "<= A MAIN>", SPOKE), SOON);
  const power = part(await mounted(drawn), ".power");
  expect([...power.classList]).toStrictEqual(["power"]);
  expect(power.getAttribute("aria-label")).toBe("track A power is unknown");
});

test("the tiles go together when the link drops", async () => {
  expect(all(await tiles(SOON), ".tile")).toHaveLength(2);
  expect(all(await tiles(LATER), ".tile")).toStrictEqual([]);
});

test("a reading the station has not given is blank and not a zero", async () => {
  const drawn = new DccexTiles();
  drawn.readings = asOf(heard(QUIET, "<= A MAIN>", SPOKE), SOON);
  expect(all(await mounted(drawn), ".tile .draws")).toStrictEqual([""]);
  expect(all(drawn, ".tile .most")).toStrictEqual([""]);
});

test("tiles nobody handed readings to are the empty row of a quiet page", async () => {
  const drawn = await mounted(new DccexTiles());
  expect(all(drawn, ".tile")).toStrictEqual([]);
});
