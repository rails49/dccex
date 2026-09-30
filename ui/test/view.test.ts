/**
 * Which **view** a hash names, and which hash a view is kept under.
 *
 * The pair that matters is the round trip: what the rail writes when a button
 * is pressed is what the page reads back on the next `hashchange`, and a page
 * opened on a link somebody sent shows the view that link names. A hash
 * nobody wrote is the other half — a reader typing something of their own
 * into the address bar gets the monitor rather than a blank pane.
 */

import { expect, test } from "vitest";

import { OPENS, VIEWS, type View, hashed, viewed } from "../src/view.js";

test("the two views are the monitor and the releases", () => {
  expect([...VIEWS]).toStrictEqual(["monitor", "releases"]);
});

test("a page opened with no hash shows the monitor", () => {
  expect(viewed("")).toBe("monitor");
  expect(OPENS).toBe("monitor");
});

test("the releases are the hash the link names", () => {
  expect(hashed("releases")).toBe("#releases");
  expect(viewed("#releases")).toBe("releases");
});

test("what the rail writes is what the page reads back", () => {
  for (const view of VIEWS) {
    expect(viewed(hashed(view))).toBe(view);
  }
});

test("a hash nobody wrote is the monitor and not a blank pane", () => {
  for (const hash of ["#", "#tiles", "#RELEASES", "#releases/1", "releases "]) {
    expect(viewed(hash)).toBe(OPENS);
  }
});

test("a view named without its hash is still that view", () => {
  // `location.hash` carries the `#` and a hand-written one may not.
  const view: View = "releases";
  expect(viewed(view)).toBe(view);
});
