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
 */

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
