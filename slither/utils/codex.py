import logging
import os
from argparse import ArgumentParser
from pathlib import Path

from slither.utils.command_line import defaults_flag_in_config

logger = logging.getLogger("Slither")


def init_parser(parser: ArgumentParser, always_enable_codex: bool = False) -> None:
    """
    Init the cli arg with codex features

    Args:
        parser:
        always_enable_codex (Optional(bool)): if true, --codex is not enabled

    Returns:

    """
    group_codex = parser.add_argument_group("Codex (https://beta.openai.com/docs/guides/code)")

    if not always_enable_codex:
        group_codex.add_argument(
            "--codex",
            help="Enable codex (require an OpenAI API Key)",
            action="store_true",
            default=defaults_flag_in_config["codex"],
        )

    group_codex.add_argument(
        "--codex-log",
        help="Log codex queries (in crytic_export/codex/)",
        action="store_true",
        default=False,
    )

    group_codex.add_argument(
        "--codex-contracts",
        help="Comma separated list of contracts to submit to OpenAI Codex",
        action="store",
        default=defaults_flag_in_config["codex_contracts"],
    )

    group_codex.add_argument(
        "--codex-model",
        help="Name of the Codex model to use (affects pricing).  Defaults to 'text-davinci-003'",
        action="store",
        default=defaults_flag_in_config["codex_model"],
    )

    group_codex.add_argument(
        "--codex-temperature",
        help="Temperature to use with Codex.  Lower number indicates a more precise answer while higher numbers return more creative answers.  Defaults to 0",
        action="store",
        default=defaults_flag_in_config["codex_temperature"],
    )

    group_codex.add_argument(
        "--codex-max-tokens",
        help="Maximum amount of tokens to use on the response.  This number plus the size of the prompt can be no larger than the limit (4097 for text-davinci-003)",
        action="store",
        default=defaults_flag_in_config["codex_max_tokens"],
    )

    group_codex.add_argument(
        "--codex-organization",
        help="Codex organization",
        action="store",
        default=None,
    )


# TODO: investigate how to set the correct return type
# So that the other modules can work with openai
def openai_module():  # type: ignore
    """
    Return the openai module
    Consider checking the usage of open (slither.codex_enabled) before using this function

    Returns:
        Optional[the openai module]
    """
    try:
        # pylint: disable=import-outside-toplevel
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            logger.info(
                "Please provide an Open API Key in OPENAI_API_KEY (https://beta.openai.com/account/api-keys)"
            )
            return None
        openai.api_key = api_key
    except ImportError:
        logger.info("OpenAI was not installed")  # type: ignore
        logger.info('run "pip install openai"')
        return None
    return openai


def log_codex(filename: str, prompt: str) -> None:
    """
    Log the prompt in crytic/export/codex/filename
    Append to the file

    Args:
        filename: filename to write to
        prompt: prompt to write

    Returns:
        None
    """

    Path("crytic_export/codex").mkdir(parents=True, exist_ok=True)

    with open(Path("crytic_export/codex", filename), "a", encoding="utf8") as file:
        file.write(prompt)
        file.write("\n")
