/**
 * Light or dark, as the system says, with no toggle in the page.
 *
 * Both Shoelace themes are linked and `prefers-color-scheme` decides (LOOK.md).
 * Shoelace's dark theme is a class rather than a query of its own, so linking
 * the two sheets is half the job and following the setting is the other half:
 * a page that linked both and set no class would sit in the light one whatever
 * the system says.
 *
 * The chrome does not follow it. The band and the rail keep one value in both
 * themes, which is what `look.css` holds and why it has no dark half.
 */

import "@shoelace-style/shoelace/dist/themes/light.css";
import "@shoelace-style/shoelace/dist/themes/dark.css";

const dark = window.matchMedia("(prefers-color-scheme: dark)");

function wear(): void {
  document.documentElement.classList.toggle("sl-theme-dark", dark.matches);
}

/** Wear the system's setting now, and again whenever it changes. */
export function followTheSystemTheme(): void {
  wear();
  dark.addEventListener("change", wear);
}
