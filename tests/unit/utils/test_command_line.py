"""Tests for slither/utils/command_line.py"""

import json

from slither.utils.command_line import config_defaults_as_json, output_config_to_markdown


def test_config_defaults_as_json_converts_enum_values():
    config = config_defaults_as_json()

    assert config["fail_on"] == "pedantic"
    assert config["exclude_dependencies"] is False
    assert config["sarif_input"] == "export.sarif"

    json.dumps(config)


def test_output_config_to_markdown(capsys):
    output_config_to_markdown()

    output = capsys.readouterr().out

    assert output.startswith("```json\n")
    assert output.endswith("\n```\n")
    assert '"exclude_dependencies": false' in output
    assert '"fail_on": "pedantic"' in output
