/**
 * Where the mirror's face is, on this page's own origin.
 *
 * A **face** is an app's own interface, about that app rather than about a
 * railroad, and this page's one counterparty is the mirror's (CONTEXT.md,
 * ADR-0008 d.1). It answers under a prefix the door strips before the app
 * sees a request, so the page and the face share one origin and one
 * certificate and nothing here is a host or a port (ADR-0004 d.2).
 *
 * The prefix is written once, here, and everything the page asks for is built
 * from it: the stream the conversation rides (`stream.ts`) as much as anything
 * fetched. A second spelling of it somewhere on the page would be a second
 * answer to where the app is, and the day the door's route moves only one of
 * them would follow.
 *
 * **Everything fetched here is fetched with an address built from that
 * prefix and with nothing on it.** The two things the page asks for — how many
 * **client**s are on the mirror's port, and what **release**s the configured
 * source carries — are questions about the app, not questions with parameters:
 * where releases are read from is that app's own configuration, and a page
 * that could name it would be a page deciding what the command station is
 * offered to run (ADR-0042, `firmware.py`).
 */

import { type Carried } from "./releases.js";

/** The prefix the mirror's face answers under on this page's own origin, and
 *  the whole of what it claims there — the door strips it before the app sees
 *  a request (ADR-0004 d.2). */
export const FACE = "/dccex-usb";

/** Where how many **client**s are on the mirror's port is asked. It is the one
 *  reading on the page the station cannot make: a command station knows
 *  nothing about who is listening to it, and the app holding the port does
 *  (ADR-0008 d.4, `face.py`). */
export const CLIENTS_PATH = `${FACE}/clients`;

/** What the count comes back under. */
const CLIENTS = "clients";

/**
 * How many clients are on the mirror's port, or `null` where the face did not
 * say.
 *
 * **Nothing said is not nobody there.** A face that is away, an answer that is
 * not a count, a status that is not a 200 — all of them come back as `null`
 * and the tile blanks, because a page drawing `0` for an app it could not ask
 * would be reporting an empty port it never saw (ADR-0009 d.2). Zero is what
 * the face says when the port is empty, and on the box this UI exists for that
 * is the ordinary evening.
 *
 * It answers rather than raising for the same reason: this is one reading on a
 * page whose other readings are arriving on the stream, and a rejection left
 * loose would be a tile taking the rest of them down with it.
 */
export async function clients(): Promise<number | null> {
  try {
    const answered = await fetch(CLIENTS_PATH);
    if (!answered.ok) {
      return null;
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return null;
    }
    const count = (said as Record<string, unknown>)[CLIENTS];
    return typeof count === "number" ? count : null;
  } catch {
    return null;
  }
}

/** Where the **release**s the configured source carries are asked for. The
 *  page asks its own app's face and never the release API: a UI talks to the
 *  bus, the store and its own app's face and nothing else (ADR-0002), and
 *  where releases are read from is a flag on that app rather than anything a
 *  browser can name (ADR-0042, `face.py`). */
export const RELEASES_PATH = `${FACE}/releases`;

/** What the list comes back under. */
const RELEASES = "releases";

/** The three fields a listed release carries. */
const TAG = "tag";
const PUBLISHED = "published";
const FLASHABLE = "flashable";

/**
 * The releases the configured source carries, or `null` where the face did
 * not say.
 *
 * **Nothing said is not nothing published**, for the reason `clients` above
 * answers `null`: a face that is away, an answer that is not a list of
 * releases, a status that is not a 200 — an empty list drawn for any of them
 * would be this page reporting a source it never read, and would send somebody
 * to a release API that is perfectly well (ADR-0009 d.2). The source carrying
 * nothing is a different sentence and it is the face's `[]`.
 *
 * Read one field at a time, as the app reads the release API (`face.py`): a
 * page that reached into an answer would be a page taken down by whatever the
 * app on the other end of its own origin returned the day it returned
 * something else. An entry that names no tag is not a release, and the rest of
 * a release is left where it is rather than guessed at — no date reads as no
 * date, and no `flashable` reads as nothing to write, which is the direction
 * that does not send an operator at a tag the mirror would refuse.
 */
export async function releases(): Promise<Carried[] | null> {
  try {
    const answered = await fetch(RELEASES_PATH);
    if (!answered.ok) {
      return null;
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return null;
    }
    const listed = (said as Record<string, unknown>)[RELEASES];
    if (!Array.isArray(listed)) {
      return null;
    }
    return listed.flatMap((entry: unknown) => {
      if (typeof entry !== "object" || entry === null) {
        return [];
      }
      const fields = entry as Record<string, unknown>;
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
  } catch {
    return null;
  }
}
