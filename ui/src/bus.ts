/**
 * The bus as the page reaches it: one connection to `control`'s broker, the
 * one row the **band** reads off it, and the row a press writes.
 *
 * **The band asks `layout` for power** (ADR-0017). A press used to send `<1>`
 * or `<0>` through the **face**, which skipped `layout` and the **translator**
 * — and `layout` is what refuses an OFF while a run is going, zeroes every
 * locomotive's speed before a cut, and runs the **script**'s power handler. So
 * the page publishes `tc49/layout/power_wanted`, a row a browser may write
 * (the organisation's ADR-0002), and reads `tc49/layout/state/power` back.
 * Nothing about power goes up the stream any more.
 *
 * **It is the page's second counterparty and the bus is the whole of it.** A
 * UI talks to the bus, the store and its own app's face (the organisation's
 * ADR-0002); this page talks to the first and the third, and it subscribes to
 * one row rather than to a railroad — what a railroad is doing is `control`'s
 * UI next door, and the one thing this page needs of it is whether the rails
 * are hot and a way to ask for them.
 *
 * **The broker is on the page's own origin** (ADR-0017 d.5). A browser served
 * over the box's door cannot dial 9001 on the layout box, and the page is not
 * cross-origin to anything: the door routes `/mqtt` on this host to
 * `control`'s broker and refuses a page from anywhere else, which is the shape
 * the face's own prefix has (`compose.box.yaml`, ADR-0004 d.2). The address is
 * `socketAt`'s, as the stream's is, so a page served over plain HTTP opens
 * `ws://` and nothing here names a host or a port (`framing.js`).
 *
 * **Nothing here reads a payload.** What one means is `readings.js`'s
 * `reported`, which is a pure function of the bytes and is run rather than
 * read (`tests/ui/test_readings.py`). This module is the connection: where it
 * is, what is subscribed to, and what is published — none of which a gate
 * without a broker can exercise, so the checks that drive it mount it against
 * a broker with nothing behind it (`ui/test/support/broker.ts`).
 */

import { connect, type MqttClient } from "mqtt";

import { socketAt } from "./framing.js";
import { UNREACHABLE, reported, type Layout } from "./readings.js";

/** Where the broker answers on this page's own origin, and the whole of what
 *  it claims there — the door strips it before the broker sees a request, as
 *  it strips the face's (ADR-0017 d.5). */
export const MQTT_PATH = "/mqtt";

/** The one row the page subscribes to: what `layout` says the railroad's power
 *  is (ADR-0017 d.2). */
export const POWER_STATE = "tc49/layout/state/power";

/** The row a press writes: what the band asks `layout` for (ADR-0017 d.1). */
export const POWER_WANTED = "tc49/layout/power_wanted";

/** How long the client waits before dialling the broker again.
 *
 * The same two seconds the **stream** waits, and for the same reason:
 * everything that ends a connection is something that ends — an outage, the
 * broker restarting, the door going down — and a band that stayed disabled
 * until somebody reloaded the page would ask an operator to reload it for a
 * network that was out for ten seconds (`REOPEN_MS`, `stream.ts`).
 */
export const RECONNECT_MS = 2000;

/**
 * The connection, held for as long as the page is in the document.
 *
 * It hands up what `layout` says as one value, every time that changes: the
 * broker being there, and the power row. The band is drawn from it beside the
 * **link** (`band()`, `readings.js`).
 *
 * **A connection that goes takes the row with it.** What `layout` reported
 * before an outage is not a reading after one, the same way the **build** is
 * not a reading once the station has stopped talking (ADR-0008 d.3): the
 * button is disabled on `no bus` either way, and a reconnect is handed the
 * state row again rather than trusting what this page remembered of it.
 *
 * **Nothing is held to be published when the connection comes back.** A press
 * is a command about a railroad, and asking for power seconds later, when the
 * operator has moved on, is worse than not asking (`stream.ts`, #6) — so the
 * client queues nothing, and the button is disabled for the whole of the time
 * there would be anything to queue.
 */
export class Bus {
  readonly #reports: (layout: Layout) => void;
  #client: MqttClient | null = null;
  #layout: Layout = UNREACHABLE;

  constructor(reports: (layout: Layout) => void) {
    this.#reports = reports;
  }

  /** Reach the broker, and keep one connection until `close()`. */
  open(): void {
    if (this.#client !== null) {
      return;
    }
    const client = connect(socketAt(window.location, MQTT_PATH), {
      reconnectPeriod: RECONNECT_MS,
      // Nothing is kept back while the connection is down, which is the
      // stream's rule about a command an operator typed (#6).
      queueQoSZero: false,
    });
    client.on("connect", () => {
      client.subscribe(POWER_STATE, { qos: 0 });
      this.#says({ connected: true, power: this.#layout.power });
    });
    // The connection going is the whole signal, as it is for the stream: an
    // outage, a broker restarting and the door going down all reach a client
    // as its connection ending. An `error` is followed by a `close`, and this
    // is the one place either arrives at — the handler is there because a
    // client with nobody listening for an error throws one instead.
    client.on("error", () => {
      /* the close that follows is what says the bus is away */
    });
    client.on("close", () => {
      this.#says(UNREACHABLE);
    });
    client.on("message", (topic: string, payload: Uint8Array) => {
      if (topic === POWER_STATE) {
        this.#says({
          connected: true,
          power: reported(new TextDecoder().decode(payload)),
        });
      }
    });
    this.#client = client;
  }

  /** Let the connection go, and reach for no more of them: the page has gone,
   *  so there is nobody to hand a reading to. */
  close(): void {
    const client = this.#client;
    this.#client = null;
    this.#says(UNREACHABLE);
    client?.end(true);
  }

  /** Ask `layout` for power: `on`, `off` or `stopped` (ADR-0017 d.1).
   *
   * The whole of what the page does about power. What becomes of the ask is
   * `layout`'s — it refuses an OFF while a run is going and zeroes every
   * locomotive before a cut (`control` ADR-0062) — and what the page shows is
   * the state row that follows, or nothing where none does (ADR-0017 d.4).
   *
   * Not retained, at QoS 0: it is a request and not a state, and a retained
   * one would be answered again by every `layout` that started afterwards.
   */
  wants(power: string): void {
    this.#client?.publish(POWER_WANTED, JSON.stringify({ power }), {
      qos: 0,
      retain: false,
    });
  }

  /** Hand a reading up, and keep it so the next one can be built on it. */
  #says(layout: Layout): void {
    this.#layout = layout;
    this.#reports(layout);
  }
}
