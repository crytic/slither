#!/usr/bin/env python3
"""Generate the configuration-file option section in docs/src/Usage.md."""

from __future__ import annotations

import argparse
import json
from enum import Enum
from pathlib import Path
from typing import Any

from crytic_compile.cryticparser.defaults import DEFAULTS_FLAG_IN_CONFIG as CRYTIC_DEFAULTS

from slither.utils.command_line import defaults_flag_in_config


ROOT = Path(__file__).resolve().parents[1]
USAGE_PATH = ROOT / "docs" / "src" / "Usage.md"

SLITHER_START = "<!-- slither-config-options:start -->"
SLITHER_END = "<!-- slither-config-options:end -->"
CRYTIC_START = "<!-- crytic-compile-config-options:start -->"
CRYTIC_END = "<!-- crytic-compile-config-options:end -->"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _render_defaults(defaults: dict[str, Any]) -> str:
    normalized = {key: _jsonable(value) for key, value in defaults.items()}
    return "```json\n" + json.dumps(normalized, indent=4) + "\n```"


def _replace_between(text: str, start: str, end: str, content: str) -> str:
    start_index = text.index(start) + len(start)
    end_index = text.index(end)
    return text[:start_index] + "\n" + content + "\n" + text[end_index:]


def render_slither_defaults() -> str:
    slither_defaults = {
        key: value for key, value in defaults_flag_in_config.items() if key not in CRYTIC_DEFAULTS
    }
    return _render_defaults(slither_defaults)


def render_crytic_defaults() -> str:
    return _render_defaults(dict(CRYTIC_DEFAULTS))


def render_usage(text: str) -> str:
    text = _replace_between(text, SLITHER_START, SLITHER_END, render_slither_defaults())
    return _replace_between(text, CRYTIC_START, CRYTIC_END, render_crytic_defaults())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if docs/src/Usage.md is stale.")
    args = parser.parse_args()

    current = USAGE_PATH.read_text(encoding="utf-8")
    rendered = render_usage(current)
    if args.check:
        if current != rendered:
            raise SystemExit("docs/src/Usage.md configuration option section is stale")
    else:
        USAGE_PATH.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
