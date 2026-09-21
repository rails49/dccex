#!/usr/bin/env bash
set -euo pipefail

# The gate: what CI runs on every pull request, and what you can run here
# before you push. Nothing to check yet -- the repository is a README and a
# prototype page. Grow this as dccex-usb, dccex and the UI land.
#
# Tests that need the serial cable, a local service or a secret must skip
# themselves when CI is set; that is the whole contract between this script
# and the workflow.

exit 0
