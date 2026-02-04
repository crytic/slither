"""Utility functions for rounding operation handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag, TagSet
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


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


def infer_tag_from_name(function_name: Optional[object]) -> RoundingTag:
    """Infer rounding direction from function name.

    Accepts non-string inputs and coerces to string for name checks.
    """
    name_lower = str(function_name).lower() if function_name is not None else ""
    if "down" in name_lower or "floor" in name_lower:
        return RoundingTag.DOWN
    elif "up" in name_lower or "ceil" in name_lower:
        return RoundingTag.UP
    return RoundingTag.NEUTRAL
