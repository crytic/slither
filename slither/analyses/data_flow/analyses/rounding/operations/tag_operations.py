"""Utility functions for rounding operation handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
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


def invert_tag(tag: RoundingTag) -> RoundingTag:
    """Invert rounding direction (UP <-> DOWN) and keep neutral tags unchanged."""
    if tag == RoundingTag.UP:
        return RoundingTag.DOWN
    if tag == RoundingTag.DOWN:
        return RoundingTag.UP
    return tag


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
