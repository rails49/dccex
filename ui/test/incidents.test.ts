/**
 * The incident list, mounted: the rows, and what opening one shows.
 *
 * The order, the stamps, the kinds and the numbers are the reading module's and
 * are run through it (`tests/ui/test_incidents.py`); what is asserted here is
 * that each reading lands on the row it is about, that a row opens on the
 * journal lines that row is made of, and that a routine line is drawn as the
 * quieter thing it is — none of which a check reading the template could say
 * (#126).
 */

import { expect, test } from "vitest";

import { COLUMNS, type Entry } from "../src/incidents.js";
import { DccexIncidents } from "../src/ui/dccex-incidents.js";
import { all, mounted, part, reads } from "./mounted.js";

/** One reversal, with the four lines it is made of, as the reading module
 *  hands it over. */
const REVERSAL: Entry = {
  at: "2026-10-12T18:00:01.100+00:00",
  when: "2026-10-12 18:00:01.100",
  district: "C",
  kind: "reversal",
  says: "",
  trips: "1",
  milliamps: "4210 mA",
  cut: "100 ms",
  routine: false,
  lines: [
    {
      at: "2026-10-12T18:00:01.000+00:00",
      when: "2026-10-12 18:00:01.000",
      said: "<* TRACK C INVERT (fast) *>",
    },
    {
      at: "2026-10-12T18:00:01.100+00:00",
      when: "2026-10-12 18:00:01.100",
      said: "<* TRACK C FAST OVERLOAD 4210mA. Pause 100ms *>",
    },
  ],
};

/** The link going down, which is the station's own and names no district. */
const OUTAGE: Entry = {
  at: "2026-10-12T18:00:05.000+00:00",
  when: "2026-10-12 18:00:05.000",
  district: "station",
  kind: "link",
  says: "",
  trips: "0",
  milliamps: "",
  cut: "0 ms",
  routine: false,
  lines: [
    {
      at: "2026-10-12T18:00:05.000+00:00",
      when: "2026-10-12 18:00:05.000",
      said: "link down",
    },
  ],
};

/** One line no incident took: the railroad working, and a row only where a
 *  reader asked for them. */
const ROUTINE: Entry = {
  at: "2026-10-12T18:00:00.000+00:00",
  when: "2026-10-12 18:00:00.000",
  district: "C",
  kind: "",
  says: "<p1 C>",
  trips: "",
  milliamps: "",
  cut: "",
  routine: true,
  lines: [
    {
      at: "2026-10-12T18:00:00.000+00:00",
      when: "2026-10-12 18:00:00.000",
      said: "<p1 C>",
    },
  ],
};

/** The list, handed the rows a view would hand it. */
async function list(entries: Entry[]): Promise<DccexIncidents> {
  const drawn = new DccexIncidents();
  drawn.entries = entries;
  return await mounted(drawn);
}

/** What the row for `kind` reads, part by part. */
function row(drawn: DccexIncidents, which: number): Record<string, string> {
  const found = drawn.renderRoot.querySelectorAll(".incident")[which];
  if (found === undefined) {
    throw new Error(`no row ${which}`);
  }
  const part = (selector: string) =>
    (found.querySelector(selector)?.textContent ?? "").trim();
  return {
    when: part(".when"),
    district: part(".district"),
    kind: part(".kind"),
    trips: part(".trips"),
    milliamps: part(".milliamps"),
    cut: part(".cut"),
    says: part(".says"),
  };
}

test("a row says the time, the district, the kind and the numbers", async () => {
  expect(row(await list([OUTAGE, REVERSAL]), 1)).toStrictEqual({
    when: "2026-10-12 18:00:01.100",
    district: "C",
    kind: "reversal",
    trips: "1",
    milliamps: "4210 mA",
    cut: "100 ms",
    says: "",
  });
});

test("the list is headed once with the module's columns", async () => {
  expect(all(await list([OUTAGE, REVERSAL]), ".head .heading")).toStrictEqual(
    COLUMNS,
  );
});

test("a row's parts are in the order of the headings", async () => {
  // The columns are laid by position, so a part out of order is a number under
  // the wrong heading.
  const drawn = await list([REVERSAL]);
  const parts = [...part(drawn, ".incident summary").children].map(
    (element) => element.className,
  );
  expect(parts).toStrictEqual([
    "when",
    "district",
    "kind",
    "trips",
    "milliamps",
    "cut",
  ]);
});

test("the rows are drawn in the order they are handed down", async () => {
  expect(all(await list([OUTAGE, REVERSAL]), ".incident .district")).toStrictEqual(
    ["station", "C"],
  );
});

test("the instant rides on the row, whatever the stamp is drawn as", async () => {
  // The time is the reader's own clock and the instant is the line's: nothing
  // about when something happened is lost to the formatting (`monitor.js`).
  const drawn = await list([REVERSAL]);
  expect(part(drawn, ".incident .when").getAttribute("datetime")).toBe(
    REVERSAL.at,
  );
});

test("a row opens on the journal lines it is made of", async () => {
  const drawn = await list([REVERSAL]);
  expect(all(drawn, ".incident .line .said")).toStrictEqual([
    "<* TRACK C INVERT (fast) *>",
    "<* TRACK C FAST OVERLOAD 4210mA. Pause 100ms *>",
  ]);
  expect(part(drawn, ".line .when").getAttribute("datetime")).toBe(
    REVERSAL.lines[0]?.at,
  );
});

test("the station's own incident is headed by its word and nothing else", async () => {
  const drawn = await list([OUTAGE]);
  expect(reads(drawn, ".incident .district")).toBe("station");
  expect(reads(drawn, ".incident .kind")).toBe("link");
  expect(all(drawn, ".incident .line .said")).toStrictEqual(["link down"]);
});

test("a routine row carries the station's words and none of the numbers", async () => {
  const drawn = await list([ROUTINE]);
  expect(part(drawn, ".incident").classList.contains("routine")).toBe(true);
  expect(reads(drawn, ".incident .says")).toBe("<p1 C>");
  expect(drawn.renderRoot.querySelector(".incident .kind")).toBeNull();
  expect(drawn.renderRoot.querySelector(".incident .trips")).toBeNull();
});

test("a list nobody has handed rows to draws none", async () => {
  expect(all(await list([]), ".incident")).toStrictEqual([]);
});

test("the list presses nothing but its own rows", async () => {
  // Opening a row is the browser's own `details`, and the controls are the
  // controls' (`ui/test/controls.test.ts`).
  const drawn = await list([OUTAGE, REVERSAL, ROUTINE]);
  expect(drawn.renderRoot.querySelectorAll("button")).toHaveLength(0);
  expect(drawn.renderRoot.querySelectorAll("details")).toHaveLength(3);
});
