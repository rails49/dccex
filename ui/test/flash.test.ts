/**
 * A flash, pressed on a mounted row, with its steps read off the page in the
 * order they are shown.
 *
 * What goes down the cable and in what order is the sequence's and is run
 * through it (`tests/ui/test_flash.py`); what is asserted here is the gesture
 * an operator makes and the sentences they read while the station is away.
 * That is the one of the five #1 named that no source-text check ever reached:
 * a press, a warning that opens under the release it is about, a second press,
 * and three steps in the order they are drawn (#126).
 *
 * **And the bar is read off the page the same way.** How far a flash has got is
 * the page's poll of the face handed down (`dccex-app.ts`), so what is asserted
 * here is what a `flashing` on the row draws: one bar, what it reads, and
 * whether it counts (ADR-0012 d.3).
 *
 * **Why the steps are drawn now rather than awaited.** `flash.js` says its
 * first two steps and sends the two messages between them without awaiting
 * anything, so Lit's one drawing per turn would show the last of the three and
 * never the two before it. `drawnNow` is what makes each of them a thing on
 * the page to read (`ui/test/mounted.ts`). Nothing about the sequence is
 * changed by it — the order is the order it asked for them in.
 */

import { expect, test } from "vitest";

import {
  CANCELS,
  CUTS,
  CUTTING,
  STOPPING,
  STOPS,
  WAITING,
  WARNS,
  type Flashing,
  type Wrote,
  instead,
  running,
  writing,
} from "../src/flash.js";
import { type Carried } from "../src/releases.js";
import { DccexReleases } from "../src/ui/dccex-releases.js";
import { all, drawnNow, mounted, part, press, reads } from "./mounted.js";

/** The release the operator chooses, and one there is nothing to write from
 *  beside it. */
const CHOSEN = "v5.2.76";
const CARRIED: Carried[] = [
  { tag: CHOSEN, published: "2026-08-03T09:00:00Z", flashable: true },
  { tag: "v5.2.75", published: "2026-07-02T09:00:00Z", flashable: false },
];

/** What a flash the mirror wrote comes back as: the write is over and the
 *  station has not said what it is running yet (ADR-0012 d.4). */
const WRITTEN: Wrote = { flashed: true, says: WAITING };

/** What the row asked for, and what it was showing when it asked.
 *
 *  Both are recorded at the moment of the ask rather than afterwards: the
 *  sentence a step is shown in is only on the page while that step is
 *  running. */
interface Asked {
  readonly typed: string[];
  readonly steps: (string | null)[];
  readonly pressable: boolean[];
}

/** A row mounted with somewhere for its stop, its cut and its write to go. */
async function flashing(): Promise<[DccexReleases, Asked]> {
  const typed: string[] = [];
  const steps: (string | null)[] = [];
  const pressable: boolean[] = [];
  const drawn = new DccexReleases();
  drawn.carried = CARRIED;
  drawn.build = null;
  const noted = (): void => {
    drawnNow(drawn);
    steps.push(reads(drawn, ".step"));
    pressable.push(!(part(drawn, ".chooses") as HTMLButtonElement).disabled);
  };
  drawn.sends = (message: string): string => {
    noted();
    typed.push(message);
    return message;
  };
  drawn.writes = async (tag: string): Promise<Wrote> => {
    noted();
    typed.push(`write ${tag}`);
    return await Promise.resolve(WRITTEN);
  };
  return [await mounted(drawn), { typed, steps, pressable }];
}

/** How far a flash the mirror is running has got, as the page's poll answers
 *  it. */
function got(stage: string, percent: number | null): Flashing {
  return { tag: CHOSEN, stage, percent };
}

/** What the one bar the row drew says its value is. */
function counts(drawn: DccexReleases): string | null {
  return (part(drawn, ".bar") as HTMLProgressElement).getAttribute("value");
}

/** Everything the press set going, finished and drawn. */
async function settled(drawn: DccexReleases): Promise<void> {
  await new Promise((done) => setTimeout(done, 0));
  await drawn.updateComplete;
}

test("choosing a release opens the warning under that release", async () => {
  const [drawn] = await flashing();
  expect(all(drawn, ".warning")).toStrictEqual([]);
  press(drawn, ".chooses");
  await drawn.updateComplete;
  const opened = part(drawn, ".release");
  expect(opened.querySelector(".tag")?.textContent).toBe(CHOSEN);
  expect(opened.querySelector(".warns")?.textContent).toBe(WARNS);
  expect(opened.querySelector(".warns")?.getAttribute("role")).toBe("alert");
});

test("the warning is read before the press that agrees to it", async () => {
  const [drawn] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  const warning = part(drawn, ".warning");
  const said = [...warning.children].map((drew) => drew.className);
  expect(said).toStrictEqual(["warns", "confirms", "cancels"]);
});

test("declining leaves the station untouched and says nothing about it", async () => {
  const [drawn, asked] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".cancels");
  await settled(drawn);
  expect(all(drawn, ".warning")).toStrictEqual([]);
  expect(all(drawn, ".became")).toStrictEqual([]);
  expect(asked.typed).toStrictEqual([]);
});

test("the steps are shown in the order the sequence runs them", async () => {
  const [drawn, asked] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await settled(drawn);
  expect(asked.steps).toStrictEqual([STOPPING, CUTTING, writing(CHOSEN)]);
  expect(asked.typed).toStrictEqual([STOPS, CUTS, `write ${CHOSEN}`]);
});

test("nothing is pressable while a step is showing", async () => {
  const [drawn, asked] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await settled(drawn);
  expect(asked.pressable).toStrictEqual([false, false, false]);
  expect((part(drawn, ".chooses") as HTMLButtonElement).disabled).toBe(false);
});

test("the step goes when the flash is over and what became of it is drawn", async () => {
  const [drawn] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await settled(drawn);
  expect(all(drawn, ".step")).toStrictEqual([]);
  expect(reads(drawn, ".became.waiting")).toBe(WAITING);
});

test("the step is drawn outside the row, which can be shut while it runs", async () => {
  const [drawn, asked] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  drawn.writes = async (): Promise<Wrote> => {
    drawnNow(drawn);
    expect(part(drawn, ".step").closest("details")).toBeNull();
    asked.typed.push("looked");
    return await Promise.resolve(WRITTEN);
  };
  press(drawn, ".confirms");
  await settled(drawn);
  expect(asked.typed).toContain("looked");
});

test("a release with nothing to write from has nothing to press", async () => {
  const [drawn] = await flashing();
  expect(all(drawn, ".chooses")).toHaveLength(1);
  expect(all(drawn, ".bare")).toHaveLength(1);
});

test("a flash that was declined and then made reads the same as any other", async () => {
  const [drawn] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".cancels");
  await drawn.updateComplete;
  press(drawn, ".chooses");
  await drawn.updateComplete;
  expect(reads(drawn, ".warns")).toBe(WARNS);
  expect(reads(drawn, ".cancels")).toBe(CANCELS);
});

test("a flash in flight draws one bar, with the stage beside it", async () => {
  const [drawn] = await flashing();
  drawn.flashing = got("writing", 42);
  await drawn.updateComplete;
  expect(all(drawn, ".bar")).toHaveLength(1);
  expect(reads(drawn, ".stage")).toBe("writing 42 %");
  expect(counts(drawn)).toBe("42");
});

test("the stages nothing counts draw an empty or a full bar", async () => {
  const [drawn] = await flashing();
  for (const [stage, value] of [
    ["fetching", "0"],
    ["checking", "0"],
    ["verifying", "100"],
  ]) {
    drawn.flashing = got("writing", 42);
    await drawn.updateComplete;
    drawn.flashing = got(stage, null);
    await drawn.updateComplete;
    expect(reads(drawn, ".stage")).toBe(stage);
    expect(counts(drawn)).toBe(value);
  }
});

test("no flash in flight draws no bar", async () => {
  const [drawn] = await flashing();
  expect(all(drawn, ".bar")).toStrictEqual([]);
  drawn.flashing = got("writing", 42);
  await drawn.updateComplete;
  drawn.flashing = null;
  await drawn.updateComplete;
  expect(all(drawn, ".bar")).toStrictEqual([]);
});

test("a flash somebody else started takes the press away", async () => {
  const [drawn] = await flashing();
  drawn.flashing = got("writing", 42);
  await drawn.updateComplete;
  expect((part(drawn, ".chooses") as HTMLButtonElement).disabled).toBe(true);
});

test("a warning left open when somebody else starts a flash cannot be agreed to", async () => {
  const [drawn, asked] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  drawn.flashing = got("writing", 42);
  await drawn.updateComplete;
  expect((part(drawn, ".confirms") as HTMLButtonElement).disabled).toBe(true);
  press(drawn, ".confirms");
  await settled(drawn);
  expect(asked.typed).toStrictEqual([]);
});

test("a station that came back running the tag is the flash that landed", async () => {
  const [drawn] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await settled(drawn);
  expect(reads(drawn, ".became.waiting")).toBe(WAITING);
  drawn.build = CHOSEN;
  await drawn.updateComplete;
  expect(reads(drawn, ".became.landed")).toBe(running(CHOSEN));
});

test("a station that came back running something else is a failure", async () => {
  const [drawn] = await flashing();
  press(drawn, ".chooses");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await settled(drawn);
  drawn.build = "v5.2.75";
  await drawn.updateComplete;
  expect(reads(drawn, ".became.failed")).toBe(instead(CHOSEN, "v5.2.75"));
});
