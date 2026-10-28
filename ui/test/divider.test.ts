/**
 * The divider between the script view's editor and its **log** (#365): the
 * share it opens with, the share a drag and a key move it to, the edge that
 * hides the log, and the share the browser remembers.
 *
 * happy-dom lays nothing out, so the room the divider is dragged in is given
 * its rectangle by the check.
 */

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

/** A drag from the divider to (`x`, `y`). */
function drags(drawn: DccexDivider, x: number, y: number): void {
  drawn.dispatchEvent(new PointerEvent("pointerdown", { pointerId: 1 }));
  drawn.dispatchEvent(
    new PointerEvent("pointermove", { pointerId: 1, clientX: x, clientY: y }),
  );
  drawn.dispatchEvent(new PointerEvent("pointerup", { pointerId: 1 }));
}

test("it opens on the default share and says so", async () => {
  const [drawn, said] = await divider();
  expect(said).toStrictEqual([SHARE]);
  expect(drawn.getAttribute("role")).toBe("separator");
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
  drawn.dispatchEvent(
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

test("the arrow keys move it", async () => {
  const [drawn, said] = await divider();
  drawn.across = false;
  drawn.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
  expect(said.at(-1)).toBeCloseTo(SHARE + 0.05);
  drawn.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
  expect(said.at(-1)).toBeCloseTo(SHARE);
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
