"""Where the page's sources are, and what a colour written out looks like."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

UI = ROOT / "ui"

#: A colour written out: `#rgb` and `#rrggbb`, and the two forms that carry an
#: alpha channel. Held to those four lengths so that an issue number, a
#: fragment or an id selector is not read as a colour.
HEX = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
