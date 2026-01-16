"""Tests for slither standalone CLI entry points."""

import pytest
from typer.testing import CliRunner


class TestStandaloneEntryPoints:
    """Test that standalone entry points work correctly.

    Each tool has a standalone entry point (e.g., slither-flat) that should
    work independently of the main slither command.
    """

    @pytest.mark.parametrize(
        "module_path,app_name,expected_help_text",
        [
            ("slither.tools.flattening.__main__", "flattener", "Flatten"),
            ("slither.tools.doctor.__main__", "doctor", "Troubleshoot"),
            ("slither.tools.upgradeability.__main__", "upgradeability_app", "Upgradeability"),
            ("slither.tools.possible_paths.__main__", "possible_paths_app", "paths"),
            ("slither.tools.properties.__main__", "properties_app", "properties"),
            ("slither.tools.read_storage.__main__", "read_storage", "storage"),
            ("slither.tools.slither_format.__main__", "format_app", "Auto-fix"),
            ("slither.tools.erc_conformance.__main__", "conformance", "ERC"),
            ("slither.tools.mutator.__main__", "mutate_cmd", "mutator"),
            ("slither.tools.interface.__main__", "interface_cmd", "interface"),
            ("slither.tools.codex.__main__", "codex_app", "Codex"),
        ],
    )
    def test_tool_entry_point_help(
        self, module_path: str, app_name: str, expected_help_text: str
    ) -> None:
        """Test that each tool's app can be invoked with --help."""
        import importlib

        module = importlib.import_module(module_path)
        app = getattr(module, app_name)

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0, f"{module_path} --help failed: {result.output}"
        assert expected_help_text.lower() in result.output.lower(), (
            f"Expected '{expected_help_text}' in {module_path} help output"
        )

    @pytest.mark.parametrize(
        "module_path",
        [
            "slither.tools.flattening.__main__",
            "slither.tools.doctor.__main__",
            "slither.tools.upgradeability.__main__",
            "slither.tools.possible_paths.__main__",
            "slither.tools.properties.__main__",
            "slither.tools.read_storage.__main__",
            "slither.tools.slither_format.__main__",
            "slither.tools.erc_conformance.__main__",
            "slither.tools.mutator.__main__",
            "slither.tools.interface.__main__",
            "slither.tools.codex.__main__",
            "slither.tools.kspec_coverage.__main__",
        ],
    )
    def test_tool_has_main_function(self, module_path: str) -> None:
        """Test that each tool module has a main() function for entry points."""
        import importlib

        module = importlib.import_module(module_path)

        assert hasattr(module, "main"), f"{module_path} missing main() function"
        assert callable(module.main), f"{module_path}.main is not callable"


class TestSimilarityEntryPoint:
    """Test similarity entry point separately (has optional dependencies)."""

    def test_similarity_has_main_function(self) -> None:
        """Test that similarity module has main() function."""
        try:
            from slither.tools.similarity import __main__ as simil_main

            assert hasattr(simil_main, "main"), "similarity missing main() function"
            assert callable(simil_main.main), "similarity.main is not callable"
        except ImportError:
            pytest.skip("similarity dependencies not installed")

    def test_similarity_app_help(self) -> None:
        """Test that similarity app can show help."""
        try:
            from slither.tools.similarity.__main__ import similarity

            runner = CliRunner()
            result = runner.invoke(similarity, ["--help"])
            assert result.exit_code == 0
            assert "similarity" in result.output.lower()
        except ImportError:
            pytest.skip("similarity dependencies not installed")


class TestMainEntryPoint:
    """Test the main slither entry point."""

    def test_main_function_exists(self) -> None:
        """Test that slither.__main__ has a main() function."""
        from slither import __main__ as slither_main

        assert hasattr(slither_main, "main"), "slither.__main__ missing main() function"
        assert callable(slither_main.main), "slither.__main__.main is not callable"

    def test_main_app_help(self) -> None:
        """Test that main app shows help."""
        from slither.__main__ import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "slither" in result.output.lower() or "detect" in result.output.lower()
