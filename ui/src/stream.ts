/**
 * The stream as the page opens it: where it is, and what arrives on it.
 *
 * The monitor is a page and a page cannot dial the mirror's port. What a
 * browser can open is a stream on the origin it is already on, which it does
 * by upgrading a request under the prefix the door strips before the mirror's
 * face sees it (ADR-0004 d.2, ADR-0004 d.3). On the other end of it is one
 * more client of the mirror's port, and every rule that port has reaches this
 * page because of it: the fan-out, the bound on how far behind a client may
 * fall, the outage that disconnects everyone (ADR-0007 d.2).
 *
 * **There is nothing on it but bytes.** No status, no progress, no link and no
 * protocol of the page's own (ADR-0008 d.2). What arrives is what the station
 * said, cut into lines at the newlines it wrote and stamped with the moment
 * they arrived — which is the only time there is, because the stream carries
 * none.
 *
 * **Nothing here reads a line.** What one means is the decoder's, which is a
 * pure function of a line (ADR-0009), and what is sent for what was typed is
 * `message.js`'s, which is another. This module is the socket: where it is,
 * what arrives on it, and one whole message at a time going up it (#4, #6).
 *
 * **What goes up goes in one write.** The page holds what is being typed until
 * it is a whole `<…>` message and writes the message in one frame, so two
 * pages open at once cannot interleave a command — the same rule the mirror
 * holds every client of its port to (`framing.py`, ADR-0007 d.2).
 */

import { message } from "./message.js";

/** The prefix the mirror's face answers under on this page's own origin, and
 *  the whole of what it claims there — the door strips it before the app sees
 *  a request (ADR-0004 d.2). */
export const FACE = "/dccex-usb";

/** Where the stream is. Opened by upgrading and fetched no other way: what it
 *  carries is what the station is saying now (`face.py`). */
export const STREAM_PATH = `${FACE}/stream`;

const HTTPS = "https:";
const WSS = "wss:";
const WS = "ws:";

/** How long the page waits before opening the stream again.
 *
 * Everything that ends a stream is something that ends: the mirror cuts off a
 * client that has fallen too far behind, an outage disconnects every client at
 * once, and the app restarting takes them all with it (ADR-0007 d.2). A
 * monitor that stayed dead until somebody reloaded the page would ask an
 * operator to reload it for a cable that was out for ten seconds.
 */
export const REOPEN_MS = 2000;

/**
 * Every byte a character, and no byte thrown away.
 *
 * The station's bytes ride as binary frames because a serial line promises no
 * UTF-8 (ADR-0007 d.5), and decoding them as UTF-8 on this end would put a
 * replacement character where the byte the station sent should be — the page
 * editing the conversation it is showing. Latin-1 is the decoding that is
 * total: one byte, one character, and a `<…>` message, which is ASCII,
 * unchanged. It is also what lets a read be decoded on its own, with no
 * character left half-arrived across two of them.
 */
const CHARACTERS = new TextDecoder("latin1");

const NEWLINE = "\n";
const RETURN = /\r+$/;

/** One line of the conversation, and the moment it was on the page's clock. */
export interface Said {
  /** When it arrived: the page's clock at the read that carried it, or at the
   *  write that sent it. Two lines in one read carry the same stamp, which is
   *  what happened. */
  readonly at: Date;
  /** The line as the station said it, with the newline it ended off — or the
   *  whole message this page sent, as it went. */
  readonly line: string;
  /** Which end of the conversation it is: `true` where this page sent it,
   *  `false` where the station said it. The monitor draws the two differently,
   *  so a reader can tell their own traffic from the railroad's. */
  readonly sent: boolean;
}

/** Where the stream is for the page `where` was read off.
 *
 * The page's own address with the scheme swapped and nothing else touched, so
 * a browser opens `wss://` from a page served over `https` and `ws://` from
 * one served over plain HTTP, on whatever host and port the page itself came
 * from. Nothing about the stream is a name or a port of its own (ADR-0004
 * d.3), and nothing in this page names a host: a page that did would work on
 * the machine it was written on and nowhere else.
 */
export function streamAt(where: Location): string {
  const at = new URL(STREAM_PATH, where.href);
  at.protocol = where.protocol === HTTPS ? WSS : WS;
  return at.href;
}

/** Fold `arrived` into `buffered` and take off every whole line, stamped `at`.
 *
 * Returns what is still a partial line, to be passed back as `buffered` next
 * time, and the lines that completed, in the order they did — the shape the
 * mirror's own readers have (`stream.py`, `framing.py`), and for the same
 * reason: bytes arrive in whatever chunks the network hands over, and a rule
 * that needed a line whole would be a rule about the network.
 *
 * A line that is empty once its newline is off is dropped. It is the `\r` of a
 * `\r\n` pair and a blank line the station wrote, and neither is something it
 * said.
 */
export function lines(
  buffered: string,
  arrived: string,
  at: Date,
): [string, Said[]] {
  const whole = buffered + arrived;
  const parts = whole.split(NEWLINE);
  const rest = parts.pop() ?? "";
  const said: Said[] = [];
  for (const part of parts) {
    const line = part.replace(RETURN, "");
    if (line) {
      said.push({ at, line, sent: false });
    }
  }
  return [rest, said];
}

/**
 * The stream, open for as long as somebody is watching.
 *
 * It holds one socket, hands whole lines to whoever asked for them, takes one
 * whole message at a time back up, and opens another socket after `REOPEN_MS`
 * when the one it has goes. What the station said while the stream was away is
 * not in the one that follows — the mirror keeps no history and there is
 * nothing to ask for (ADR-0010).
 *
 * **A line the stream was cut off in the middle of is handed on as far as it
 * got.** Those bytes arrived, the newline that would have finished them never
 * will, and dropping them would be this page quietly losing what the station
 * said.
 */
export class Stream {
  readonly #said: (said: Said[]) => void;
  #socket: WebSocket | null = null;
  #reopening: ReturnType<typeof setTimeout> | null = null;
  #wanted = false;
  #partial = "";
  #partialAt = new Date();

  constructor(said: (said: Said[]) => void) {
    this.#said = said;
  }

  /** Open the stream, and keep one open until `close()`. */
  open(): void {
    this.#wanted = true;
    if (this.#socket === null && this.#reopening === null) {
      this.#dial();
    }
  }

  /** Let the stream go, and open no more of them: the monitor has left the
   *  page, so there is nobody to hand a line to. */
  close(): void {
    this.#wanted = false;
    if (this.#reopening !== null) {
      clearTimeout(this.#reopening);
      this.#reopening = null;
    }
    const socket = this.#socket;
    this.#socket = null;
    socket?.close();
  }

  /** Send what was typed, as one whole `<…>` message in one write.
   *
   * Returns the message that went, so the monitor can show what it sent, or
   * `null` where nothing did — there was nothing to send, or there is no
   * stream open to send it on. A page that showed a line it had not managed to
   * send would be telling an operator a command reached the station when it
   * reached nothing, which is the observation nobody made (ADR-0009 d.2).
   *
   * **One write, and the whole message in it.** The buffering is the box at
   * the foot: what is typed is held there until an operator sends it, and what
   * leaves here is a message rather than a keystroke. Two pages open at once
   * therefore cannot interleave a command, which is the rule the mirror holds
   * every client of its port to and is not written a second time here
   * (`framing.py`, ADR-0007 d.2).
   *
   * It rides as a text frame. The mirror reads what a page sends as payload
   * whatever kind of frame carries it, and a `<…>` message is ASCII, so there
   * is nothing here for a decoding to lose — which is not true of the bytes
   * coming the other way (ADR-0007 d.5).
   */
  send(typed: string): string | null {
    const said = message(typed);
    const socket = this.#socket;
    if (
      said === null ||
      socket === null ||
      socket.readyState !== WebSocket.OPEN
    ) {
      return null;
    }
    socket.send(said);
    return said;
  }

  #dial(): void {
    this.#reopening = null;
    this.#partial = "";
    const socket = new WebSocket(streamAt(window.location));
    socket.binaryType = "arraybuffer";
    socket.addEventListener("message", (said: MessageEvent<unknown>) => {
      this.#arrived(said.data);
    });
    // The socket going is the whole signal, as it is for every other client of
    // the mirror's port: a cut-off, an outage past its grace and the app going
    // down all reach a client as its connection ending (ADR-0007). An `error`
    // is followed by a `close`, so this is the one place either arrives at.
    socket.addEventListener("close", () => {
      this.#gone(socket);
    });
    this.#socket = socket;
  }

  #arrived(data: unknown): void {
    const text =
      typeof data === "string"
        ? data
        : data instanceof ArrayBuffer
          ? CHARACTERS.decode(data)
          : // A frame that is neither is not one the face sends: the station's
            // bytes ride as binary and `binaryType` is what this reads them as
            // (ADR-0007 d.5).
            "";
    const at = new Date();
    const [rest, said] = lines(this.#partial, text, at);
    this.#partial = rest;
    this.#partialAt = at;
    if (said.length > 0) {
      this.#said(said);
    }
  }

  #gone(socket: WebSocket): void {
    if (socket !== this.#socket) {
      return;
    }
    this.#socket = null;
    if (this.#partial) {
      this.#said([{ at: this.#partialAt, line: this.#partial, sent: false }]);
      this.#partial = "";
    }
    if (this.#wanted) {
      this.#reopening = setTimeout(() => {
        this.#dial();
      }, REOPEN_MS);
    }
  }
}
