import logging
import os
from pathlib import Path

logger = logging.getLogger("Slither")


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
