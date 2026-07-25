import argparse

from slither.utils.command_line import (
    defaults_flag_in_config,
    output_config_json,
    read_config_file,
)


def test_output_config_json_serializes_defaults() -> None:
    config = output_config_json()

    assert config["fail_on"] == "pedantic"
    assert config["json-types"] == "detectors,printers"
    assert config.keys() == defaults_flag_in_config.keys()


def test_read_config_file_supports_hyphenated_keys(tmp_path) -> None:
    config_file = tmp_path / "slither.config.json"
    config_file.write_text('{"json-types": "detectors"}', encoding="utf8")
    args = argparse.Namespace(
        config_file=str(config_file),
        json_types=defaults_flag_in_config["json-types"],
    )

    read_config_file(args)

    assert args.json_types == "detectors"


def test_read_config_file_preserves_cli_override_for_hyphenated_keys(tmp_path) -> None:
    config_file = tmp_path / "slither.config.json"
    config_file.write_text('{"json-types": "detectors"}', encoding="utf8")
    args = argparse.Namespace(config_file=str(config_file), json_types="printers")

    read_config_file(args)

    assert args.json_types == "printers"


def test_read_config_file_accepts_supported_key_absent_from_namespace(tmp_path) -> None:
    config_file = tmp_path / "slither.config.json"
    config_file.write_text('{"codex": true}', encoding="utf8")
    args = argparse.Namespace(config_file=str(config_file))

    read_config_file(args)

    assert args.codex is True
