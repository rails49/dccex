/**
 * The translator's **log** beside the script view's editor (#365): what the
 * page makes of each answer (`log.ts`), the ask (`face.ts`'s `log()`), and the
 * pane that times the asking (`dccex-log.ts`).
 *
 * The face is stubbed at `fetch` for the ask, and the pane is handed a hand
 * that records the byte it asked from and answers what a check says. Time is
 * vitest's, so a second is a step a check takes.
 */

import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { LOG_PATH, log } from "../src/face.js";
import { type Logged, Tail } from "../src/log.js";
import { DccexLog, EVERY } from "../src/ui/dccex-log.js";
import { mounted, reads } from "./mounted.js";

/** `text` as the face serves it, from byte `from`. */
function bytes(text: string, from = 0): Logged {
  return { from, bytes: new TextEncoder().encode(text) };
}

/** The face's sentence for a mirror started without `--log`. */
const NO_LOG =
  "this mirror was given no log, so it cannot serve one: the path is --log" +
  " on its command line";

test("a log read whole and then in parts is the parts in order", () => {
  const tail = new Tail();
  expect(tail.took(bytes("one\n"))).toBe(false);
  expect(tail.took(bytes("two\n", 4))).toBe(false);
  expect(tail.parts.join("")).toBe("one\ntwo\n");
  expect(tail.at).toBe(8);
});

test("nothing new adds no part", () => {
  const tail = new Tail();
  tail.took(bytes("one\n"));
  tail.took(bytes("", 4));
  expect(tail.parts).toStrictEqual(["one\n"]);
});

test("a character split across two answers is read whole", () => {
  const tail = new Tail();
  const encoded = new TextEncoder().encode("Zürich\n");
  tail.took({ from: 0, bytes: encoded.slice(0, 2) });
  tail.took({ from: 2, bytes: encoded.slice(2) });
  expect(tail.parts.join("")).toBe("Zürich\n");
  expect(tail.at).toBe(encoded.byteLength);
});

test("a trimmed log is emptied and asked for again at once, whole", () => {
  const tail = new Tail();
  tail.took(bytes("one\ntwo\n"));
  expect(tail.took({ trimmed: true })).toBe(true);
  expect(tail.at).toBe(0);
  expect(tail.parts).toStrictEqual([]);
  tail.took(bytes("two\n"));
  expect(tail.parts.join("")).toBe("two\n");
});

test("a part that does not follow on is dropped, and the file asked for whole", () => {
  const tail = new Tail();
  tail.took(bytes("one\n"));
  expect(tail.took(bytes("two\n", 9))).toBe(false);
  expect(tail.parts).toStrictEqual([]);
  expect(tail.at).toBe(0);
});

test("a whole file where a part was asked for replaces what was held", () => {
  const tail = new Tail();
  tail.took(bytes("one\n"));
  tail.took(bytes("again\n"));
  expect(tail.parts.join("")).toBe("again\n");
  expect(tail.at).toBe(6);
});

test("the face's sentence is held as it came, and lines replace it", () => {
  const tail = new Tail();
  tail.took({ says: NO_LOG });
  expect(tail.says).toBe(NO_LOG);
  tail.took(bytes("one\n"));
  expect(tail.says).toBe("");
});

test("no answer changes nothing", () => {
  const tail = new Tail();
  tail.took(bytes("one\n"));
  expect(tail.took(null)).toBe(false);
  expect(tail.parts.join("")).toBe("one\n");
  expect(tail.at).toBe(4);
});

/** What the page asked the face, and what the face answers. */
const fetched: { url: string; range: string | null }[] = [];

function answering(answers: () => Response): void {
  globalThis.fetch = (
    resource: RequestInfo | URL,
    asks?: RequestInit,
  ): Promise<Response> => {
    fetched.push({
      url: String(resource),
      range: new Headers(asks?.headers).get("range"),
    });
    return Promise.resolve(answers());
  };
}

afterEach(() => {
  fetched.length = 0;
});

test("the log is asked for from a byte on, at the face's own address", async () => {
  answering(
    () =>
      new Response("two\n", {
        status: 206,
        headers: { "content-range": "bytes 4-7/8" },
      }),
  );
  const logged = await log(4);
  expect(fetched).toStrictEqual([{ url: LOG_PATH, range: "bytes=4-" }]);
  expect(logged).toStrictEqual(bytes("two\n", 4));
});

test("a whole file is from byte 0", async () => {
  answering(() => new Response("one\n", { status: 200 }));
  expect(await log(9)).toStrictEqual(bytes("one\n"));
});

test("a 416 is a trimmed log", async () => {
  answering(() => new Response('{"reason":"past the end"}', { status: 416 }));
  expect(await log(9)).toStrictEqual({ trimmed: true });
});

test("a mirror with no log is the face's sentence", async () => {
  answering(
    () =>
      new Response(JSON.stringify({ reason: NO_LOG }), {
        status: 503,
      }),
  );
  expect(await log(0)).toStrictEqual({ says: NO_LOG });
});

test("a face that is away is no answer", async () => {
  globalThis.fetch = (): Promise<Response> =>
    Promise.reject(new Error("there is no face here"));
  expect(await log(0)).toBeNull();
  answering(() => new Response("", { status: 502 }));
  expect(await log(0)).toBeNull();
});

/** A pane handed a hand that answers from `answers`, in order, and records
 *  the byte each ask started at. The last answer repeats. */
async function pane(
  answers: Logged[],
  showing = true,
): Promise<[DccexLog, number[]]> {
  const asked: number[] = [];
  const drawn = new DccexLog();
  drawn.showing = showing;
  drawn.reads = (from: number): Promise<Logged> => {
    asked.push(from);
    return Promise.resolve(answers[Math.min(asked.length, answers.length) - 1]);
  };
  await mounted(drawn);
  await vi.advanceTimersByTimeAsync(0);
  await drawn.updateComplete;
  return [drawn, asked];
}

/** A second goes by, and the pane draws what it was answered. */
async function second(drawn: DccexLog): Promise<void> {
  await vi.advanceTimersByTimeAsync(EVERY);
  await drawn.updateComplete;
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

test("the pane asks about once a second, from where it got to", async () => {
  const [drawn, asked] = await pane([
    bytes("one\n"),
    bytes("two\n", 4),
    bytes("", 8),
  ]);
  expect(reads(drawn, ".log")).toBe("one");
  await second(drawn);
  expect(asked).toStrictEqual([0, 4]);
  expect(drawn.tail.parts.join("")).toBe("one\ntwo\n");
  await second(drawn);
  expect(asked).toStrictEqual([0, 4, 8]);
});

test("a trimmed log is read whole again at once", async () => {
  const [drawn, asked] = await pane([
    bytes("one\n"),
    { trimmed: true },
    bytes("two\n"),
    bytes("", 4),
  ]);
  await second(drawn);
  expect(asked).toStrictEqual([0, 4, 0]);
  expect(drawn.tail.parts.join("")).toBe("two\n");
});

test("a mirror with no log shows the face's sentence in the pane", async () => {
  const [drawn] = await pane([{ says: NO_LOG }]);
  expect(reads(drawn, ".log")).toBe(NO_LOG);
});

test("a pane that is not showing asks nothing", async () => {
  const [drawn, asked] = await pane([bytes("one\n")], false);
  await second(drawn);
  expect(asked).toStrictEqual([]);
});

test("asking stops when the pane stops showing, and starts again", async () => {
  const [drawn, asked] = await pane([bytes("one\n"), bytes("", 4)]);
  drawn.showing = false;
  await drawn.updateComplete;
  await second(drawn);
  await second(drawn);
  expect(asked).toStrictEqual([0]);
  drawn.showing = true;
  await drawn.updateComplete;
  await vi.advanceTimersByTimeAsync(0);
  expect(asked).toStrictEqual([0, 4]);
});

test("asking stops when the pane is taken away", async () => {
  const [drawn, asked] = await pane([bytes("one\n"), bytes("", 4)]);
  drawn.remove();
  await second(drawn);
  expect(asked).toStrictEqual([0]);
});

/** The pane's scroller, made to report `height` of text in `shown` of room,
 *  scrolled to `top`. happy-dom lays nothing out, so the three are set. */
function scrolled(
  drawn: DccexLog,
  height: number,
  shown: number,
  top: number,
): HTMLElement {
  const scroller = drawn.renderRoot.querySelector(".log") as HTMLElement;
  Object.defineProperty(scroller, "scrollHeight", {
    configurable: true,
    value: height,
  });
  Object.defineProperty(scroller, "clientHeight", {
    configurable: true,
    value: shown,
  });
  scroller.scrollTop = top;
  scroller.dispatchEvent(new Event("scroll"));
  return scroller;
}

test("the pane follows the bottom unless the reader scrolled up", async () => {
  const [drawn] = await pane([bytes("one\n"), bytes("two\n", 4), bytes("", 8)]);
  const scroller = scrolled(drawn, 1000, 100, 200);
  await second(drawn);
  expect(scroller.scrollTop).toBe(200);
  scrolled(drawn, 1000, 100, 900);
  Object.defineProperty(scroller, "scrollHeight", {
    configurable: true,
    value: 1200,
  });
  drawn.requestUpdate();
  await drawn.updateComplete;
  expect(scroller.scrollTop).toBe(1200);
});
