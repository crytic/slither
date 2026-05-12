"""Unit tests for slither.utils.command_line."""

from slither.utils.command_line import (
    FailOnLevel,
    _config_default_to_markdown,
    output_config_file_options,
)


def test_config_default_to_markdown_handles_json_values():
    assert _config_default_to_markdown(False) == "false"
    assert _config_default_to_markdown(None) == "null"
    assert _config_default_to_markdown("all") == '"all"'
    assert _config_default_to_markdown(FailOnLevel.PEDANTIC) == '"pedantic"'


def test_output_config_file_options_includes_known_slither_keys(capsys):
    output_config_file_options()

    output = capsys.readouterr().out
    assert "| Key | Default |" in output
    assert "| `exclude_dependencies` | `false` |" in output
    assert "| `exclude_optimization` | `false` |" in output
    assert "| `sarif` | `null` |" in output
    assert "| `compile_force_framework` | `null` |" in output
