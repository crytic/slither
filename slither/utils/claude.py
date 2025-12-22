"""
Claude integration for Slither
Supports both ANTHROPIC_API_KEY and CLAUDE_CODE_OAUTH_TOKEN (for Claude Code MAX users)
"""
import logging
import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, Any

from slither.utils.command_line import defaults_flag_in_config

logger = logging.getLogger("Slither")


def init_parser(parser: ArgumentParser, always_enable_claude: bool = False) -> None:
    """
    Init the cli arg with Claude features

    Args:
        parser:
        always_enable_claude (Optional(bool)): if true, --claude is not added

    Returns:

    """
    group_claude = parser.add_argument_group("Claude (https://www.anthropic.com/claude)")

    if not always_enable_claude:
        group_claude.add_argument(
            "--claude",
            help="Enable Claude (requires ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN)",
            action="store_true",
            default=defaults_flag_in_config["claude"],
        )

    group_claude.add_argument(
        "--claude-log",
        help="Log Claude queries (in crytic_export/claude/)",
        action="store_true",
        default=False,
    )

    group_claude.add_argument(
        "--claude-contracts",
        help="Comma separated list of contracts to submit to Claude",
        action="store",
        default=defaults_flag_in_config["claude_contracts"],
    )

    group_claude.add_argument(
        "--claude-model",
        help="Claude model to use (passed to Claude Code CLI's --model option, e.g., 'opus', 'sonnet'). Defaults to 'sonnet'",
        action="store",
        default=defaults_flag_in_config["claude_model"],
    )

    group_claude.add_argument(
        "--claude-max-tokens",
        help="Maximum amount of tokens to use on the response. Defaults to 4096",
        action="store",
        default=defaults_flag_in_config["claude_max_tokens"],
    )

    group_claude.add_argument(
        "--claude-use-code",
        help="Use Claude Code CLI instead of API (uses CLAUDE_CODE_OAUTH_TOKEN, no API cost for MAX subscribers)",
        action="store_true",
        default=False,
    )


def get_claude_client() -> Optional[Any]:
    """
    Return the Anthropic client using ANTHROPIC_API_KEY

    Returns:
        Optional[Anthropic client]
    """
    try:
        # pylint: disable=import-outside-toplevel
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key is None:
            logger.info(
                "Please provide an Anthropic API Key in ANTHROPIC_API_KEY (https://console.anthropic.com/)"
            )
            return None
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        logger.info("Anthropic SDK was not installed")
        logger.info('run "pip install anthropic"')
        return None


def check_claude_code_available() -> bool:
    """
    Check if Claude Code CLI is available and authenticated

    Returns:
        bool: True if Claude Code is available
    """
    oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
    if oauth_token:
        return True

    # Check if claude CLI is available
    try:
        result = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=10, check=False
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_claude_code(prompt: str, model: str = "sonnet", timeout: int = 120) -> Optional[str]:
    """
    Run prompt through Claude Code CLI
    This uses CLAUDE_CODE_OAUTH_TOKEN for MAX subscribers (no API cost)

    Args:
        prompt: The prompt to send
        model: Model to use (e.g., 'opus', 'sonnet', or full model name)
        timeout: Timeout in seconds

    Returns:
        Optional[str]: Claude's response or None on failure
    """
    try:
        env = os.environ.copy()
        oauth_token = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        if oauth_token:
            env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token

        logger.info(f"Claude Code: Sending request with model '{model}' (this may take a while)...")

        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )

        if result.returncode == 0:
            logger.info("Claude Code: Response received")
            return result.stdout.strip()
        logger.info(f"Claude Code failed: {result.stderr}")
        return None
    except subprocess.TimeoutExpired:
        logger.info(f"Claude Code request timed out after {timeout}s")
        return None
    except FileNotFoundError:
        logger.info(
            "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        )
        return None


def run_claude_api(
    client: Any, prompt: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096
) -> Optional[str]:
    """
    Run prompt through Claude API

    Args:
        client: Anthropic client
        prompt: The prompt to send
        model: Model to use
        max_tokens: Maximum tokens for response

    Returns:
        Optional[str]: Claude's response or None on failure
    """
    try:
        message = client.messages.create(
            model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:  # pylint: disable=broad-except
        logger.info(f"Claude API request failed: {str(e)}")
        return None


def log_claude(filename: str, content: str) -> None:
    """
    Log the prompt/response in crytic_export/claude/filename
    Append to the file

    Args:
        filename: filename to write to
        content: content to write

    Returns:
        None
    """
    Path("crytic_export/claude").mkdir(parents=True, exist_ok=True)

    with open(Path("crytic_export/claude", filename), "a", encoding="utf8") as file:
        file.write(content)
        file.write("\n")
