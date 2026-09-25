/**
 * The **monitor**, mounted: a line the **decoder** knows, one it does not, and
 * the two controls pressed.
 *
 * Which lines carry a **gloss** and what each one says is the decoder's and is
 * run through it (`tests/ui/test_decoder.py`); what is asserted here is that
 * the sentence reaches the row it is about and that a line the decoder said
 * nothing about is drawn with nothing beside it. The absence is the page
 * saying it does not know (ADR-0009 d.2), and an absence is the thing a
 * source-text check is worst at: a template that drew an empty sentence and
 * one that drew none read the same off the source (#126).
 *
 * **And the controls are pressed** (#144). That the pause and the clear run
 * what they were handed, that the pause names what pressing it will do, and
 * what the count beside them reads were held against the source of this
 * component until here — which is the instrument #111 was filed to remove and
 * #126 retired for everything else a component draws. What a press does to a
 * conversation is the page's and is held where that is
 * (`tests/ui/test_monitor.py`); this is a person's finger on the control.
 *
 * How loud the gloss is beside the bytes is the stylesheet's and stays there —
 * happy-dom does no layout and has no cascade to ask.
 */

import { expect, test } from "vitest";

import { gloss } from "../src/decoder.js";
import { type Behind } from "../src/monitor.js";
import { DccexMonitor, type Keyed } from "../src/ui/dccex-monitor.js";
import { all, mounted, part, press, reads } from "./mounted.js";

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

/** The monitor with the two controls handed to it, and a count of what they
 *  are holding back. */
async function controls(
  paused: boolean,
  behind: Behind<Keyed> = { lines: [], dropped: 0 },
): Promise<{ drawn: DccexMonitor; pressed: string[] }> {
  const pressed: string[] = [];
  const drawn = new DccexMonitor();
  drawn.said = SAID;
  drawn.paused = paused;
  drawn.behind = behind;
  drawn.pauses = (): void => {
    pressed.push("pauses");
  };
  drawn.clears = (): void => {
    pressed.push("clears");
  };
  return { drawn: await mounted(drawn), pressed };
}

test("pressing the pause runs what the page handed it", async () => {
  const { drawn, pressed } = await controls(false);
  press(drawn, ".hold");
  expect(pressed).toStrictEqual(["pauses"]);
});

test("pressing the clear runs what the page handed it", async () => {
  const { drawn, pressed } = await controls(false);
  press(drawn, ".empty");
  expect(pressed).toStrictEqual(["clears"]);
});

test("the pause names what pressing it will do, either way round", async () => {
  const { drawn: holding } = await controls(false);
  expect(reads(holding, ".hold")).toBe("pause");
  const { drawn: held } = await controls(true);
  expect(reads(held, ".hold")).toBe("resume");
  expect(reads(held, ".empty")).toBe("clear");
});

test("the count says what is waiting and what the queue dropped", async () => {
  const waits: Keyed[] = Array.from({ length: 500 }, (_line, key) => ({
    line: KNOWN,
    at: AT,
    sent: false,
    key,
  }));
  const { drawn } = await controls(true, { lines: waits, dropped: 12 });
  expect(reads(drawn, ".waiting")).toBe("500 waiting, 12 dropped");
});

test("a monitor with nothing waiting carries no count at all", async () => {
  const { drawn } = await controls(false);
  expect(reads(drawn, ".waiting")).toBeNull();
});

test("a monitor nobody handed the controls to does nothing when pressed", async () => {
  const drawn = await monitor(SAID);
  press(drawn, ".hold");
  press(drawn, ".empty");
  expect(all(drawn, ".line")).toHaveLength(2);
  expect(reads(drawn, ".hold")).toBe("pause");
});
