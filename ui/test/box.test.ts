/**
 * The box at the foot of the monitor, mounted: what it remembers of what was
 * sent, and how ↑, ↓, a tap on a sent line and an on-screen keyboard reach it.
 */

import { afterEach, beforeEach, expect, test } from "vitest";

import { message } from "../src/message.js";
import { type Shown } from "../src/monitor.js";
import { DccexMonitor } from "../src/ui/dccex-monitor.js";
import { mounted, part, press } from "./mounted.js";

const AT = new Date("2026-09-30T13:04:05.007Z");

/** A monitor that sends what `message.js` makes of the typing, as the page's
 *  does with a stream open. */
async function monitor(said: Shown[] = []): Promise<DccexMonitor> {
  const drawn = new DccexMonitor();
  drawn.said = said;
  drawn.sends = message;
  return await mounted(drawn);
}

function box(drawn: DccexMonitor): HTMLInputElement {
  return part(drawn, ".typed") as HTMLInputElement;
}

function step(drawn: DccexMonitor, selector: string): HTMLButtonElement {
  return part(drawn, selector) as HTMLButtonElement;
}

/** Type `typed` into the box and send it. */
async function send(drawn: DccexMonitor, typed: string): Promise<void> {
  box(drawn).value = typed;
  part(drawn, ".box").dispatchEvent(new Event("submit", { cancelable: true }));
  await drawn.updateComplete;
}

async function key(drawn: DccexMonitor, name: string): Promise<void> {
  box(drawn).dispatchEvent(
    new KeyboardEvent("keydown", { key: name, cancelable: true }),
  );
  await drawn.updateComplete;
}

beforeEach(() => {
  localStorage.clear();
});

test("↑ recalls what was sent, newest first, as it was sent", async () => {
  const drawn = await monitor();
  await send(drawn, "s");
  await send(drawn, "<1 JOIN>");
  await key(drawn, "ArrowUp");
  expect(box(drawn).value).toBe("<1 JOIN>");
  await key(drawn, "ArrowUp");
  expect(box(drawn).value).toBe("<s>");
  await key(drawn, "ArrowUp");
  expect(box(drawn).value).toBe("<s>");
});

test("↓ past the newest brings back what was being typed", async () => {
  const drawn = await monitor();
  await send(drawn, "s");
  box(drawn).value = "t 3";
  await key(drawn, "ArrowUp");
  expect(box(drawn).value).toBe("<s>");
  await key(drawn, "ArrowDown");
  expect(box(drawn).value).toBe("t 3");
});

test("the step buttons do what the keys do and are off at their ends", async () => {
  const drawn = await monitor();
  expect(step(drawn, ".older").disabled).toBe(true);
  expect(step(drawn, ".newer").disabled).toBe(true);
  await send(drawn, "s");
  expect(step(drawn, ".older").disabled).toBe(false);
  expect(step(drawn, ".newer").disabled).toBe(true);
  press(drawn, ".older");
  await drawn.updateComplete;
  expect(box(drawn).value).toBe("<s>");
  expect(step(drawn, ".older").disabled).toBe(true);
  expect(step(drawn, ".newer").disabled).toBe(false);
  press(drawn, ".newer");
  await drawn.updateComplete;
  expect(box(drawn).value).toBe("");
});

test("a press on a step button leaves focus in the box", async () => {
  const drawn = await monitor();
  const pressing = new MouseEvent("mousedown", { cancelable: true });
  part(drawn, ".older").dispatchEvent(pressing);
  expect(pressing.defaultPrevented).toBe(true);
});

test("a repeat of the last command is kept once", async () => {
  const drawn = await monitor();
  await send(drawn, "s");
  await send(drawn, "<s>");
  await key(drawn, "ArrowUp");
  await key(drawn, "ArrowUp");
  expect(box(drawn).value).toBe("<s>");
  expect(JSON.parse(localStorage.getItem("dccex.sent") ?? "")).toStrictEqual([
    "<s>",
  ]);
});

test("the last fifty are kept", async () => {
  const drawn = await monitor();
  for (let n = 0; n < 60; n++) {
    await send(drawn, `t ${n}`);
  }
  const kept = JSON.parse(localStorage.getItem("dccex.sent") ?? "") as string[];
  expect(kept).toHaveLength(50);
  expect(kept[0]).toBe("<t 10>");
  expect(kept.at(-1)).toBe("<t 59>");
});

test("what was not sent is not remembered", async () => {
  const drawn = await monitor();
  await send(drawn, "<>");
  expect(step(drawn, ".older").disabled).toBe(true);
});

test("a later visit on this device recalls what an earlier one sent", async () => {
  await send(await monitor(), "s");
  document.body.replaceChildren();
  const later = await monitor();
  await key(later, "ArrowUp");
  expect(box(later).value).toBe("<s>");
});

test("storage that cannot be read leaves the box with no history", async () => {
  localStorage.setItem("dccex.sent", "{not json");
  const drawn = await monitor();
  expect(step(drawn, ".older").disabled).toBe(true);
});

test("tapping a sent line puts it in the box and focuses it", async () => {
  const drawn = await monitor([
    { line: "<p1>", at: AT, sent: false, key: 1 },
    { line: "<s>", at: AT, sent: true, key: 2 },
  ]);
  press(drawn, ".line:not(.sent)");
  expect(box(drawn).value).toBe("");
  press(drawn, ".sent");
  expect(box(drawn).value).toBe("<s>");
  expect(drawn.shadowRoot?.activeElement).toBe(box(drawn));
});

/** The window's visual viewport, as a keyboard opening resizes it. */
let viewport: EventTarget;

/** `.lines` as a scroller of 1000 pixels with 100 showing, at `top`. */
function scrolled(drawn: DccexMonitor, top: number): HTMLElement {
  const lines = part(drawn, ".lines") as HTMLElement;
  Object.defineProperty(lines, "scrollHeight", { value: 1000 });
  Object.defineProperty(lines, "clientHeight", { value: 100 });
  lines.scrollTop = top;
  return lines;
}

beforeEach(() => {
  viewport = new EventTarget();
  Object.defineProperty(window, "visualViewport", {
    value: viewport,
    configurable: true,
  });
});

afterEach(() => {
  Reflect.deleteProperty(window, "visualViewport");
});

test("a reader at the bottom stays on the newest line as the keyboard opens", async () => {
  const drawn = await monitor();
  const lines = scrolled(drawn, 900);
  box(drawn).focus();
  lines.scrollTop = 400;
  viewport.dispatchEvent(new Event("resize"));
  await drawn.updateComplete;
  expect(lines.scrollTop).toBe(1000);
});

test("a reader who scrolled up is not moved as the keyboard opens", async () => {
  const drawn = await monitor();
  const lines = scrolled(drawn, 200);
  box(drawn).focus();
  viewport.dispatchEvent(new Event("resize"));
  await drawn.updateComplete;
  expect(lines.scrollTop).toBe(200);
});
