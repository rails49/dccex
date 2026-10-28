# A stopped translator

The translator sets no MQTT last will, and nothing publishes for it once its
process has stopped. Its retained `device/link/<id>` and `device/track` rows
keep what they last said.

## Why this is out of scope

The translator has not stopped on its own in use. It stops when a person
restarts its container, redeploys or reboots the box, and that person knows
the railroad is not being driven while it is down.

A crash is restarted by Docker within seconds (`restart: unless-stopped` in
`compose.box.yaml`). The new process publishes its opening rows, the link
`down` and the track dark with a reason, so the stale rows last only that long.

A will would not cover the common case anyway. `docker stop` ends the process
with a clean disconnect, and the broker discards the will on a clean
disconnect. It would also need `control`'s `MqttBus` to take a will, which it
does not: the bus connects from its constructor.

Reopen this if the translator stops unattended and the stale rows cause
trouble.

## Prior requests

- #354: "translator: a stopped translator reads as a dark supply"
