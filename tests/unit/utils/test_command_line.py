"""Tests for slither/utils/command_line.py"""

import argparse
import json
import os

import pytest

from slither.utils.command_line import DEFAULT_CONFIG_FILENAMES, read_config_file


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
