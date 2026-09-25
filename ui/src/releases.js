/**
 * The releases the mirror is configured to read, as the page lists them:
 * newest first, each with its date, and the one that is on the station marked.
 *
 * What comes in is what the **face** answered — the **release**s the
 * configured source carries, in the source's own order — and what the station
 * says it is running, which is the **build** off its banner (ADR-0008 d.3).
 * What comes out is the rows a person reads. Nothing here fetches: the page
 * asks the face and hands the answer down, as it does with everything else it
 * knows (`face.ts`, `dccex-app.ts`).
 *
 * **Reading the answer is here too, and for the same reason.** `carried()`
 * below is what the page makes of a `releases` document — the rule `face.py`
 * draws on the same shape at the other end of the wire — and it sits beside
 * the listing rather than beside the `fetch` because neither has anything of
 * a browser in it, and what a bare node can run is asserted by running it
 * (#95, `tests/ui/test_releases.py`).
 *
 * **The source is the app's configuration and is nowhere on this page.** There
 * is no host, no repository and no URL in this module or in the one that
 * fetches for it: a page that could name where releases are read from would be
 * a page that decides what the command station is offered to run, and the LAN
 * carries no authentication on purpose (ADR-0042, `firmware.py`). What the
 * browser asks is the mirror's face on its own origin, and the face asks the
 * source it was started with.
 *
 * **Nor does anything the face says name it.** The promise above is about
 * what these modules spell, and it would be worth little if a sentence
 * written on the box arrived with the URL in it — the page shows what the
 * face said word for word (#66), so a refusal that spelled the source would
 * put it on the page by the back way. A flash turned down because the release
 * source could not be read, or answered with something that is not a release,
 * says so and names the **tag**; where it is read from is on the box's log,
 * for whoever is fixing it (`firmware.py`, `tests/dccex_usb/test_firmware.py`,
 * #94).
 *
 * **Newest first is this page's ordering and not the source's.** The face
 * passes the list on as it came, because which one is newest is a question
 * about the dates rather than about the wire, and it is asked here where the
 * list is drawn.
 *
 * A pure function of what the face said and of what the station said, so the
 * whole of it — the order, the dates, the mark — is asserted on a machine with
 * nothing plugged in and no network in reach (`tests/ui/test_releases.py`). It
 * is one of the modules of the page written as JavaScript with its types in
 * JSDoc — they are named in `tests/ui/test_decoder.py`'s docstring, which is
 * where they are counted so that a header need not (#110) — for the reason the
 * rest are: the gate is Python with a bare node in it, and a list an operator
 * reads asserted against the source that would produce it is not asserted.
 * `tsc` checks it as it checks the rest (`ui/tsconfig.json`).
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
 * @property {boolean} flashable whether it carries a firmware to write with
 *   a digest to check it against — false where it carries no firmware, and
 *   false where it carries one the source reports no digest for (#81,
 *   `face.py`'s `FLASHABLE`)
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
 * @property {boolean} flashable whether there is a firmware on it to write
 *   and a digest to check the write against, which is the one thing the face
 *   says about both of the releases there is nothing to write from (#81)
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
 *  the list: whether the station is up to date is a thing to see rather than
 *  to work out by reading a **build** and a **tag** against each other
 *  (docs/ui/README.md). */
export const ON_STATION = "on the station now";

/** What is said of a release there is nothing to write from: no firmware, or
 *  none with a digest to check it against. A release exists whether or not
 *  anything can be written from it (CONTEXT.md), and a row that looked like
 *  the others would send an operator to a **tag** the mirror would refuse
 *  (`face.py`).
 *
 *  **One sentence for two releases, because the face sends one boolean.**
 *  `flashable` is false for a release published with no `firmware.bin` and
 *  for one whose `firmware.bin` the source reports no digest for (#81,
 *  `face.py`'s `FLASHABLE`), and the wire says which of those it is nowhere.
 *  So the row says what is true of both — there is nothing here to write and
 *  nothing to check it against — rather than naming the first and being wrong
 *  about the second (#109). Which one it is, is on the mirror's refusal for
 *  whoever asks it to write the tag anyway (`firmware.py`). */
export const NO_FIRMWARE = "nothing here to write and check";

/** What is said where the face could not be asked. **Nothing said is not
 *  nothing published**: an empty list drawn for a face that did not answer
 *  would be this page reporting a source it never read (ADR-0009 d.2). */
export const UNREADABLE = "the releases could not be read";

/** What is said where the source answered and carries nothing. That is an
 *  answer and not an outage, and saying it the other way would send somebody
 *  to look at the network (`face.py`). */
export const NONE = "the source has published no releases yet";

/** The three fields a listed release carries, as the face names them. */
const TAG = "tag";
const PUBLISHED = "published";
const FLASHABLE = "flashable";

/**
 * The releases in `answer`, as the page reads what the face answered, or
 * `null` where it is not a list of releases at all.
 *
 * **This is `face.py`'s `carried()` at the other end of the wire.** Both read
 * the same shape and the duplication stays: the app reads a release API and
 * the page reads a network response, and each reads defensively because
 * neither is holding the other's memory. What must not differ is the rule, so
 * this is written as that one is — the same two names in the same order — and
 * whoever changes either should find the other.
 *
 * The rule is the line #66 was filed to draw. A source that lists nothing
 * carries no releases yet, which is an answer and comes back as an empty
 * list; a source that lists entries and names none of them is not answering
 * about releases, which is not, and comes back as `null`. The page has a
 * sentence for each and they are not the same sentence: `NONE` says the
 * source has published nothing, `UNREADABLE` says the releases could not be
 * read, and drawing the first for a document nobody could read would send
 * somebody to a release API that is perfectly well (ADR-0009 d.2).
 *
 * Read one field at a time, as the app reads the release API: a page that
 * reached into an answer would be a page taken down by whatever the app on
 * the other end of its own origin returned the day it returned something
 * else. An entry that names no tag is not a release, and the rest of a
 * release is left where it is rather than guessed at — no date reads as no
 * date, and no `flashable` reads as nothing to write, which is the direction
 * that does not send an operator at a tag the mirror would refuse.
 *
 * It is here rather than beside the `fetch` that gets the document because
 * this is the part with nothing of a browser in it, and a bare node can run
 * it: what the page makes of a release document is asserted by running it on
 * one rather than by reading the module that would (`tests/ui/test_releases.py`,
 * ADR-0009 d.3). What is left in `face.ts` is the asking.
 *
 * **What it is handed is not called `document`.** A `releases` document is
 * what arrives, and the prose above says so, but that word is a browser's
 * global and it is one of the literals the purity checks grep a module for,
 * to hold it to the claim this one makes about itself. This module is grepped
 * for it too now, along with the rest of the list its siblings are held to
 * (`tests/ui/test_releases.py`, #120, #122). So the parameter says what the
 * thing is — the face's answer — and no reader has to work out which
 * `document` a line means.
 *
 * The prose keeps the word because the check reads the code: the comments
 * come off before the scan, so a sentence about a JSON body is not a page
 * reaching for a DOM, and nothing above had to be reworded to be held to
 * anything (`tests/ui/test_stream.py`'s `code()`).
 *
 * @param {unknown} answer what the face answered under `releases`
 * @returns {Carried[] | null} the releases, or nothing said
 */
export function carried(answer) {
  if (!Array.isArray(answer)) {
    return null;
  }
  /** @type {unknown[]} */
  const listed = answer;
  const found = listed.flatMap((entry) => {
    if (typeof entry !== "object" || entry === null) {
      return [];
    }
    const fields = /** @type {Record<string, unknown>} */ (entry);
    const tag = fields[TAG];
    if (typeof tag !== "string" || tag === "") {
      return [];
    }
    const published = fields[PUBLISHED];
    return [
      {
        tag,
        published: typeof published === "string" ? published : "",
        flashable: fields[FLASHABLE] === true,
      },
    ];
  });
  if (listed.length > 0 && found.length === 0) {
    return null;
  }
  return found;
}

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
