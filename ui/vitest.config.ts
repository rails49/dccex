import { defineConfig } from "vitest/config";

// The components, mounted. `vite.config.ts` beside this builds the page and
// says nothing about checking it; this file is the other job and is kept
// apart from it so that what the image builds cannot be changed by what the
// checks need.
//
// `happy-dom` is the DOM the components are mounted in: custom elements, a
// shadow root, an animation frame and the rectangles Lit asks for, in a
// process rather than a browser. It does no layout — nothing here may assert
// a width, a wrap or a height — which is why the look rules and the widths a
// phone reads at are still held against the stylesheets
// (`tests/ui/test_look.py`, #126).
//
// **This is not the gate.** `scripts/check.sh` is Python and runs with no
// node on the machine; these run in the workflow's `node` job beside the
// modules a bare node runs (`.github/workflows/ci.yml`, `pyproject.toml`).
export default defineConfig({
  test: {
    environment: "happy-dom",
    include: ["test/**/*.test.ts"],
    setupFiles: ["test/mounted.ts"],
  },
});
