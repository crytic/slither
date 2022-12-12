import pytest
from solc_select import solc_select
from argparse import ArgumentTypeError


def skip_unsupported_platforms(ver: str):
    return pytest.mark.skipif(invalid_version(ver))


def invalid_version(ver: str) -> bool:
    """Wrapper function to check if the solc-version is valid

    The solc_select function raises and exception but for checks below,
    only a bool is needed.
    """
    try:
        solc_select.valid_version(ver)
        return False
    except ArgumentTypeError:
        return True
