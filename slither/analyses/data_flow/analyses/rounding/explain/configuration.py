"""DSPy language model configuration for rounding trace explanation."""

import os
from pathlib import Path

import dspy

from slither.analyses.data_flow.logger import get_logger

logger = get_logger()

DEFAULT_MODEL = "anthropic/claude-sonnet-4-5-20250929"


def configure_dspy(
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> None:
    """Configure DSPy with the specified language model.

    Loads .env file from cwd if present, then reads API keys from
    environment variables. Supported providers: anthropic (ANTHROPIC_API_KEY),
    openai (OPENAI_API_KEY).
    """
    _load_env_file()
    _validate_api_key(model)
    language_model = dspy.LM(
        model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    dspy.configure(lm=language_model)


def _validate_api_key(model: str) -> None:
    """Raise if the required API key env var is not set."""
    provider_keys = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    provider = model.split("/")[0]
    env_var = provider_keys.get(provider)
    if env_var and not os.environ.get(env_var):
        logger.error_and_raise(
            f"Environment variable {env_var} not set for provider {provider}",
            EnvironmentError,
        )


def _load_env_file() -> None:
    """Load .env file from current working directory if it exists."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
