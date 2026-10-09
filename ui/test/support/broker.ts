/**
 * A broker with nothing behind it: what `mqtt` is in the page's checks.
 *
 * `ui/src/bus.ts` dials the broker on the page's own origin, reads one row off
 * it and publishes another. happy-dom has no socket and the suite has no
 * broker, so the vitest config aliases `mqtt` to this module and a check
 * drives the connection the page made: say it is up, put a payload on a row,
 * say it has gone, and read back what the page published and what it asked for
 * (`vitest.config.ts`, `ui/test/bus.test.ts`).
 *
 * **It is the page's counterparty and not a broker.** Nothing here speaks
 * MQTT, keeps a session or honours a QoS: what a check asserts is what the page
 * asked for, which is where a wrong topic, a retained row or a second
 * connection shows (ADR-0017 d.1, d.5). `control`'s page is a client of the
 * same broker and its checks hold it the same way.
 */

/** One `publish` the page made, as it made it. */
export interface Published {
  readonly topic: string;
  readonly payload: string;
  readonly qos: number | undefined;
  readonly retain: boolean | undefined;
}

/** What the page asked `mqtt` to do, and the three things a check says back. */
export interface Dialled {
  /** Where the page asked for the broker. */
  readonly url: string;
  /** What it asked for: the options it handed `connect`. */
  readonly options: Record<string, unknown>;
  /** The rows it subscribed to, in the order it did. */
  readonly subscribed: readonly string[];
  /** What it published, in the order it did. */
  readonly published: readonly Published[];
  /** Whether it has let the connection go. */
  readonly ended: boolean;
  /** Say the connection is up. */
  connects: () => void;
  /** Say it has gone, which is what an outage reaches a client as. */
  closes: () => void;
  /** Put `payload` on `topic`, as a broker would. */
  says: (topic: string, payload: string) => void;
}

type Listener = (...said: never[]) => void;

/** Every connection the page has made, in the order it made them.
 *
 *  A list rather than the latest one, because the page opening a second
 *  connection is a defect a check should be able to name (`bus.ts`). */
export const dialled: Dialled[] = [];

/** Forget them. A connection left here would be the next check reading the
 *  one before it. */
export function forgotten(): void {
  dialled.length = 0;
}

/** `mqtt.connect`, as the page calls it. */
export function connect(
  url: string,
  options: Record<string, unknown> = {},
): unknown {
  const listeners = new Map<string, Listener[]>();
  const subscribed: string[] = [];
  const published: Published[] = [];
  const said = (event: string, ...carries: unknown[]): void => {
    for (const listener of listeners.get(event) ?? []) {
      (listener as (...said: unknown[]) => void)(...carries);
    }
  };
  const made = {
    url,
    options,
    subscribed,
    published,
    ended: false,
    connects: () => {
      said("connect");
    },
    closes: () => {
      said("close");
    },
    says: (topic: string, payload: string) => {
      said("message", topic, new TextEncoder().encode(payload));
    },
  };
  dialled.push(made);
  return {
    on(event: string, listener: Listener) {
      listeners.set(event, [...(listeners.get(event) ?? []), listener]);
      return this;
    },
    subscribe(topic: string) {
      subscribed.push(topic);
      return this;
    },
    publish(
      topic: string,
      payload: string,
      opts: { qos?: number; retain?: boolean } = {},
    ) {
      published.push({
        topic,
        payload,
        qos: opts.qos,
        retain: opts.retain,
      });
      return this;
    },
    end() {
      made.ended = true;
      return this;
    },
  };
}

export default { connect };
