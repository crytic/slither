import os
import pathlib
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from inspect import getsourcefile
from typing import Optional

import pytest
from solc_select import solc_select
from slither import Slither

# Directory of currently executing script. Will be used as basis for temporary file names.
SCRIPT_DIR = pathlib.Path(getsourcefile(lambda: 0)).parent


@contextmanager
def _select_solc_version(version: Optional[str]):
    """Selects solc version to use for running tests.

    If no version is provided, latest is used."""
    # If no solc_version selected just use the latest avail
    if not version:
        # This sorts the versions numerically
        vers = sorted(
            map(
                lambda x: (int(x[0]), int(x[1]), int(x[2])),
                map(lambda x: x.split(".", 3), solc_select.installed_versions()),
            )
        )
        ver = list(vers)[-1]
        version = ".".join(map(str, ver))
    env = dict(os.environ)
    env_restore = dict(env)
    env["SOLC_VERSION"] = version
    os.environ.clear()
    os.environ.update(env)

    yield version

    os.environ.clear()
    os.environ.update(env_restore)


@pytest.fixture(name="select_solc_version")
def fixture_select_solc_version():
    return _select_solc_version


@pytest.fixture
def slither_from_source(select_solc_version):
    @contextmanager
    def _slither_from_source(source_code: str, solc_version: Optional[str] = None):
        """Yields a Slither instance using source_code string and solc_version

        Creates a temporary file and changes the solc-version temporary to solc_version.
        """
        fname = ""
        try:
            with NamedTemporaryFile(dir=SCRIPT_DIR, mode="w", suffix=".sol", delete=False) as f:
                fname = f.name
                f.write(source_code)
            with select_solc_version(solc_version):
                yield Slither(fname)
        finally:
            pathlib.Path(fname).unlink()

    return _slither_from_source
