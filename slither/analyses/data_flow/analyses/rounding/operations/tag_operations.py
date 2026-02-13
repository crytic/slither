"""Utility functions for rounding operation handlers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag, TagSet
from slither.analyses.data_flow.logger import get_logger
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )

_logger = get_logger()

KnownLibraryTags = dict[tuple[str, str], RoundingTag]


def get_variable_tag(
    variable: Optional[Union[RVALUE, Function]],
    domain: "RoundingDomain",
) -> RoundingTag:
    """Get the rounding tag for a variable or constant.

    Accepts RVALUE/None and returns NEUTRAL for constants or unrecognized types.
    """
    if isinstance(variable, Constant):
        return RoundingTag.NEUTRAL
    if isinstance(variable, Variable):
        return domain.state.get_tag(variable)
    return RoundingTag.NEUTRAL


def get_variable_tags(
    variable: Optional[Union[RVALUE, Function]],
    domain: "RoundingDomain",
) -> TagSet:
    """Get the rounding tag set for a variable or constant.

    Accepts RVALUE/None and returns {NEUTRAL} for constants or unrecognized types.
    """
    if isinstance(variable, Constant):
        return frozenset({RoundingTag.NEUTRAL})
    if isinstance(variable, Variable):
        return domain.state.get_tags(variable)
    return frozenset({RoundingTag.NEUTRAL})


def invert_tag(tag: RoundingTag) -> RoundingTag:
    """Invert rounding direction (UP <-> DOWN) and keep neutral tags unchanged."""
    if tag == RoundingTag.UP:
        return RoundingTag.DOWN
    if tag == RoundingTag.DOWN:
        return RoundingTag.UP
    return tag


def invert_tag_set(tags: TagSet) -> TagSet:
    """Invert all tags in a set (UP <-> DOWN)."""
    return frozenset(invert_tag(tag) for tag in tags)


def combine_tags(left: RoundingTag, right: RoundingTag) -> tuple[RoundingTag, bool]:
    """Combine two tags, detecting conflicts.

    Returns (combined_tag, has_conflict).
    Rules:
    - NEUTRAL combines with anything → the other tag
    - Same tags → that tag
    - UP + DOWN → UNKNOWN (conflict)
    - UNKNOWN in either → UNKNOWN
    """
    if left == RoundingTag.UNKNOWN or right == RoundingTag.UNKNOWN:
        return RoundingTag.UNKNOWN, True
    if left == RoundingTag.NEUTRAL:
        return right, False
    if right == RoundingTag.NEUTRAL:
        return left, False
    if left == right:
        return left, False
    return RoundingTag.UNKNOWN, True


def combine_tag_sets(left: TagSet, right: TagSet) -> tuple[TagSet, bool]:
    """Combine two tag sets for binary operations.

    Computes cross-product of combining each tag pair. Returns (result_set, has_conflict).
    """
    result: set[RoundingTag] = set()
    has_conflict = False
    for left_tag in left:
        for right_tag in right:
            combined, conflict = combine_tags(left_tag, right_tag)
            if conflict:
                has_conflict = True
            result.add(combined)
    return frozenset(result), has_conflict


BUILTIN_LIBRARY_TAGS: KnownLibraryTags = {
    ("FullMath", "mulDiv"): RoundingTag.DOWN,
    ("FullMath", "mulDivRoundingUp"): RoundingTag.UP,
}


def load_known_tags(file_path: Optional[Path] = None) -> KnownLibraryTags:
    """Load known library rounding tags, merging user JSON over built-in defaults.

    Built-in defaults cover common libraries (e.g. FullMath). If file_path is
    provided, user entries are merged on top (overriding any collisions).

    Expected JSON format: {"Contract.function": "UP|DOWN", ...}
    """
    tags: KnownLibraryTags = dict(BUILTIN_LIBRARY_TAGS)
    if file_path is None:
        return tags

    user_tags = _parse_known_tags_file(file_path)
    tags.update(user_tags)
    return tags


def _parse_known_tags_file(file_path: Path) -> KnownLibraryTags:
    """Parse a JSON file of known library rounding tags."""
    valid_tags = {"UP": RoundingTag.UP, "DOWN": RoundingTag.DOWN}
    raw = json.loads(file_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        _logger.error_and_raise(
            f"safe-libs file must be a JSON object, got {type(raw).__name__}",
            ValueError,
        )

    tags: KnownLibraryTags = {}
    for key, value in raw.items():
        parts = key.rsplit(".", maxsplit=1)
        if len(parts) != 2:
            _logger.error_and_raise(
                f"Invalid key '{key}': expected 'Contract.function'",
                ValueError,
            )
        contract_name, function_name = parts
        tag = valid_tags.get(value)
        if tag is None:
            _logger.error_and_raise(
                f"Invalid tag '{value}' for '{key}': must be UP or DOWN",
                ValueError,
            )
        tags[(contract_name, function_name)] = tag

    return tags


def lookup_known_tag(
    contract_name: str,
    function_name: str,
    known_tags: KnownLibraryTags,
) -> Optional[RoundingTag]:
    """Look up rounding tag for a known library function."""
    return known_tags.get((contract_name, function_name))


def infer_tag_from_name(function_name: Optional[object]) -> RoundingTag:
    """Infer rounding direction from function name.

    If name contains both up/ceil and down/floor indicators, returns NEUTRAL
    to fall back to interprocedural analysis (e.g., _downscaleUp).
    """
    name_lower = str(function_name).lower() if function_name is not None else ""

    has_down = "down" in name_lower or "floor" in name_lower
    has_up = "up" in name_lower or "ceil" in name_lower

    # Ambiguous - fall back to interprocedural analysis
    if has_down and has_up:
        return RoundingTag.NEUTRAL

    if has_down:
        return RoundingTag.DOWN
    if has_up:
        return RoundingTag.UP

    return RoundingTag.NEUTRAL


_ROUND_COMMENT_RE = re.compile(r"//\s*@round\s+(.+)")
_VALID_INLINE_TAGS: dict[str, RoundingTag] = {
    "UP": RoundingTag.UP,
    "DOWN": RoundingTag.DOWN,
    "NEUTRAL": RoundingTag.NEUTRAL,
    "UNKNOWN": RoundingTag.UNKNOWN,
}


def parse_inline_round_annotations(source_line: str) -> dict[str, RoundingTag]:
    """Parse //@round annotations from a Solidity source line.

    Supports ``//@round funcName=TAG`` or ``//@round f1=TAG, f2=TAG``.
    TAG must be UP, DOWN, NEUTRAL, or UNKNOWN (case-insensitive).
    Function names are case-sensitive.
    Logs a warning for unrecognized tag values.

    Args:
        source_line: A single line of Solidity source code.

    Returns:
        Mapping of function name to RoundingTag. Empty if no annotation found.
    """
    match = _ROUND_COMMENT_RE.search(source_line)
    if match is None:
        return {}

    annotations: dict[str, RoundingTag] = {}
    for entry in re.split(r"[,\s]+", match.group(1).strip()):
        if not entry:
            continue
        parts = entry.split("=", maxsplit=1)
        if len(parts) != 2:
            _logger.warning(
                f"Malformed //@round entry '{entry}': "
                "expected funcName=TAG — defaulting to UNKNOWN"
            )
            annotations[entry] = RoundingTag.UNKNOWN
            continue
        func_name, tag_str = parts
        tag = _VALID_INLINE_TAGS.get(tag_str.upper())
        if tag is None:
            _logger.warning(
                f"Invalid //@round tag '{tag_str}' for '{func_name}': "
                "must be UP, DOWN, NEUTRAL, or UNKNOWN — defaulting to UNKNOWN"
            )
            tag = RoundingTag.UNKNOWN
        annotations[func_name] = tag
    return annotations


def lookup_inline_round_tag(
    source_line: str,
    function_name: str,
) -> Optional[RoundingTag]:
    """Look up a function's rounding tag from an inline //@round annotation.

    Args:
        source_line: Raw Solidity source line containing the call.
        function_name: Name of the called function to look up.

    Returns:
        RoundingTag if the function is annotated, None otherwise.
    """
    return parse_inline_round_annotations(source_line).get(function_name)
