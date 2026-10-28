/**
 * The **journal** view, mounted: what it asks for, when it asks, and what it
 * hands the three components under it.
 *
 * The reading is the module's and is run through it
 * (`tests/ui/test_incidents.py`); what is asserted here is the pane — that
 * opening it asks the **face** once, that the reload asks again, that a period
 * and the toggle change what is counted without asking anything.
 *
 * The ask is the one the page hands down, and nothing here fetches: a
 * pane holding its own counterparty would be a second answer to what the page
 * talks to (the organisation's ADR-0002, `dccex-app.ts`).
 */

import { expect, test } from "vitest";

import { EMPTY, UNREADABLE, type Served, when } from "../src/incidents.js";
import { type DccexControls } from "../src/ui/dccex-controls.js";
import { type DccexCounts } from "../src/ui/dccex-counts.js";
import { type DccexIncidents } from "../src/ui/dccex-incidents.js";
import { DccexJournal } from "../src/ui/dccex-journal.js";
import { all, mounted, part, press, reads } from "./mounted.js";

/** One journal: a district powered on, a flip, the short it did not clear,
 *  the district itself again, and the link going and coming back. */
const JOURNAL: Served = {
  bytes: 640,
  lines: [
    {
      at: "2026-10-12T18:00:00.000+00:00",
      build: "g1",
      said: "<p1 C>",
      district: "C",
      mode: "MAIN_AUTO",
      limit: 3000,
    },
    {
      at: "2026-10-12T18:00:01.000+00:00",
      build: "g1",
      said: "<* TRACK C INVERT (fast) *>",
      district: "C",
      mode: "MAIN_AUTO",
      limit: 3000,
    },
    {
      at: "2026-10-12T18:00:01.100+00:00",
      build: "g1",
      said: "<* TRACK C FAST OVERLOAD 4210mA. Pause 100ms *>",
      district: "C",
      mode: "MAIN_AUTO",
      limit: 3000,
    },
    {
      at: "2026-10-12T18:00:01.300+00:00",
      build: "g1",
      said: "<* TRACK C NORMAL (after 20ms/40ms) 180mA *>",
      district: "C",
      mode: "MAIN_AUTO",
      limit: 3000,
    },
    { at: "2026-10-12T18:00:05.000+00:00", build: "", link: "down" },
    { at: "2026-10-12T18:00:09.000+00:00", build: "g2", link: "up" },
  ],
};

/** The view, and what it asked the face for. `serves` answers the read, so a
 *  check can say what the file was at each ask. */
async function view(
  serves: () => Served | null = () => JOURNAL,
): Promise<{ drawn: DccexJournal; read: number }> {
  let read = 0;
  const drawn = new DccexJournal();
  drawn.reads = () => {
    read += 1;
    return Promise.resolve(serves());
  };
  await mounted(drawn);
  // The pane asks where it joins the document, which is one turn of the loop
  // before the answer is on the page.
  await drawn.updateComplete;
  await drawn.updateComplete;
  return {
    drawn,
    get read(): number {
      return read;
    },
  };
}

/** The list under the view, and the table above it. */
function list(drawn: DccexJournal): DccexIncidents {
  return part(drawn, "dccex-incidents") as DccexIncidents;
}

function table(drawn: DccexJournal): DccexCounts {
  return part(drawn, "dccex-counts") as DccexCounts;
}

/** The controls above both of them, which is what a reader presses. */
function controls(drawn: DccexJournal): DccexControls {
  return part(drawn, "dccex-controls") as DccexControls;
}

test("opening the view asks the face for the journal, once", async () => {
  const opened = await view();
  expect(opened.read).toBe(1);
  expect(all(list(opened.drawn), ".incident .kind")).toStrictEqual([
    "link",
    "reversal",
  ]);
});

test("the counts are drawn above the incidents, off the same reading", async () => {
  const opened = await view();
  expect(all(table(opened.drawn), "tr.district .name")).toStrictEqual(["C"]);
  expect(reads(table(opened.drawn), "tr.station .links")).toBe("1 link loss");
});

test("the reload asks the face again, and draws what it answers", async () => {
  let served: Served | null = JOURNAL;
  const opened = await view(() => served);
  served = { bytes: 0, lines: [] };
  press(controls(opened.drawn), ".reloads");
  await opened.drawn.updateComplete;
  await opened.drawn.updateComplete;
  expect(opened.read).toBe(2);
  expect(reads(opened.drawn, ".empty")).toBe(EMPTY);
});

test("a journal with nothing in it says so and draws no table", async () => {
  const opened = await view(() => ({ bytes: 0, lines: [] }));
  expect(reads(opened.drawn, ".empty")).toBe(EMPTY);
  expect(opened.drawn.renderRoot.querySelector("dccex-counts")).toBeNull();
  expect(opened.drawn.renderRoot.querySelector("dccex-incidents")).toBeNull();
});

test("a journal the face would not serve is a different sentence", async () => {
  // Nothing said is not nothing in it: a table of zeros for a file nobody read
  // would be a count nobody made (ADR-0009 d.2).
  const opened = await view(() => null);
  expect(reads(opened.drawn, ".empty")).toBe(UNREADABLE);
  expect(opened.drawn.renderRoot.querySelector("dccex-counts")).toBeNull();
});

test("the period and the toggle change what is counted and ask nothing", async () => {
  const opened = await view();
  opened.drawn.routine = true;
  await opened.drawn.updateComplete;
  expect(all(list(opened.drawn), ".incident.routine .says")).toStrictEqual([
    "<p1 C>",
  ]);
  opened.drawn.choice = "g2";
  await opened.drawn.updateComplete;
  expect(all(list(opened.drawn), ".incident")).toHaveLength(1);
  expect(opened.read).toBe(1);
});

test("the periods on offer are the spans, the builds and the days in the file", async () => {
  const opened = await view();
  expect([...controls(opened.drawn).choices]).toStrictEqual([
    "all",
    "last day",
    "last 7 days",
    "g2",
    "g1",
    // The day on the clock of the machine running this (#370).
    when("2026-10-12T18:00:00.000+00:00").slice(0, 10),
  ]);
  expect(controls(opened.drawn).bytes).toBe(JOURNAL.bytes);
});

test("a pane nobody handed the ask to says the journal could not be read", async () => {
  const drawn = await mounted(new DccexJournal());
  await drawn.updateComplete;
  expect(reads(drawn, ".empty")).toBe(UNREADABLE);
});
