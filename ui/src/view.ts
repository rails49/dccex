/**
 * The **view**s, and the hash the page keeps the current one in.
 *
 * There are three — the **monitor**, the releases and the **script** — and the
 * **rail** picks between them (CONTEXT.md, #166, #169, issue 185). The **band**
 * is the same over all of them: what is true of the whole station does not
 * change with what a person is looking at.
 *
 * **The hash is where the view is kept**, so the address bar says which one a
 * page is on. A view somebody is looking at can then be sent to somebody else,
 * a reload comes back where it was, and the browser's back button steps
 * through the views rather than off the page. The page reads it and the rail's
 * press writes it, which is one direction each and one answer to which view is
 * in front of a person (`dccex-app.ts`).
 *
 * **Anything else in the hash is the monitor.** A hash nobody here wrote — a
 * fragment typed by hand, a link from an older page, an empty `#` — is not a
 * view, and the page that answers it with a blank pane is the page saying
 * nothing rather than saying the default. The station's conversation is what
 * this UI is for, so that is what an unrecognised hash lands on.
 *
 * Both rules are pure functions of a string, so the pairs that matter go
 * through them rather than being read off a template (`ui/test/view.test.ts`).
 */

/** What the work pane shows: one of the three. */
export type View = "monitor" | "releases" | "script";

/** The views, in the order the rail draws a button for each of them.
 *
 *  Written out once. The rail iterating this is a rail that cannot offer a
 *  view the page would not read back, and a view is one entry here and one
 *  icon there. */
export const VIEWS: readonly View[] = ["monitor", "releases", "script"];

/** The view a page with no view named in its hash opens on. */
export const OPENS: View = "monitor";

/** The view `hash` names, or `OPENS` where it names none.
 *
 *  `location.hash` carries its `#` and a hand-written name may not, so both
 *  forms are read. Nothing else is: a name that is not a view exactly is not
 *  a view, because the alternative is a page guessing which one a reader
 *  meant. */
export function viewed(hash: string): View {
  const named = hash.startsWith("#") ? hash.slice(1) : hash;
  for (const view of VIEWS) {
    if (view === named) {
      return view;
    }
  }
  return OPENS;
}

/** The hash `view` is kept under: its own name, which is the word the rail's
 *  button says and the word the glossary uses. */
export function hashed(view: View): string {
  return `#${view}`;
}
