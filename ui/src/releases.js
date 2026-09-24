/**
 * The releases the box is configured to read, as the page lists them: newest
 * first, each with its date, and the one that is on the station marked.
 *
 * What comes in is what the **face** answered — the **release**s the
 * configured source carries, in the source's own order — and what the station
 * says it is running, which is the **build** off its banner (ADR-0008 d.3).
 * What comes out is the rows a person reads. Nothing here fetches: the page
 * asks the face and hands the answer down, as it does with everything else it
 * knows (`face.ts`, `dccex-app.ts`).
 *
 * **The source is the app's configuration and is nowhere on this page.** There
 * is no host, no repository and no URL in this module or in the one that
 * fetches for it: a page that could name where releases are read from would be
 * a page that decides what the command station is offered to run, and the LAN
 * carries no authentication on purpose (ADR-0042, `firmware.py`). What the
 * browser asks is the mirror's face on its own origin, and the face asks the
 * source it was started with.
 *
 * **Newest first is this page's ordering and not the source's.** The face
 * passes the list on as it came, because which one is newest is a question
 * about the dates rather than about the wire, and it is asked here where the
 * list is drawn.
 *
 * A pure function of what the face said and of what the station said, so the
 * whole of it — the order, the dates, the mark — is asserted on a machine with
 * nothing plugged in and no network in reach (`tests/ui/test_releases.py`). It
 * is the fourth module of the page written as JavaScript with its types in
 * JSDoc, for the reason the other three are: the gate is Python with a bare
 * node in it, and a list an operator reads asserted against the source that
 * would produce it is not asserted. `tsc` checks it as it checks the rest
 * (`ui/tsconfig.json`).
 */

/**
 * One release, as the mirror's face answers it.
 *
 * Three facts and no more, which is the whole of what the face passes on: the
 * rest of a release document is somebody else's shape and never reaches this
 * page (`face.py`).
 *
 * @typedef {object} Carried
 * @property {string} tag what the release is named by, and the only thing a
 *   caller ever names one with
 * @property {string} published when the source published it, as the source
 *   stamped it, or `""` where it stamped none
 * @property {boolean} flashable whether it carries a firmware to write
 */

/**
 * One release as a row on the page.
 *
 * @typedef {object} Listed
 * @property {string} tag what the release is named by
 * @property {string} published the day it was published, in the words a person
 *   reads, or `""` where the source named none
 * @property {boolean} onStation whether this is the release the station is
 *   running now
 * @property {boolean} flashable whether it carries a firmware to write
 */

/**
 * The releases as the page shows them: the rows, and what it has to say where
 * there are none.
 *
 * @typedef {object} Listing
 * @property {string} says why the list is empty, or `""` where it is not
 * @property {Listed[]} rows the releases, newest first
 */

/** What is said of the release the station is running now. It is the point of
 *  the list: whether the box is up to date is a thing to see rather than to
 *  work out by reading a **build** and a **tag** against each other
 *  (docs/ui/README.md). */
export const ON_STATION = "on the station now";

/** What is said of a release published with no firmware on it. A release
 *  exists whether or not anything can be written from it (CONTEXT.md), and a
 *  row that looked like the others would send an operator to a **tag** the
 *  mirror would refuse (`face.py`). */
export const NO_FIRMWARE = "no firmware to write";

/** What is said where the face could not be asked. **Nothing said is not
 *  nothing published**: an empty list drawn for a face that did not answer
 *  would be this page reporting a source it never read (ADR-0009 d.2). */
export const UNREADABLE = "the releases could not be read";

/** What is said where the source answered and carries nothing. That is an
 *  answer and not an outage, and saying it the other way would send somebody
 *  to look at the network (`face.py`). */
export const NONE = "the source has published no releases yet";

/** The day out of a moment, as the source stamped it. */
const DAY = /^(\d{4}-\d{2}-\d{2})/;

/**
 * The day a release was published, in the words a person reads.
 *
 * The date as the source wrote it, cut at the day: a stamp is UTC and a reader
 * is at the layout, so an hour drawn here would be an hour in a zone nobody
 * asked about. `2025-09-14` rather than a month's name because this page is
 * read in more than one country and a date nobody has to disambiguate is worth
 * more than a pretty one.
 *
 * A stamp this cannot read is no date, which is what a release the source
 * named none for gets: a guess standing where a reading goes is an observation
 * the page did not make (ADR-0009 d.2).
 *
 * @param {string} published as the source stamped it
 * @returns {string} the day, or `""`
 */
function day(published) {
  const stamped = DAY.exec(published);
  return stamped === null ? "" : stamped[1];
}

/**
 * Newest first, and the ones the source dated before the ones it did not.
 *
 * The stamps are compared whole rather than by the day the row shows, so two
 * releases published on one afternoon are in the order they were published.
 * Equal stamps and missing ones keep the order the source listed them in,
 * because the sort is stable and the source's order is the only other thing
 * there is to go on.
 *
 * @param {Carried} a
 * @param {Carried} b
 * @returns {number}
 */
function newestFirst(a, b) {
  if (a.published === b.published) {
    return 0;
  }
  if (a.published === "") {
    return 1;
  }
  if (b.published === "") {
    return -1;
  }
  return a.published < b.published ? 1 : -1;
}

/**
 * The releases as the page lists them.
 *
 * **The release on the station is the one whose tag is the build.** The build
 * is what the station said it is running, off the `G-` field of its banner,
 * and it goes with the **link**: a station that is not answering has no build,
 * so nothing is marked and no row claims to be what is on a board the page
 * cannot see (ADR-0008 d.3). A build that matches nothing in the list marks
 * nothing either — it is a station running something the source does not
 * carry, which is a true thing to show and not an error.
 *
 * @param {Carried[] | null} carried what the face answered, or nothing
 * @param {string | null} build what the station says it is running
 * @returns {Listing}
 */
export function listing(carried, build) {
  if (carried === null) {
    return { says: UNREADABLE, rows: [] };
  }
  const rows = [...carried].sort(newestFirst).map((release) => ({
    tag: release.tag,
    published: day(release.published),
    onStation: build !== null && release.tag === build,
    flashable: release.flashable,
  }));
  return { says: rows.length === 0 ? NONE : "", rows };
}
