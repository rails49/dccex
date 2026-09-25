/**
 * The **tile**s, mounted, blanking together when the **link** drops.
 *
 * Which words a set of facts produces is the readings module's and is run
 * through it (`tests/ui/test_readings.py`); what is asserted here is that the
 * blanking happens on the page. It is the one of the five #1 named that a
 * source-text check could never have made: three tiles emptying at the same
 * moment is a property of a rendered row and not of a template (#126).
 *
 * The **build** blanks hardest, and it is drawn empty rather than dropped: a
 * build held over from before a flash would be the page reporting what it
 * cannot see, and a row that collapsed as the station went would move the
 * monitor under the reader's thumb (ADR-0008 d.3). That second half is the
 * stylesheet's `min-height` and is still held there — happy-dom does no
 * layout.
 */

import { expect, test } from "vitest";

import { QUIET, asOf, heard } from "../src/readings.js";
import { DccexTiles } from "../src/ui/dccex-tiles.js";
import { all, mounted, part, reads } from "./mounted.js";

/** When the station spoke, on the page's clock, and two moments to ask at:
 *  one it has spoken within, one it has been quiet past `SILENT_MS` for. */
const SPOKE = 1000;
const SOON = SPOKE + 1000;
const LATER = SPOKE + 60_000;

/** The banner a station sends when it comes up, what track A is set to, and
 *  the currents the tracks are drawing. */
const BANNER = "<iDCC-EX V-5.2.76 / MEGA / STANDARD_MOTOR G-9db6d36>";
const TRACK_A = "<= A MAIN>";
const CURRENTS = "<jI 250>";

/** The build that banner names. */
const BUILD = "9db6d36";

/** A station that came up, said what its track is and what it is drawing. */
const TALKED = [BANNER, TRACK_A, CURRENTS].reduce(
  (kept, line) => heard(kept, line, SPOKE),
  QUIET,
);

/** The tiles, handed what the page knew at `now`. */
async function tiles(now: number): Promise<DccexTiles> {
  const drawn = new DccexTiles();
  drawn.readings = asOf(TALKED, now);
  return await mounted(drawn);
}

test("a talking station fills the build and a tile for the track in use", async () => {
  const drawn = await tiles(SOON);
  expect(all(drawn, ".tile .of")).toStrictEqual([
    "link",
    "build",
    "track A · MAIN",
  ]);
  expect(all(drawn, ".tile .reads")).toStrictEqual([BUILD, "250 mA"]);
});

test("the build and the track blank together when the link drops", async () => {
  const drawn = await tiles(LATER);
  expect(all(drawn, ".tile .of")).toStrictEqual(["link", "build"]);
  expect(reads(drawn, ".tile .reads")).toBe("");
});

test("the build is drawn empty rather than held over from before", async () => {
  expect(all(await tiles(SOON), ".tile .reads")).toContain(BUILD);
  expect(all(await tiles(LATER), ".tile .reads")).not.toContain(BUILD);
});

test("the light says whether the station is answering, in words too", async () => {
  const talking = part(await tiles(SOON), ".dot");
  expect(talking.classList).toContain("on");
  expect(talking.getAttribute("aria-label")).toBe("answering");
  const quiet = part(await tiles(LATER), ".dot");
  expect(quiet.classList).toContain("off");
  expect(quiet.getAttribute("aria-label")).toBe("not answering");
});

test("tiles nobody handed readings to are the blanks of a quiet page", async () => {
  const drawn = await mounted(new DccexTiles());
  expect(all(drawn, ".tile .of")).toStrictEqual(["link", "build"]);
  expect(reads(drawn, ".tile .reads")).toBe("");
});
