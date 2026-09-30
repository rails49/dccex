/**
 * The **monitor**, mounted: a line the **decoder** knows and one it does not,
 * the page's own note among them, and the two controls pressed.
 *
 * Which lines carry a **gloss** and what each one says is the decoder's and is
 * run through it (`tests/ui/test_decoder.py`); what is asserted here is that
 * the sentence reaches the row it is about and that a line the decoder said
 * nothing about is drawn with nothing beside it. The absence is the page
 * saying it does not know (ADR-0009 d.2), and an absence is the thing a
 * source-text check is worst at: a template that drew an empty sentence and
 * one that drew none read the same off the source (#126).
 *
 * **And the controls are drawn as icons and pressed** (#144, #167). Which
 * shape each carries and the word it carries as a tooltip and as a label are
 * read back off the mounted button; the shape itself is `dccex-icon`'s
 * (`ui/test/icon.test.ts`). That the pause and the clear run
 * what they were handed, that the pause names what pressing it will do, and
 * what the count beside them reads were held against the source of this
 * component until here — which is the instrument #111 was filed to remove,
 * and is what let a resume that lost twelve lines and a pause that suppressed
 * the line it dropped both read correctly (#142, #143). What the presses do
 * to a conversation is the rules', run under a bare node
 * (`tests/ui/test_monitor.py`); this is a person's finger on the control.
 *
 * How loud the gloss is beside the bytes is the stylesheet's and stays there —
 * happy-dom does no layout and has no cascade to ask.
 */

import { mdiNotificationClearAll, mdiPause, mdiPlay } from "@mdi/js";
import { expect, test } from "vitest";

import { gloss } from "../src/decoder.js";
import { type Behind, type Line, type Shown } from "../src/monitor.js";
import { type DccexIcon } from "../src/ui/dccex-icon.js";
import { DccexMonitor } from "../src/ui/dccex-monitor.js";
import { all, mounted, part, press, reads } from "./mounted.js";

/** A line the decoder knows, and one it does not. */
const KNOWN = "<p1>";
const UNKNOWN = "<zzz>";

/** When they arrived, on the page's clock. */
const AT = new Date("2026-09-25T13:04:05.007Z");

/** The conversation as the page hands it down: the station said both lines,
 *  and each was keyed when it was kept. */
const SAID: Shown[] = [
  { line: KNOWN, at: AT, sent: false, key: 1 },
  { line: UNKNOWN, at: AT, sent: false, key: 2 },
];

/** The monitor, handed `said`. */
async function monitor(said: Shown[]): Promise<DccexMonitor> {
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

test("the page's own note is drawn as the page and not as the station", async () => {
  const drawn = await monitor([
    { note: "12 lines dropped while paused", key: 1 },
    { line: KNOWN, at: AT, sent: false, key: 2 },
  ]);
  expect(all(drawn, ".note")).toStrictEqual(["12 lines dropped while paused"]);
  expect(all(drawn, ".line")).toHaveLength(1);
  const note = part(drawn, ".note");
  expect(note.querySelector("time")).toBeNull();
  expect(note.querySelector(".mark")).toBeNull();
});

/** The monitor with the two controls handed to it, and a count of what they
 *  are holding back. */
async function controls(
  paused: boolean,
  behind: Behind<Line> = { lines: [], dropped: 0 },
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

/** What `selector` is drawn as: the word it carries both ways, and the path
 *  of the icon in it. */
function control(
  drawn: DccexMonitor,
  selector: string,
): { tooltip: string | null; label: string | null; path: string } {
  const pressed = part(drawn, selector);
  return {
    tooltip: pressed.getAttribute("title"),
    label: pressed.getAttribute("aria-label"),
    path: (part(drawn, `${selector} dccex-icon`) as DccexIcon).path,
  };
}

test("the pause names what pressing it will do, either way round", async () => {
  const { drawn: holding } = await controls(false);
  expect(control(holding, ".hold").label).toBe("pause");
  const { drawn: held } = await controls(true);
  expect(control(held, ".hold").label).toBe("resume");
  expect(control(held, ".empty").label).toBe("clear");
});

test("the pause is drawn as a pause, and as a play while it is holding", async () => {
  const { drawn: holding } = await controls(false);
  expect(control(holding, ".hold").path).toBe(mdiPause);
  const { drawn: held } = await controls(true);
  expect(control(held, ".hold").path).toBe(mdiPlay);
});

test("the clear is drawn as the lines going", async () => {
  const { drawn } = await controls(false);
  expect(control(drawn, ".empty").path).toBe(mdiNotificationClearAll);
});

test("each control carries its word as a tooltip and as a label", async () => {
  const { drawn } = await controls(false);
  for (const [selector, word] of [
    [".hold", "pause"],
    [".empty", "clear"],
  ] as const) {
    const carried = control(drawn, selector);
    expect(carried.tooltip).toBe(word);
    expect(carried.label).toBe(word);
  }
});

test("a control drawn as an icon says nothing in text", async () => {
  // The word is the tooltip's and the label's. A reader of the row reads a
  // shape, and a check that asked for the text would pass on a button with
  // both.
  const { drawn } = await controls(false);
  expect(reads(drawn, ".hold")).toBe("");
  expect(reads(drawn, ".empty")).toBe("");
});

test("the count says what is waiting and what the queue dropped", async () => {
  const waits: Line[] = Array.from({ length: 500 }, (_line, key) => ({
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
  expect(part(drawn, ".hold").getAttribute("aria-label")).toBe("pause");
});

test("the box says a command can be typed with or without its brackets", async () => {
  const drawn = await monitor([]);
  expect(part(drawn, ".typed").getAttribute("placeholder")).toBe("s or <s>");
});
