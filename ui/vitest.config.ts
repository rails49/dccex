import { defineConfig } from "vitest/config";

// The components, mounted. `vite.config.ts` beside this builds the page and
// says nothing about checking it; this file is the other job and is kept
// apart from it so that what the image builds cannot be changed by what the
// checks need.
//
// `happy-dom` is the DOM the components are mounted in: custom elements, a
// shadow root, an animation frame and the rectangles Lit asks for, in a
// process rather than a browser. It does no layout — nothing here may assert
// a width, a wrap or a height — which is why the widths a phone reads at are
// held against the built page in a browser
// (`tests/ui/test_page_at_a_phones_width.py`, #126).
//
// `mqtt` is aliased to a broker with nothing behind it, for the same reason:
// the page is a client of `control`'s broker and there is none here, so what a
// check drives is the connection the page made rather than a socket
// (`ui/test/support/broker.ts`, ADR-0017 d.5). The alias is this file's and
// not the build's — the page that runs on the box dials the real one.
//
// **This is not the gate.** `scripts/check.sh` is Python and runs with no
// node on the machine; these run in the workflow's `node` job beside the
// modules a bare node runs (`.github/workflows/ci.yml`, `pyproject.toml`).
export default defineConfig({
  resolve: {
    alias: {
      mqtt: new URL("./test/support/broker.ts", import.meta.url).pathname,
    },
  },
  test: {
    environment: "happy-dom",
    include: ["test/**/*.test.ts"],
    setupFiles: ["test/mounted.ts"],
    // A Shoelace dialog shut while it opens cancels its animation, and
    // happy-dom rejects the cancelled animation's promise where a browser
    // marks it handled. That rejection, and no other, is not a failure.
    onUnhandledError: (error) =>
      error.name === "AbortError" &&
      error.message === "The animation was canceled."
        ? false
        : undefined,
  },
});
