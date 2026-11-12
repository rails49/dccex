"""The box's files through `docker compose config`, under each value of
`BOX_DOMAIN` a box can have (#379).

Set to a name is a box with a certificate, which loads `compose.https.yaml`
too. Set and empty is a box with no certificate, which leaves it out. Unset is
a box started without its declaration, and is refused (installation#53 d.1).

`config` needs the docker CLI and no daemon. It carries the `docker` marker,
so it runs in the workflow's docker job and the gate does not collect it.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.deploy.test_stack import TWINS
from tests.ui.paths import ROOT
from tests.ui.test_compose_serves import environment

pytestmark = pytest.mark.docker


def config(
    *argument: str, env_file: str = os.devnull, https: bool = False, **set_here: str
) -> subprocess.CompletedProcess[str]:
    """`docker compose config` over the box's files, with no `.env` read unless
    `env_file` names one. `https` adds `compose.https.yaml`."""
    if shutil.which("docker") is None:
        if os.environ.get("CI"):
            pytest.fail("this job requires docker on the path")
        pytest.skip("no docker on the path")
    return subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            env_file,
            "-f",
            "compose.yaml",
            "-f",
            "compose.box.yaml",
            *(("-f", "compose.https.yaml") if https else ()),
            "config",
            *(argument or ("--quiet",)),
        ],
        cwd=ROOT,
        env=environment(**set_here),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("https", [False, True])
@pytest.mark.parametrize("domain", ["", "example.org"])
def test_a_box_with_or_without_a_certificate_is_admitted(
    domain: str, https: bool
) -> None:
    done = config(https=https, BOX_DOMAIN=domain)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("https", [False, True])
def test_a_box_with_no_declaration_is_refused(https: bool) -> None:
    done = config(https=https)
    assert done.returncode != 0
    assert "/etc/rails49/box.env" in done.stderr


def labels(done: subprocess.CompletedProcess[str]) -> dict[str, str]:
    """Every service's labels in one `config --format json`, merged."""
    assert done.returncode == 0, done.stderr
    merged: dict[str, str] = {}
    for service in json.loads(done.stdout)["services"].values():
        merged |= service.get("labels") or {}
    return merged


def test_only_the_https_file_names_websecure_or_a_resolver() -> None:
    """Without `compose.https.yaml` no label names `websecure` or a
    certificate resolver. With it, each router on `websecure` is there with
    the box's host (#396)."""
    without = labels(config("--format", "json", BOX_DOMAIN=""))
    named = [
        f"{key}={value}"
        for key, value in without.items()
        if "websecure" in value or "certresolver" in key
    ]
    assert named == []
    with_it = labels(config("--format", "json", https=True, BOX_DOMAIN="example.org"))
    for router in TWINS:
        prefix = f"traefik.http.routers.{router}"
        assert with_it[f"{prefix}.entrypoints"] == "websecure", router
        assert with_it[f"{prefix}.tls.certresolver"] == "le", router
        assert with_it[f"{prefix}.rule"].startswith("Host(`dccex.example.org`)")


@pytest.mark.parametrize("domain", ["", "example.org"])
def test_a_box_publishes_the_page_on_no_port(domain: str) -> None:
    """On a box the page is reached through the door alone, on HTTPS and on
    its UI port (rails49/.github#69 d.3, #383). The clean clone's published
    port is `test_compose_serves.py`'s."""
    done = config("--format", "json", https=bool(domain), BOX_DOMAIN=domain)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["services"]["web"].get("ports", []) == []


def test_the_settings_file_moves_the_device_and_the_store(tmp_path: Path) -> None:
    """`/etc/rails49/dccex.env` holds what differs from box to box
    (installation#65 d.14), and both apps read the store it names."""
    settings = tmp_path / "dccex.env"
    settings.write_text(
        "DCCEX_STATION_DEVICE=/dev/serial/by-id/a-station\n"
        "DCCEX_STORE_URL=http://elsewhere:8765\n"
    )
    done = config(
        "--format",
        "json",
        env_file=str(settings),
        https=True,
        BOX_DOMAIN="example.org",
    )
    assert done.returncode == 0, done.stderr
    services = json.loads(done.stdout)["services"]
    mirror = services["mirror"]["command"]
    assert mirror[mirror.index("--device") + 1] == "/host/dev/serial/by-id/a-station"
    assert mirror[mirror.index("--store") + 1] == "http://elsewhere:8765"
    translator = services["translator"]["command"]
    assert translator[translator.index("--store") + 1] == "http://elsewhere:8765"
