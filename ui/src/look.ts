/**
 * The one look rule a stylesheet cannot read for itself.
 *
 * `look.css` holds every value this page draws with, as custom properties the
 * rules ask for by name. A media query cannot read a custom property, so the
 * height at which the rail lies down has to reach the two sheets that turn as
 * a number instead — `dccex-app.styles.ts` gives the rail a row to lie in and
 * `dccex-rail.styles.ts` lies its own contents down, and a page that turned
 * one without the other would draw the strip inside a column that is still
 * there.
 *
 * One number, interpolated into both, rather than two that agree.
 * `tests/ui/test_look.py` holds it against `--rail-turns` in the copy.
 */

/** The window height at or below which the rail becomes a horizontal strip
 *  along the top of the work. `--rail-turns` in `look/tokens.css`. */
export const RAIL_TURNS_PX = 640;
