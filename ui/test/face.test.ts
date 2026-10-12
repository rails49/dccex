/**
 * The two asks about the **journal**, driven against a face with nothing
 * behind it.
 *
 * What the page makes of the file is the reading module's and is run through it
 * (`tests/ui/test_incidents.py`); what is asserted here is the asking — the
 * address, the method, the bytes counted as bytes, and what a face that said
 * nothing comes back as, none of which a Python gate with no browser can reach
 * (ADR-0022 d.4, `ui/src/face.ts`).
 *
 * The journal is the one thing on the face whose body is not JSON, which is
 * the half a check that stubbed `json()` would walk past: the file is
 * `application/x-ndjson` and the size on the view is the length of what came
 * back (#264).
 */

import { afterEach, expect, test } from "vitest";

import { JOURNAL_PATH, clears, journal } from "../src/face.js";
import { UNANSWERED } from "../src/incidents.js";

/** One ask the page made, as it made it. */
interface Asked {
  readonly url: string;
  readonly method: string;
}

/** Every ask, and what the face is answering with. A list rather than the last
 *  one, because the page asking twice is a defect a check should be able to
 *  name. */
const asked: Asked[] = [];

/** The face, answering `answers` to whatever is asked of it. */
function answering(answers: () => Response): void {
  globalThis.fetch = (
    resource: RequestInfo | URL,
    asks?: RequestInit,
  ): Promise<Response> => {
    asked.push({
      url: String(resource),
      method: asks?.method ?? "GET",
    });
    return Promise.resolve(answers());
  };
}

/** A face that is away: nothing to ask, and a rejection where the page asks. */
function away(): void {
  globalThis.fetch = (): Promise<Response> =>
    Promise.reject(new Error("there is no face here"));
}

/** One journal, as the translator wrote it and the face serves it. */
const SERVED =
  '{"at":"2026-10-12T18:00:00.000+00:00","build":"g1","said":"<p1 A>",' +
  '"district":"A","mode":"MAIN","limit":3000}\n';

afterEach(() => {
  asked.length = 0;
});

test("the journal is read off the face's own address", async () => {
  answering(() => new Response(SERVED, { status: 200 }));
  const served = await journal();
  expect(asked).toStrictEqual([{ url: JOURNAL_PATH, method: "GET" }]);
  expect(served?.lines).toHaveLength(1);
  expect(served?.lines[0]?.district).toBe("A");
});

test("the size is the length of the bytes that came back", async () => {
  answering(() => new Response(SERVED, { status: 200 }));
  expect((await journal())?.bytes).toBe(SERVED.length);
});

test("a journal with nothing in it is no lines and no bytes", async () => {
  // The face answers an empty body where the file is not there and where it is
  // empty, which is a railroad that has said nothing about power rather than a
  // page that was not told (#264).
  answering(() => new Response("", { status: 200 }));
  expect(await journal()).toStrictEqual({ lines: [], bytes: 0 });
});

test("a face that would not serve it says nothing rather than nothing in it", async () => {
  answering(() => new Response('{"reason":"no journal"}', { status: 503 }));
  expect(await journal()).toBeNull();
  away();
  expect(await journal()).toBeNull();
});

test("the journal is emptied with a DELETE of the same address", async () => {
  answering(() => new Response('{"cleared":1500}', { status: 200 }));
  expect(await clears()).toStrictEqual({
    cleared: true,
    says: "the journal is empty: 1.5 kB cleared",
  });
  expect(asked).toStrictEqual([{ url: JOURNAL_PATH, method: "DELETE" }]);
});

test("a refusal is the face's own sentence", async () => {
  const reason = "this mirror was given no journal";
  answering(() => new Response(JSON.stringify({ reason }), { status: 503 }));
  expect(await clears()).toStrictEqual({ cleared: false, says: reason });
});

test("a face that said nothing about a clear is said to have said nothing", async () => {
  // Nothing said is not nothing cleared: what the page says is its own
  // sentence, and only where there was no answer to read (ADR-0009 d.2).
  answering(() => new Response("not json", { status: 200 }));
  expect(await clears()).toStrictEqual({ cleared: false, says: UNANSWERED });
  away();
  expect(await clears()).toStrictEqual({ cleared: false, says: UNANSWERED });
});
