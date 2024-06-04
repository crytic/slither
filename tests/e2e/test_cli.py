import sys
import tempfile
import pytest

from slither.__main__ import main_impl


def test_cli_exit_on_invalid_compilation_file(caplog):

    with tempfile.NamedTemporaryFile("w") as f:
        f.write("pragma solidity ^0.10000.0;")

        sys.argv = ["slither", f.name]
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            main_impl([], [])

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    assert caplog.record_tuples[0] == ("Slither", 40, "Unable to compile all targets.")
