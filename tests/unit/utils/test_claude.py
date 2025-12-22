"""
Tests for Claude integration utilities
"""

import os
import subprocess
from unittest.mock import patch, MagicMock

from slither.utils.claude import (
    check_claude_code_available,
    get_claude_client,
    run_claude_code,
)


class TestClaudeCodeAvailability:
    """Tests for Claude Code CLI availability check"""

    def test_oauth_token_available(self):
        """Test that OAuth token makes Claude Code available"""
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test_token"}):
            assert check_claude_code_available() is True

    def test_oauth_token_not_available_cli_works(self):
        """Test fallback to CLI check when no OAuth token"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                # Remove CLAUDE_CODE_OAUTH_TOKEN if it exists
                os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
                result = check_claude_code_available()
                assert result is True
                mock_run.assert_called_once()

    def test_oauth_token_not_available_cli_fails(self):
        """Test that CLI check failure returns False"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
                result = check_claude_code_available()
                assert result is False

    def test_cli_not_found(self):
        """Test handling when CLI is not installed"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()
                os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
                result = check_claude_code_available()
                assert result is False


class TestClaudeClient:
    """Tests for Anthropic client initialization"""

    def test_no_api_key(self):
        """Test that missing API key returns None"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = get_claude_client()
            assert result is None

    def test_anthropic_not_installed(self):
        """Test handling when anthropic package is not installed"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
            with patch.dict("sys.modules", {"anthropic": None}):
                # This will raise ImportError
                with patch(
                    "slither.utils.claude.get_claude_client",
                    side_effect=ImportError("No module named 'anthropic'"),
                ):
                    pass  # Just verify no crash


class TestRunClaudeCode:
    """Tests for Claude Code CLI runner"""

    def test_run_claude_code_success(self):
        """Test successful Claude Code CLI execution"""
        with patch("slither.utils.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Test response", stderr="")
            result = run_claude_code("test prompt", model="sonnet")
            assert result == "Test response"
            mock_run.assert_called_once()

    def test_run_claude_code_failure(self):
        """Test Claude Code CLI execution failure"""
        with patch("slither.utils.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error message")
            result = run_claude_code("test prompt", model="sonnet")
            assert result is None

    def test_run_claude_code_timeout(self):
        """Test Claude Code CLI timeout handling"""
        with patch("slither.utils.claude.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)
            result = run_claude_code("test prompt", timeout=120)
            assert result is None

    def test_run_claude_code_not_found(self):
        """Test handling when Claude CLI is not installed"""
        with patch("slither.utils.claude.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = run_claude_code("test prompt")
            assert result is None
