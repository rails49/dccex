/**
 * The **bus** as the page reaches it, driven against a broker with nothing
 * behind it.
 *
 * What a payload *means* is the readings module's and is run through it
 * (`tests/ui/test_readings.py`); what is asserted here is the connection —
 * where it is opened, which row it subscribes to, what a press publishes and
 * what an outage does to the reading — none of which a Python gate with no
 * broker can reach (`ui/test/support/broker.ts`, ADR-0017).
 */

import { beforeEach, expect, test } from "vitest";

import {
  Bus,
  MQTT_PATH,
  POWER_STATE,
  POWER_WANTED,
  RECONNECT_MS,
} from "../src/bus.js";
import { UNREACHABLE, type Layout } from "../src/readings.js";
import { type Dialled, dialled, forgotten } from "./support/broker.js";

beforeEach(forgotten);

/** A row `layout` publishes, and one this page cannot read. */
const HOT = '{"power":"on"}';
const COLD = '{"power":"off"}';
const HALTED = '{"power":"stopped"}';
const NONSENSE = "{";

/** A bus open on the broker, the connection it made, and every reading it has
 *  handed up. */
function opened(): { bus: Bus; broker: Dialled; reported: Layout[] } {
  const reported: Layout[] = [];
  const bus = new Bus((layout) => {
    reported.push(layout);
  });
  bus.open();
  const broker = dialled.at(-1);
  if (broker === undefined) {
    throw new Error("the bus reached no broker");
  }
  return { bus, broker, reported };
}

/** The latest reading the bus handed up. */
function latest(reported: Layout[]): Layout {
  const last = reported.at(-1);
  if (last === undefined) {
    throw new Error("the bus handed up no reading");
  }
  return last;
}

test("the broker is on the page's own origin, under the prefix the door strips", () => {
  const { broker } = opened();
  expect(broker.url).toBe(`ws://${window.location.host}${MQTT_PATH}`);
});

test("the page reaches one broker and dials again on its own", () => {
  const { bus } = opened();
  bus.open();
  expect(dialled).toHaveLength(1);
  expect(dialled[0]?.options.reconnectPeriod).toBe(RECONNECT_MS);
});

test("it subscribes to the power row and to nothing else", () => {
  const { broker } = opened();
  broker.connects();
  expect(broker.subscribed).toEqual([POWER_STATE]);
});

test("what layout reports on the power row is what the page reads", () => {
  const { broker, reported } = opened();
  broker.connects();
  broker.says(POWER_STATE, HOT);
  expect(latest(reported)).toEqual({ connected: true, power: "on" });
  broker.says(POWER_STATE, COLD);
  expect(latest(reported)).toEqual({ connected: true, power: "off" });
  broker.says(POWER_STATE, HALTED);
  expect(latest(reported)).toEqual({ connected: true, power: "stopped" });
});

test("a payload the page cannot read reads as off", () => {
  const { broker, reported } = opened();
  broker.connects();
  broker.says(POWER_STATE, NONSENSE);
  expect(latest(reported)).toEqual({ connected: true, power: "off" });
});

test("a row that is not the power row is not read as the power", () => {
  const { broker, reported } = opened();
  broker.connects();
  broker.says(POWER_STATE, HOT);
  broker.says("tc49/layout/state/run", COLD);
  expect(latest(reported)).toEqual({ connected: true, power: "on" });
});

test("a connection that has not been made yet is a bus that is away", () => {
  const { reported } = opened();
  expect(reported).toEqual([]);
});

test("a connection that goes takes the row with it", () => {
  const { broker, reported } = opened();
  broker.connects();
  broker.says(POWER_STATE, HOT);
  broker.closes();
  expect(latest(reported)).toEqual(UNREACHABLE);
});

test("a press publishes what it asks for, at QoS 0 and not retained", () => {
  const { bus, broker } = opened();
  broker.connects();
  bus.wants("off");
  expect(broker.published).toEqual([
    { topic: POWER_WANTED, payload: COLD, qos: 0, retain: false },
  ]);
});

test("a press asks for one row and not a second", () => {
  const { bus, broker } = opened();
  broker.connects();
  bus.wants("on");
  bus.wants("on");
  expect(broker.published.map((said) => said.payload)).toEqual([HOT, HOT]);
});

test("a bus nobody opened publishes nothing", () => {
  const bus = new Bus(() => {
    throw new Error("a bus nobody opened reported something");
  });
  bus.wants("on");
  expect(dialled).toEqual([]);
});

test("letting the bus go ends the connection and says the bus is away", () => {
  const { bus, broker, reported } = opened();
  broker.connects();
  broker.says(POWER_STATE, HOT);
  bus.close();
  expect(broker.ended).toBe(true);
  expect(latest(reported)).toEqual(UNREACHABLE);
});
