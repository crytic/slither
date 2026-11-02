"""Tests for slither-check-upgradeability CLI wiring."""

import json
import sys

import pytest

from slither.tools.upgradeability.__main__ import _get_checks, parse_args
from slither.utils.command_line import read_config_file


@pytest.fixture
def in_tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _invoke_parse_args(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", argv)
    return parse_args(_get_checks())


def test_parser_exposes_config_file(monkeypatch):
    args = _invoke_parse_args(
        monkeypatch,
        ["slither-check-upgradeability", "x.sol", "Foo", "--config-file", "custom.json"],
    )
    assert args.config_file == "custom.json"


def test_parser_config_file_defaults_to_none(monkeypatch):
    args = _invoke_parse_args(monkeypatch, ["slither-check-upgradeability", "x.sol", "Foo"])
    assert args.config_file is None


def test_read_config_file_autodetects_default(in_tmp_cwd, monkeypatch):
    (in_tmp_cwd / "slither.config.json").write_text(json.dumps({"exclude_low": True}))
    args = _invoke_parse_args(monkeypatch, ["slither-check-upgradeability", "x.sol", "Foo"])
    assert args.exclude_low is False
    read_config_file(args)
    assert args.config_file == "slither.config.json"
    assert args.exclude_low is True


def test_read_config_file_applies_solc_remaps(in_tmp_cwd, monkeypatch):
    (in_tmp_cwd / "slither.config.json").write_text(
        json.dumps({"solc_remaps": "@openzeppelin=node_modules/@openzeppelin"})
    )
    args = _invoke_parse_args(monkeypatch, ["slither-check-upgradeability", "x.sol", "Foo"])
    read_config_file(args)
    assert args.solc_remaps == "@openzeppelin=node_modules/@openzeppelin"
