# Where this package came from

`src/dccex_usb` is a copy. It was written in
[`rails49/control`](https://github.com/rails49/control) and moved here by
rails49/dccex#11, under #10, because the app is about a command station and
nothing in `control` is.

- **Repository:** `rails49/control`
- **Commit:** `deee7b6f54d0215f4e02c128e60f50322fd0978c`
- **Copied:** 2026-09-22

The copy keeps `control`'s file names so that a diff against that commit shows
the bus coming out and, since `control`'s copy was deleted, the fixes listed
under *What has been fixed here* below. What to run to see it:

```
git clone https://github.com/rails49/control /tmp/control
git -C /tmp/control checkout deee7b6f54d0215f4e02c128e60f50322fd0978c
diff -u /tmp/control/src/tc49/dccex_usb/station.py src/dccex_usb/station.py
```

## What came from where

| In `control` at `deee7b6` | Here |
| --- | --- |
| `src/tc49/dccex_usb/framing.py` | `src/dccex_usb/framing.py` |
| `src/tc49/dccex_usb/station.py` | `src/dccex_usb/station.py` |
| `src/tc49/dccex_usb/firmware.py` | `src/dccex_usb/firmware.py` |
| `src/tc49/dccex_usb/__init__.py` | `src/dccex_usb/__init__.py` |
| `src/tc49/dccex_usb/__main__.py` | `src/dccex_usb/__main__.py` |
| `tests/dccex_usb/*` | `tests/dccex_usb/*` |
| `docs/dccex_usb/README.md` | `docs/dccex_usb/README.md` |

## What the copy changed

This is what the copy landed as. What has changed since is the section under
it.

`framing.py` came across untouched. `station.py` differs in two lines: the
import it spends on `framing`, and the docstring on `Station.run`, where
`python -m tc49.dccex_usb` became `python -m dccex_usb` — the package cannot
be run under the old path, so leaving it would have shipped a false statement.
The rest is the bus being cut, which is
[ADR-0001](../docs/adr/0001-the-mirror-leaves-the-bus-for-a-face.md):

- `__main__.py` is not a copy. It was built on `tc49.lib.startup.command_line`,
  which did not come, so it was rewritten around the same arguments less
  `--broker` and `--id`.
- `firmware.py` lost the two topics, the payload reader, the subscription, the
  bus it was constructed on and the row it refused on. A refusal is logged now
  and goes nowhere else.
- The tests came across with it. `test_firmware.py` lost the cases that were
  about the payload and the row; `test_main.py` was adapted with `__main__.py`.

## What has been fixed here

`rails49/control#567` merged on 2026-09-22 and deleted `src/tc49/dccex_usb`
and `tests/dccex_usb/`. There is no copy there any more, so a defect in this
package is fixed here rather than upstream and re-copied
([ADR-0003](../docs/adr/0003-the-copy-has-no-original-left-and-is-fixed-here.md),
superseding ADR-0002). The commit above still says where the package came
from and the diff still runs; what it no longer says is that the two files
are the same. Each change made here since is listed, newest last, so a reader
sorting the diff is told which side of it is ours:

- **#23** — `station.py` and the tests for it: client streams were closed
  where the write buffer may never drain, which hung `Station.close()` and
  held the device with it. They are aborted at all three sites now, as the
  cut-off already did, and three tests hold that shut.
- **#24** — `station.py` and the tests for it: a client's message being
  written when the device was let go — the flash handover, or a cable pulled
  — was parked on a descriptor closed underneath it and never woken, so it
  held the write lock for the life of the process and every client's message
  queued behind it. The descriptor is taken off the loop and the parked write
  woken with a private `DeviceGone` before it is closed; the message is
  dropped like anything else sent into an outage. Two tests hold it.
- **#26** — `station.py` and the tests for it: a handover that ended on a
  station which had been closed meanwhile started a fresh watcher, which
  reopens and holds the device of a mirror nobody is using — reachable on a
  signal mid-flash, and a leak rather than a stuck device only because the
  event loop's task cleanup happened to cancel it. The station records that it
  has been closed, and the handover asks before it takes the device back. One
  test holds it.
- **#34** — `station.py` and the tests for it: #24's fix woke a parked write by
  handing it an exception, and passed over one the selector had already woken.
  That write resumed with nothing to tell it the device had gone, so it took
  the closed number for its own — unregistering a writer from it and writing a
  client's command bytes into whatever the OS had handed it to next, while
  reporting the message sent. The open device is an object of its own now,
  `Device`: it holds the descriptor, the write lock and whatever is parked, no
  `os.read`, `os.write`, `os.close` or loop registration happens outside it,
  and a write asks it whether the number is still the device's rather than
  inferring that from how it was woken. `Station` lost three fields with it.
  One test holds it, and it goes red against the shape #24 left.
- **#12** — `firmware.py`, in its prose alone: three sentences said the flash
  would have a caller once the face was written. The face is written and
  answers what releases the source carries; what will ask for a flash is the
  route #13 adds to it, so they say that instead. No behaviour, no numbers,
  and nothing in the file's code moved.
