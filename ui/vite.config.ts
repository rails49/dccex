import { defineConfig } from "vite";

// The page is one entry and one output directory. `deploy/ui.Dockerfile`'s
// node stage runs this and the nginx stage copies `dist/` out of it, so what
// the box serves is what came out of here and nothing else.
//
// The proxy is the development server's and is in nothing the box runs. On a
// box the door routes `/mqtt` on this page's host to `control`'s broker and
// strips the prefix (`compose.box.yaml`, ADR-0017 d.5); on a laptop there is
// no door, so this stands in for one and strips the same prefix, and the page
// goes on knowing nothing but its own origin (`ui/src/bus.ts`).
export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/mqtt": {
        target: "ws://127.0.0.1:9001",
        ws: true,
        rewrite: (path) => path.replace(/^\/mqtt/, ""),
      },
    },
  },
});
