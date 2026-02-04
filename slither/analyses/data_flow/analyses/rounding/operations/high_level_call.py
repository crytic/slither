"""High level call operation handler for rounding analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.high_level_call import HighLevelCall

if TYPE_CHECKING:
    pass


class HighLevelCallHandler(InterproceduralHandler):
    """Handler for high level call operations.

    High level calls are external function calls where we can only
    infer rounding from the function name.
    """

    def _get_called_function(self, operation: Call) -> Function | None:
        """External calls don't have accessible function bodies."""
        return None

    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""
        if not isinstance(operation, HighLevelCall):
            return ""
        return str(operation.function_name.value)
