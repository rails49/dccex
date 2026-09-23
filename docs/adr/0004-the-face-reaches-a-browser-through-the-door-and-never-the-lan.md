# ADR-0004 — the face reaches a browser through the door, and never the LAN

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#40, under #10
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (the
  mirror leaves the bus for a face),
  [ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)
  (what a UI may talk to, and what a private face is),
  [control ADR-0042](https://github.com/rails49/control/blob/main/docs/adr/0042-the-edge-terminates-tls-and-the-lan-is-the-trust-boundary.md)
  (the edge terminates TLS and the LAN is the trust boundary)

## Context

The face is written (#12). It answers on `--face-port` and nothing published
it: no label, no record, no router — unpublished rather than served somewhere
else, which is why nothing about its address moves now.

Its one caller is the page, and a page is a browser. That is what ADR-0042
does not answer. ADR-0042 says the edge terminates TLS and the LAN is the
trust boundary, and it settles the mirror's port: JMRI, a hand-held throttle
and the translator are programs on the wifi holding a serial conversation, and
what limits their reach is the network they are on. A browser is not one of
them. It is held to the origin of the page it loaded, it will not fetch plain
HTTP from a page served over `https`, and it will not open a `ws://` stream
from one either. So "the LAN is the trust boundary" cannot be the answer to
how a page reaches this app: on the LAN there is nothing for a browser to
reach the face *as*.

The box already answers that question for everything else it serves. It has a
door: one host, one router per thing a browser reaches, and a certificate
issued per router through ACME DNS-01. The door holds no wildcard, so a label
is a record somebody adds, and the box's page lists a UI only if the label is
in `BOX_UIS` in `/etc/rails49/box.env`, which is root-owned and edited by
hand.

Two shapes were open. A label of the face's own is a second origin, a second
certificate and a page that is cross-origin to the app it is about — every
fetch and the stream negotiated across origins, for an interface that is
private to one page. The face on the LAN raw is worse: the page is served over
`https` and cannot speak to it at all, and an app's private interface would be
sitting on a network that carries no authentication on purpose.

## Decision

**d.1** A browser reaches the face through the door and never the LAN. The
face's port is the door's to reach on the box's own network: it is not
published to the LAN, and the face is given no label and no certificate of its
own.

**d.2** The page and the face are one origin — the box's `dccex` label — and
two routers on it. The page's takes the host rule and outranks the face's: the
origin is the page's, and the face claims nothing on it but the path prefix
`/dccex-usb`, which the door strips before the mirror sees it. Under that
prefix the face answers and nothing else does; everything else on the label is
the page's, including anything the two rules are ever both written for. The
face's address is that prefix and has never been anything else, so no UI
ticket has to know which era it is in.

**d.3** The stream the UI's monitor rides is that same router, so a browser on
the page's origin opens it as `wss://` on the origin it is already on. There
is no second certificate anywhere, and nothing about the stream is a name or a
port of its own.

**d.4** A page from another origin is refused by the face itself, with a
status and a sentence like every other refusal (`face.py`, `elsewhere`). The
host is what is compared and not the scheme: the door terminates TLS, so a
page served over `https` asks a face spoken to over plain HTTP, and what the
two share is the label. A request with no origin on it is not a page from
another one — an origin is what a browser attaches, and what limits a caller
that is not a browser is d.1 and ADR-0042.

**d.5** Only the containers a browser reaches carry door labels. The mirror
goes on publishing 2560 raw, with no router and no certificate over it: it is
a serial conversation between programs on the wifi, ADR-0042 is what limits
it, and putting it behind the door would put a certificate between a throttle
and the command station for nobody's benefit.

**d.6** The steps on the box are not code and are not in this repository. An
`A` record for the `dccex` label, because the door holds no wildcard;
`dccex` in `BOX_UIS` in `/etc/rails49/box.env`, so the box's page links it.
The stack that carries the labels above is #15's.

## Consequences

- Both servers go on binding every interface inside the container, which is
  unchanged. What keeps the face off the LAN is that its port is not
  published, and what keeps it answering is that the door is on the box's own
  network.
- The gate cannot check any of this: there is no door in the suite and no box.
  What is held here is the face's side of it — the origin refusal, and that
  the path the face answers is `/releases` with the prefix already off.
- The face's refusals gain a status. `403` joins the `404`, `405`, `502`,
  `400`, `413` and `431` that were there, and carries its sentence in the same
  `reason` field.
- A page at the label reaches two containers over one certificate, so the UI
  is written against one origin and the stream needs nothing of its own. What
  it costs is that the door is now between the page and the app: a door that
  is down is a UI that is down, which is already true of every other UI on the
  box.
- Nothing here reaches the LAN's side of the mirror. 2560 is what it was, and
  this decision does not touch it.
