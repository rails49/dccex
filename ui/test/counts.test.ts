/**
 * The statistics table, mounted: a row per district and one for the station.
 *
 * What the counts are and what words they are drawn in is the reading module's
 * and is run through it (`tests/ui/test_incidents.py`); what is asserted here
 * is that a cell lands under the column it belongs to and that the station's
 * row is the one carrying its two counts — which a check reading the template
 * could not say (#126).
 *
 * The facts are the ones the view hands down: one reading of one journal.
 */

import { expect, test } from "vitest";

import { HEADINGS, type Row, type Standing } from "../src/incidents.js";
import { DccexCounts } from "../src/ui/dccex-counts.js";
import { all, mounted, part, reads } from "./mounted.js";

/** Two districts, as the reading module hands them over: one the station cut
 *  and one it only ever watched. A cell is one string and the blanks are the
 *  readings nobody took. */
const DISTRICTS: Row[] = [
  {
    district: "A",
    cells: ["0", "0", "0", "1", "0", "1", "3120 mA", "5 m 00 s", "0", "0.50 h", "2.00"],
  },
  {
    district: "D",
    cells: ["0", "0", "1", "0", "0", "0", "", "0 ms", "0", "0.00 h", ""],
  },
];

/** The station's own row. */
const STATION: Standing = {
  district: "station",
  says: ["1 link loss", "0 restarts"],
};

/** The table, handed one reading. */
async function table(
  districts: Row[],
  station: Standing | null,
): Promise<DccexCounts> {
  const drawn = new DccexCounts();
  drawn.districts = districts;
  drawn.station = station;
  return await mounted(drawn);
}

/** What one district's row reads, by the column each cell is under. */
function row(drawn: DccexCounts, district: string): Record<string, string> {
  const found = [...drawn.renderRoot.querySelectorAll("tr.district")].find(
    (tr) => tr.querySelector(".name")?.textContent?.trim() === district,
  );
  if (found === undefined) {
    throw new Error(`no row for ${district}`);
  }
  const cells = [...found.querySelectorAll(".count")].map((cell) =>
    (cell.textContent ?? "").trim(),
  );
  return Object.fromEntries(
    HEADINGS.slice(1).map((heading, where) => [heading, cells[where] ?? ""]),
  );
}

test("the columns are the ones the reading module names, in that order", async () => {
  expect(all(await table(DISTRICTS, STATION), ".heading")).toStrictEqual([
    ...HEADINGS,
  ]);
});

test("a count lands under the column it belongs to", async () => {
  const drawn = await table(DISTRICTS, STATION);
  expect(row(drawn, "A")).toStrictEqual({
    "repeated reversal": "0",
    reversal: "0",
    "slow reversal": "0",
    trip: "1",
    spike: "0",
    trips: "1",
    "peak mA": "3120 mA",
    cut: "5 m 00 s",
    flips: "0",
    hours: "0.50 h",
    "per hour": "2.00",
  });
  expect(row(drawn, "D")["slow reversal"]).toBe("1");
});

test("a reading nobody took is a blank cell and not a zero", async () => {
  const drawn = await table(DISTRICTS, STATION);
  expect(row(drawn, "D")["peak mA"]).toBe("");
  expect(row(drawn, "D")["per hour"]).toBe("");
});

test("one row per district, in the order they are handed down", async () => {
  const drawn = await table(DISTRICTS, STATION);
  expect(all(drawn, "tr.district .name")).toStrictEqual(["A", "D"]);
});

test("the station's link losses and restarts are its own row", async () => {
  const drawn = await table(DISTRICTS, STATION);
  expect(reads(drawn, "tr.station .name")).toBe("station");
  expect(reads(drawn, "tr.station .links")).toBe("1 link loss");
  expect(reads(drawn, "tr.station .restarts")).toBe("0 restarts");
  // It lies across the district columns rather than putting a number under
  // one of them: there is no trip and no peak to count of the station.
  expect(part(drawn, "tr.station .restarts").getAttribute("colspan")).toBe(
    String(HEADINGS.length - 2),
  );
});

test("a table nobody has handed rows to draws the headings and no rows", async () => {
  const drawn = await table([], null);
  expect(all(drawn, ".heading")).toHaveLength(HEADINGS.length);
  expect(all(drawn, "tr.district")).toStrictEqual([]);
  expect(all(drawn, "tr.station")).toStrictEqual([]);
});

test("the table presses nothing", async () => {
  // The period, the toggle, the reload and the clear are the controls'
  // (`ui/test/controls.test.ts`): a table that offered one would be a second
  // place this view is driven from.
  const drawn = await table(DISTRICTS, STATION);
  expect(drawn.renderRoot.querySelectorAll("button")).toHaveLength(0);
  expect(drawn.renderRoot.querySelectorAll("input")).toHaveLength(0);
});
