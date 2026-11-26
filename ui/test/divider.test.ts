/**
 * The divider between the script view's editor and its **log** (#365, #416):
 * the share it opens with, the way its `look-gap` is dragged, the share a
 * drag moves it to, the edge that hides the log, and the share the browser
 * remembers.
 *
 * happy-dom lays nothing out, so the room the divider is dragged in is given
 * its rectangle by the check.
 */

import type { LookGap } from "@rails49/look";
import { afterEach, expect, test } from "vitest";

import {
  DccexDivider,
  REMEMBERED,
  SHARE,
  held,
  remembered,
} from "../src/ui/dccex-divider.js";

afterEach(() => {
  localStorage.clear();
});

/** A divider in a room `width` by `height` at the origin, and every share it
 *  said, the one it opened with first. */
async function divider(
  width = 1000,
  height = 1000,
): Promise<[DccexDivider, number[]]> {
  const said: number[] = [];
  const room = document.createElement("div");
  room.getBoundingClientRect = () => new DOMRect(0, 0, width, height);
  document.body.append(room);
  const drawn = new DccexDivider();
  drawn.addEventListener("divided", (e) => {
    said.push((e as CustomEvent<number>).detail);
  });
  room.append(drawn);
  await drawn.updateComplete;
  return [drawn, said];
}

/** The `look-gap` the divider drew. */
function gap(drawn: DccexDivider): LookGap {
  return drawn.renderRoot.querySelector("look-gap")!;
}

/** A drag of the divider's gap to (`x`, `y`). The gap says each move in a
 *  `look-gap-move`. */
function drags(drawn: DccexDivider, x: number, y: number): void {
  for (const name of ["pointerdown", "pointermove", "pointerup"]) {
    gap(drawn).dispatchEvent(
      new PointerEvent(name, { button: 0, clientX: x, clientY: y }),
    );
  }
}

test("it opens on the default share and says so", async () => {
  const [, said] = await divider();
  expect(said).toStrictEqual([SHARE]);
});

test("the gap is dragged sideways beside the editor, and up and down below it", async () => {
  const [drawn] = await divider();
  drawn.across = true;
  await drawn.updateComplete;
  expect(gap(drawn).axis).toBe("x");
  drawn.across = false;
  await drawn.updateComplete;
  expect(gap(drawn).axis).toBe("y");
});

test("a drag below the editor gives the log what is under the pointer", async () => {
  const [drawn, said] = await divider();
  drawn.across = false;
  drags(drawn, 500, 700);
  expect(said.at(-1)).toBeCloseTo(0.3);
});

test("a drag beside the editor gives the log what is right of the pointer", async () => {
  const [drawn, said] = await divider();
  drawn.across = true;
  drags(drawn, 800, 500);
  expect(said.at(-1)).toBeCloseTo(0.2);
});

test("a move with no press is not a drag", async () => {
  const [drawn, said] = await divider();
  gap(drawn).dispatchEvent(
    new PointerEvent("pointermove", { clientX: 10, clientY: 10 }),
  );
  expect(said).toStrictEqual([SHARE]);
});

test("dragged to the edge the log is hidden, and dragged back it shows", async () => {
  const [drawn, said] = await divider();
  drawn.across = false;
  drags(drawn, 500, 995);
  expect(said.at(-1)).toBe(0);
  drags(drawn, 500, 500);
  expect(said.at(-1)).toBeCloseTo(0.5);
});

test("the share is remembered and a new divider opens on it", async () => {
  const [drawn] = await divider();
  drawn.across = false;
  drags(drawn, 500, 750);
  expect(localStorage.getItem(REMEMBERED)).toBe("0.25");
  const [, said] = await divider();
  expect(said).toStrictEqual([0.25]);
});

test("a store that refuses still opens and still moves", async () => {
  const getItem = Storage.prototype.getItem;
  const setItem = Storage.prototype.setItem;
  Storage.prototype.getItem = () => {
    throw new Error("refused");
  };
  Storage.prototype.setItem = () => {
    throw new Error("refused");
  };
  try {
    expect(remembered()).toBe(SHARE);
    const [drawn, said] = await divider();
    drawn.across = false;
    drags(drawn, 500, 500);
    expect(said).toStrictEqual([SHARE, 0.5]);
  } finally {
    Storage.prototype.getItem = getItem;
    Storage.prototype.setItem = setItem;
  }
});

test("a share is held between the edge and the most the log takes", () => {
  expect(held(0.01)).toBe(0);
  expect(held(0.5)).toBe(0.5);
  expect(held(2)).toBe(0.9);
  expect(held(Number.NaN)).toBe(SHARE);
});
