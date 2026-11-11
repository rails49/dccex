"""The box's two files through `docker compose config`, under each value of
`BOX_DOMAIN` a box can have (#379).

Set to a name is a box with a certificate. Set and empty is a box with no
certificate. Unset is a box started without its declaration, and is refused
(installation#53 d.1).

`config` needs the docker CLI and no daemon. It carries the `docker` marker,
so it runs in the workflow's docker job and the gate does not collect it.
"""

import os
import shutil
import subprocess

import pytest

from tests.ui.paths import ROOT
from tests.ui.test_compose_serves import environment

pytestmark = pytest.mark.docker


def config(**set_here: str) -> subprocess.CompletedProcess[str]:
    """`docker compose config` over both files, with no `.env` read."""
    if shutil.which("docker") is None:
        if os.environ.get("CI"):
            pytest.fail("this job requires docker on the path")
        pytest.skip("no docker on the path")
    return subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            os.devnull,
            "-f",
            "compose.yaml",
            "-f",
            "compose.box.yaml",
            "config",
            "--quiet",
        ],
        cwd=ROOT,
        env=environment(**set_here),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("domain", ["", "example.org"])
def test_a_box_with_or_without_a_certificate_is_admitted(domain: str) -> None:
    done = config(BOX_DOMAIN=domain)
    assert done.returncode == 0, done.stderr


def test_a_box_with_no_declaration_is_refused() -> None:
    done = config()
    assert done.returncode != 0
    assert "/etc/rails49/box.env" in done.stderr
