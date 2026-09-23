import { defineConfig } from "vite";

// The page is one entry and one output directory. `deploy/ui.Dockerfile`'s
// node stage runs this and the nginx stage copies `dist/` out of it, so what
// the box serves is what came out of here and nothing else.
export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
