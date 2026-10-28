/**
 * The translator's **log** as the page holds it: what the face has served so
 * far, and the byte the next ask starts at (#365).
 *
 * The face serves the file whole or from byte N (`Range: bytes=N-`), and
 * answers a start past the end with a `416`, which is a file the translator
 * trimmed (docs/dccex_usb/README.md#the-log). What the page does with each
 * answer is here, and the asking is `face.ts`'s `log()`.
 *
 * The bytes are decoded as a stream, so a character split across two answers
 * is read whole. What has arrived is kept as the parts it arrived in, so a draw
 * adds the new part and leaves the old ones alone.
 */

/** What one ask of the log came to.
 *
 *  - `bytes`: the file from byte `from` on. A whole file is from `0`.
 *  - `trimmed`: the ask started past the end. The file was trimmed.
 *  - `says`: the face's sentence, where it would not serve the log.
 *  - `null`: no answer to read. */
export type Logged =
  | { readonly from: number; readonly bytes: Uint8Array }
  | { readonly trimmed: true }
  | { readonly says: string }
  | null;

/** The log as far as it has been read. */
export class Tail {
  /** The byte the next ask starts at. */
  at = 0;

  /** The text, in the parts it arrived in. */
  parts: string[] = [];

  /** The face's sentence where it would not serve the log, or `""`. */
  says = "";

  #decoder = new TextDecoder();

  /** Take one answer. Returns whether the log should be asked again at once,
   *  which is a trimmed file, read whole. A `null` changes nothing. */
  took(logged: Logged): boolean {
    if (logged === null) {
      return false;
    }
    if ("says" in logged) {
      this.#empty();
      this.says = logged.says;
      return false;
    }
    if ("trimmed" in logged) {
      this.#empty();
      return true;
    }
    if (logged.from !== this.at) {
      // A whole file where a part was asked for, or a part that does not
      // follow on: what is held is not the start of it. A part that does not
      // follow on is dropped, and the next ask is for the whole file.
      this.#empty();
      if (logged.from !== 0) {
        return false;
      }
    }
    this.says = "";
    this.at += logged.bytes.byteLength;
    const text = this.#decoder.decode(logged.bytes, { stream: true });
    if (text !== "") {
      this.parts = [...this.parts, text];
    }
    return false;
  }

  #empty(): void {
    this.at = 0;
    this.parts = [];
    this.says = "";
    this.#decoder = new TextDecoder();
  }
}
