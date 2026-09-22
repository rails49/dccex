# Where this package came from

`src/dccex_usb` was written in
[`rails49/control`](https://github.com/rails49/control) and moved here by
rails49/dccex#11, under #10, because the app is about a command station and
nothing in `control` is.

- **Repository:** `rails49/control`
- **Commit:** `deee7b6f54d0215f4e02c128e60f50322fd0978c`
- **Copied:** 2026-09-22

**`control` deleted its side on 2026-09-22** (rails49/control#567). This file
is provenance now and not a constraint: nothing has to stay diffable, and a
defect here is fixed here
([ADR-0003](../docs/adr/0003-the-copy-has-no-source-and-station-py-is-ours.md)).

The file names are `control`'s because that is where the code was written. A
diff against the commit above still runs — deleting a file on `main` does not
take it out of history — and what it shows is the bus coming out:

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

These are the differences the move itself made. Anything beyond them is this
repository's own work, done since.

`framing.py` came across untouched. `station.py` differed in two lines: the
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
