from argparse import Namespace
import re

import pytest

from slither.__main__ import DEFAULT_EXCLUDE_TEST_PATHS, apply_exclude_test_filter


def test_apply_exclude_test_filter_adds_default_pattern():
    args = Namespace(exclude_test=True, filter_paths=[], include_paths=[])

    apply_exclude_test_filter(args)

    assert args.filter_paths == [DEFAULT_EXCLUDE_TEST_PATHS]


def test_apply_exclude_test_filter_preserves_existing_filters():
    args = Namespace(exclude_test=True, filter_paths=["vendor"], include_paths=[])

    apply_exclude_test_filter(args)

    assert args.filter_paths == ["vendor", DEFAULT_EXCLUDE_TEST_PATHS]


def test_apply_exclude_test_filter_rejects_include_paths():
    args = Namespace(exclude_test=True, filter_paths=[], include_paths=["contracts"])

    with pytest.raises(ValueError, match="--exclude-test cannot be used with --include-paths"):
        apply_exclude_test_filter(args)


def test_apply_exclude_test_filter_noops_when_disabled():
    args = Namespace(exclude_test=False, filter_paths=["vendor"], include_paths=[])

    apply_exclude_test_filter(args)

    assert args.filter_paths == ["vendor"]


@pytest.mark.parametrize(
    "path",
    [
        "/repo/test/Token.sol",
        "/repo/tests/Token.sol",
        "/repo/mock/Token.sol",
        "/repo/mocks/Token.sol",
        "/repo/contracts/TestToken.sol",
        "/repo/contracts/MockToken.sol",
    ],
)
def test_exclude_test_default_pattern_matches_test_and_mock_paths(path):
    assert re.search(DEFAULT_EXCLUDE_TEST_PATHS, path)


def test_exclude_test_default_pattern_keeps_regular_contract_paths():
    assert not re.search(DEFAULT_EXCLUDE_TEST_PATHS, "/repo/contracts/Token.sol")
