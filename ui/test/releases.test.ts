/**
 * The **release** row, mounted, marking the **build** that is on the station.
 *
 * The ordering, the dates and which row is marked are the listing module's and
 * are run through it (`tests/ui/test_releases.py`); what is asserted here is
 * that the mark lands on the row it is about. A source-text check could say
 * the component draws `ON_STATION` somewhere and could not say which release
 * an operator would read it beside, which is the whole of the claim #1 asked
 * for (#126).
 *
 * The facts are the ones a page would hand it: what the **face** answered
 * under `releases`, and what the station says it is running.
 */

import { expect, test } from "vitest";

import {
  NO_FIRMWARE,
  ON_STATION,
  UNREADABLE,
  type Carried,
} from "../src/releases.js";
import { DccexReleases } from "../src/ui/dccex-releases.js";
import { all, mounted, part, reads } from "./mounted.js";

/** What the face answered: two releases with a firmware to write from and one
 *  published without one, newest last so that the ordering is drawn and not
 *  copied. */
const CARRIED: Carried[] = [
  { tag: "v5.2.74", published: "2026-06-01T09:00:00Z", flashable: true },
  { tag: "v5.2.75", published: "2026-07-02T09:00:00Z", flashable: false },
  { tag: "v5.2.76", published: "2026-08-03T09:00:00Z", flashable: true },
];

/** The tag the station is running in most of what follows. */
const RUNNING = "v5.2.75";

/** The row, handed what the face answered and what the station said. */
async function row(
  carried: Carried[] | null,
  build: string | null,
): Promise<DccexReleases> {
  const drawn = new DccexReleases();
  drawn.carried = carried;
  drawn.build = build;
  return await mounted(drawn);
}

/** The tags of the rows that carry the mark. */
function marked(drawn: DccexReleases): string[] {
  return [...drawn.renderRoot.querySelectorAll(".release")]
    .filter((release) => release.querySelector(".mark") !== null)
    .map((release) => release.querySelector(".tag")?.textContent ?? "");
}

test("the releases are listed newest first", async () => {
  expect(all(await row(CARRIED, RUNNING), ".tag")).toStrictEqual([
    "v5.2.76",
    "v5.2.75",
    "v5.2.74",
  ]);
});

test("the row whose tag is the build is the one that carries the mark", async () => {
  const drawn = await row(CARRIED, RUNNING);
  expect(marked(drawn)).toStrictEqual([RUNNING]);
  expect(reads(drawn, ".release.on .mark")).toBe(ON_STATION);
  expect(reads(drawn, ".release.on .tag")).toBe(RUNNING);
});

test("a station that is not answering has no build and marks nothing", async () => {
  expect(marked(await row(CARRIED, null))).toStrictEqual([]);
});

test("a build the source does not carry marks nothing either", async () => {
  expect(marked(await row(CARRIED, "v9.9.9"))).toStrictEqual([]);
});

test("the release there is nothing to write from says so and is not pressable", async () => {
  const drawn = await row(CARRIED, RUNNING);
  const bare = part(drawn, ".release.on");
  expect(bare.querySelector(".bare")?.textContent).toBe(NO_FIRMWARE);
  expect(bare.querySelector(".chooses")).toBeNull();
  expect(all(drawn, ".chooses")).toHaveLength(2);
});

test("a face that did not answer says so rather than listing nothing", async () => {
  const drawn = await row(null, RUNNING);
  expect(reads(drawn, ".says")).toBe(UNREADABLE);
  expect(all(drawn, ".release")).toStrictEqual([]);
});

test("the day is drawn and not the stamp the source published it with", async () => {
  expect(all(await row(CARRIED, RUNNING), ".published")).toStrictEqual([
    "2026-08-03",
    "2026-07-02",
    "2026-06-01",
  ]);
});
