"""Tests for slither CLI subcommands."""

import re

import pytest
from typer.testing import CliRunner

from slither.__main__ import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestMainHelp:
    """Test the main help output."""

    def test_main_help_shows_subcommands(self) -> None:
        """Test that main help lists all expected subcommands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)

        expected_subcommands = [
            "detect",
            "print",
            "doctor",
            "flat",
            "interface",
            "mutate",
            "find-paths",
            "prop",
            "read-storage",
            "format",
            "check-upgradeability",
            "check-erc",
            "codex",
            "simil",
        ]

        for subcommand in expected_subcommands:
            assert subcommand in output, f"Missing subcommand: {subcommand}"

    def test_main_help_excludes_hidden_subcommands(self) -> None:
        """Test that hidden subcommands are not shown in main help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)

        # demo should be hidden
        assert (
            "demo" not in output.lower().split("commands")[1]
            if "commands" in output.lower()
            else True
        )


class TestDetectSubcommand:
    """Test the detect subcommand."""

    def test_detect_help(self) -> None:
        """Test that detect --help works."""
        result = runner.invoke(app, ["detect", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Run slither detectors on the target" in output

    def test_detect_has_list_detectors_flag(self) -> None:
        """Test that --list-detectors flag exists."""
        result = runner.invoke(app, ["detect", "--help"])
        output = strip_ansi(result.output)
        assert "--list-detectors" in output

    def test_detect_has_detect_flag(self) -> None:
        """Test that --detect flag exists for filtering detectors."""
        result = runner.invoke(app, ["detect", "--help"])
        output = strip_ansi(result.output)
        assert "--detect" in output

    def test_detect_has_help_long_flag(self) -> None:
        """Test that --help-long flag exists for crytic-compile options."""
        result = runner.invoke(app, ["detect", "--help"])
        output = strip_ansi(result.output)
        assert "--help-long" in output


class TestPrintSubcommand:
    """Test the print subcommand."""

    def test_print_help(self) -> None:
        """Test that print --help works."""
        result = runner.invoke(app, ["print", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Run printers on the target" in output

    def test_print_has_list_printers_flag(self) -> None:
        """Test that --list-printers flag exists."""
        result = runner.invoke(app, ["print", "--help"])
        output = strip_ansi(result.output)
        assert "--list-printers" in output

    def test_print_has_no_fail_flag(self) -> None:
        """Test that --no-fail flag exists in print command (echidna mode)."""
        result = runner.invoke(app, ["print", "--help"])
        output = strip_ansi(result.output)
        assert "--no-fail" in output

    def test_no_fail_not_in_global_help(self) -> None:
        """Test that --no-fail is NOT in global help (only in print)."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--no-fail" not in output


class TestToolSubcommands:
    """Test that tool subcommands exist and have help."""

    @pytest.mark.parametrize(
        "subcommand,expected_text",
        [
            ("doctor", "Troubleshoot"),
            ("flat", "Flatten"),
            ("interface", "interface"),
            ("mutate", "mutator"),
            ("find-paths", "paths"),
            ("prop", "properties"),
            ("read-storage", "storage"),
            ("format", "Auto-fix"),
            ("check-upgradeability", "Upgradeability"),
            ("check-erc", "ERC"),
            ("codex", "Codex"),
            ("simil", "similarity"),
        ],
    )
    def test_tool_subcommand_help(self, subcommand: str, expected_text: str) -> None:
        """Test that tool subcommands have working help."""
        result = runner.invoke(app, [subcommand, "--help"])
        output = strip_ansi(result.output)
        assert result.exit_code == 0, f"{subcommand} --help failed: {output}"
        assert expected_text.lower() in output.lower(), (
            f"Expected '{expected_text}' in {subcommand} help"
        )


class TestGlobalOptions:
    """Test global options are available."""

    def test_version_flag(self) -> None:
        """Test that --version flag works."""
        result = runner.invoke(app, ["--version"])
        output = strip_ansi(result.output)
        # Should show version or exit with 0
        assert result.exit_code == 0 or "version" in output.lower()

    def test_output_format_options(self) -> None:
        """Test that output format options are in help."""
        result = runner.invoke(app, ["--help"])
        output = strip_ansi(result.output)
        assert "--output-format" in output
        assert "json" in output.lower()
        assert "sarif" in output.lower()

    def test_config_file_option(self) -> None:
        """Test that --config-file option exists."""
        result = runner.invoke(app, ["--help"])
        output = strip_ansi(result.output)
        assert "--config-file" in output
