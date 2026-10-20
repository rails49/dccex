# ADR-0025 — the mirror reaches the station through the host's `/dev`

- **Status:** accepted, 2026-10-20
- **Ticket:** rails49/dccex#312

## Context

The box overlay mapped the station with a compose `devices:` entry. Docker
reads that entry when it starts the container. On 2026-10-18 a deploy
recreated the mirror while the station was unplugged. Docker refused the
entry, and the container stayed in `Created`. `restart: unless-stopped` does
not apply to a container that never started, so plugging the station in did
nothing. 2560 was closed for two days.

The app needs no change. It treats a missing device as an outage and retries
(mirror README, "While the device is away").

## Decision

**d.1** The mirror has no `devices:` entry. It is given
`device_cgroup_rules: ["c 188:* rmw"]` and the host's `/dev` mounted
read-only at `/host/dev`. 188 is the ttyUSB major. The CH340 on the station
is a ttyUSB.

**d.2** The app opens the `by-id` path under `/host/dev`. The `by-id` links
are relative (`../../ttyUSBn`), so they resolve inside the mount. A device
plugged in after the start appears in the mount, under whichever `ttyUSBn` it
gets.

**d.3** `DCCEX_STATION_DEVICE` stays the host path. The image's own default
device, `/dev/dccex`, is unchanged; the box overlay names the device instead.

## Consequences

- The mirror starts with the station unplugged, and opens it when it appears.
- The container can see every node in the host's `/dev`. It can open only
  ttyUSB devices beyond Docker's defaults.
- A station that comes up as ttyACM (major 166) needs a second rule.

## Considered

- **Bind host `/dev` over the container's `/dev`.** The container loses its
  own `/dev` and gets write access to the host's device tree.
- **A host udev rule that restarts the mirror when the station appears.** It
  lives in `installation`, and a deploy with the station unplugged still
  leaves the mirror not running.
