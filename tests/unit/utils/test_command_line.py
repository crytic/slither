"""Tests for slither/utils/command_line.py"""

import json

from slither.utils.command_line import (
    FailOnLevel,
    format_config_file_defaults,
    output_config_file_section,
)


def test_format_config_file_defaults_outputs_valid_json():
    result = format_config_file_defaults(
        {
            "detectors_to_run": "all",
            "fail_on": FailOnLevel.PEDANTIC,
            "json": None,
            "exclude_dependencies": False,
        }
    )

    assert json.loads(result) == {
        "detectors_to_run": "all",
        "fail_on": "pedantic",
        "json": None,
        "exclude_dependencies": False,
    }


def test_output_config_file_section_includes_supported_defaults(capsys):
    output_config_file_section()

    captured = capsys.readouterr()
    assert "### Configuration File" in captured.out
    assert "```json" in captured.out
    assert '"exclude_dependencies": false' in captured.out
    assert '"exclude_optimization": false' in captured.out
    assert '"sarif": null' in captured.out
    assert '"json-types": "detectors,printers"' in captured.out
