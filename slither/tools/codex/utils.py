import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger("Slither")


# TODO: investigate how to set the correct return type
# So that the other modules can work with openai
def openai_module(api_key: Optional[str] = None):  # type: ignore
    """
    Return the openai module
    Consider checking the usage of open (slither.codex_enabled) before using this function

    Returns:
        Optional[the openai module]
    """
    try:
        # pylint: disable=import-outside-toplevel
        import openai

        # Here, we leverage the fact that importing a module in Python is a singleton
        # So defining the key the first time is enough for subsequent imports
        if api_key is not None:
            openai.api_key = api_key

        assert openai.api_key is not None

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
