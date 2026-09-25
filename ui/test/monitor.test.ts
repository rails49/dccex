/**
 * The **monitor**, mounted, with a line the **decoder** knows and one it does
 * not.
 *
 * Which lines carry a **gloss** and what each one says is the decoder's and is
 * run through it (`tests/ui/test_decoder.py`); what is asserted here is that
 * the sentence reaches the row it is about and that a line the decoder said
 * nothing about is drawn with nothing beside it. The absence is the page
 * saying it does not know (ADR-0009 d.2), and an absence is the thing a
 * source-text check is worst at: a template that drew an empty sentence and
 * one that drew none read the same off the source (#126).
 *
 * How loud the gloss is beside the bytes is the stylesheet's and stays there —
 * happy-dom does no layout and has no cascade to ask.
 */

import { expect, test } from "vitest";

import { gloss } from "../src/decoder.js";
import { DccexMonitor, type Keyed } from "../src/ui/dccex-monitor.js";
import { all, mounted, part, reads } from "./mounted.js";

/** A line the decoder knows, and one it does not. */
const KNOWN = "<p1>";
const UNKNOWN = "<zzz>";

/** When they arrived, on the page's clock. */
const AT = new Date("2026-09-25T13:04:05.007Z");

/** The conversation as the page hands it down: the station said both lines,
 *  and each was keyed when it was kept. */
const SAID: Keyed[] = [
  { line: KNOWN, at: AT, sent: false, key: 1 },
  { line: UNKNOWN, at: AT, sent: false, key: 2 },
];

/** The monitor, handed `said`. */
async function monitor(said: Keyed[]): Promise<DccexMonitor> {
  const drawn = new DccexMonitor();
  drawn.said = said;
  return await mounted(drawn);
}

test("a line the decoder knows carries its sentence beside the bytes", async () => {
  const drawn = await monitor(SAID);
  const row = part(drawn, ".line");
  expect(row.querySelector(".said")?.textContent).toBe(KNOWN);
  expect(row.querySelector(".gloss")?.textContent).toBe(gloss(KNOWN));
});

test("a line the decoder does not know is drawn raw with nothing beside it", async () => {
  const drawn = await monitor(SAID);
  const row = all(drawn, ".line");
  expect(row).toHaveLength(2);
  const raw = [...drawn.renderRoot.querySelectorAll(".line")][1];
  expect(raw?.querySelector(".said")?.textContent).toBe(UNKNOWN);
  expect(raw?.querySelector(".gloss")).toBeNull();
});

test("the gloss column is empty and not blank for a line with no reading", async () => {
  const drawn = await monitor(SAID);
  expect(all(drawn, ".gloss")).toStrictEqual([gloss(KNOWN)]);
});

test("every line carries the time it arrived, to the millisecond", async () => {
  const drawn = await monitor(SAID);
  const stamps = [...drawn.renderRoot.querySelectorAll("time")];
  expect(stamps).toHaveLength(2);
  for (const stamp of stamps) {
    expect(stamp.getAttribute("datetime")).toBe(AT.toISOString());
    expect(stamp.textContent).toMatch(/^\d{2}:\d{2}:\d{2}\.\d{3}$/);
  }
});

test("a line this page sent is marked where the station's lines are not", async () => {
  const drawn = await monitor([
    { line: KNOWN, at: AT, sent: false, key: 1 },
    { line: "<s>", at: AT, sent: true, key: 2 },
  ]);
  const rows = [...drawn.renderRoot.querySelectorAll(".line")];
  expect(rows[0]?.classList).not.toContain("sent");
  expect(rows[0]?.querySelector(".mark")?.textContent).toBe("");
  expect(rows[1]?.classList).toContain("sent");
  expect(rows[1]?.querySelector(".mark")?.textContent).not.toBe("");
});

test("a conversation nothing has been said in says so", async () => {
  const drawn = await monitor([]);
  expect(all(drawn, ".line")).toStrictEqual([]);
  expect(reads(drawn, ".quiet")).toBe("nothing said yet");
});
