import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

import pytest
from slither import Slither
from solc_select import solc_select
from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson


@contextmanager
def _select_solc_version(version: Optional[str]):
    """Selects solc version to use for running tests.
    If no version is provided, latest is used."""
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
def slither_from_dir(select_solc_version):
    @contextmanager
    def _slither_from_dir(directory: str, solc_version: Optional[str] = None):
        """Yields a Slither instance using solidity files in directory and solc_version.
        Temporarily changes the solc-version temporary to solc_version.
        """
        standard_json = SolcStandardJson()
        for source_file in Path(directory).rglob("*.sol"):
            standard_json.add_source_file(Path(source_file).as_posix())
        with select_solc_version(solc_version):
            compilation = CryticCompile(standard_json)
            yield Slither(compilation)

    return _slither_from_dir
