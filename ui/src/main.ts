/**
 * What the page runs: look's stylesheet, where Shoelace's assets are served
 * from, and the app.
 *
 * `look.css` carries Shoelace's light and dark themes, and the system's
 * setting picks one. Shoelace's glyphs are served from the page's own origin
 * at `/shoelace` (`vite.config.ts`), so nothing is fetched from a CDN.
 */

import "@rails49/look/look.css";
import { setBasePath } from "@shoelace-style/shoelace/dist/utilities/base-path.js";

import "./ui/dccex-app.js";

setBasePath("/shoelace");
