"""Tests for slither/utils/command_line.py"""

import argparse
import json
import os
import sys

import pytest

from slither.__main__ import parse_args
from slither.utils.command_line import DEFAULT_CONFIG_FILENAMES, positive_int, read_config_file


@pytest.fixture
def in_tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write_json(path, data):
    path.write_text(json.dumps(data))


def test_read_config_file_autodetects_config_json(in_tmp_cwd):
    _write_json(in_tmp_cwd / "slither.config.json", {"exclude_low": True})
    args = argparse.Namespace(config_file=None, exclude_low=False)
    read_config_file(args)
    assert args.config_file == "slither.config.json"
    assert args.exclude_low is True


def test_read_config_file_autodetects_conf_json(in_tmp_cwd):
    _write_json(in_tmp_cwd / "slither.conf.json", {"exclude_low": True})
    args = argparse.Namespace(config_file=None, exclude_low=False)
    read_config_file(args)
    assert args.config_file == "slither.conf.json"
    assert args.exclude_low is True


def test_read_config_file_prefers_config_over_conf(in_tmp_cwd):
    _write_json(in_tmp_cwd / "slither.config.json", {"exclude_low": True})
    _write_json(in_tmp_cwd / "slither.conf.json", {"exclude_low": False})
    args = argparse.Namespace(config_file=None, exclude_low=False)
    read_config_file(args)
    assert args.config_file == "slither.config.json"
    assert args.exclude_low is True


def test_read_config_file_no_default_present(in_tmp_cwd):
    args = argparse.Namespace(config_file=None)
    read_config_file(args)
    assert args.config_file is None


def test_default_filenames_constant():
    assert DEFAULT_CONFIG_FILENAMES == ("slither.config.json", "slither.conf.json")


def test_read_config_file_sets_cyclomatic_complexity_threshold(in_tmp_cwd):
    _write_json(in_tmp_cwd / "slither.config.json", {"cyclomatic_complexity_threshold": 15})
    args = argparse.Namespace(config_file=None, cyclomatic_complexity_threshold=11)
    read_config_file(args)
    assert args.cyclomatic_complexity_threshold == 15


def test_read_config_file_preserves_explicit_threshold(in_tmp_cwd):
    _write_json(in_tmp_cwd / "slither.config.json", {"cyclomatic_complexity_threshold": 15})
    args = argparse.Namespace(config_file=None, cyclomatic_complexity_threshold=12)
    read_config_file(args)
    assert args.cyclomatic_complexity_threshold == 12


@pytest.mark.parametrize(("value", "expected"), [("1", 1), (1, 1), ("15", 15)])
def test_positive_int_accepts_positive_integers(value, expected):
    assert positive_int(value) == expected


@pytest.mark.parametrize("value", [0, -1, "0", "-1", "1.5", 1.5, True, None])
def test_positive_int_rejects_invalid_values(value):
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(value)


def test_parse_args_accepts_cyclomatic_complexity_threshold(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["slither", "target.sol", "--cyclomatic-complexity-threshold", "15"],
    )
    args = parse_args([], [])
    assert args.cyclomatic_complexity_threshold == 15


def test_parse_args_reads_cyclomatic_complexity_threshold_from_config(in_tmp_cwd, monkeypatch):
    _write_json(in_tmp_cwd / "slither.config.json", {"cyclomatic_complexity_threshold": 15})
    monkeypatch.setattr(sys, "argv", ["slither", "target.sol"])
    args = parse_args([], [])
    assert args.cyclomatic_complexity_threshold == 15


def test_cli_threshold_overrides_config_threshold(in_tmp_cwd, monkeypatch):
    _write_json(in_tmp_cwd / "slither.config.json", {"cyclomatic_complexity_threshold": 15})
    monkeypatch.setattr(
        sys,
        "argv",
        ["slither", "target.sol", "--cyclomatic-complexity-threshold", "12"],
    )
    args = parse_args([], [])
    assert args.cyclomatic_complexity_threshold == 12


def test_parse_args_rejects_non_positive_config_threshold(in_tmp_cwd, monkeypatch):
    _write_json(in_tmp_cwd / "slither.config.json", {"cyclomatic_complexity_threshold": 0})
    monkeypatch.setattr(sys, "argv", ["slither", "target.sol"])
    with pytest.raises(SystemExit):
        parse_args([], [])
