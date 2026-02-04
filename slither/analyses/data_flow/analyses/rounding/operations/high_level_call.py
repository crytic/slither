"""High level call operation handler for rounding analysis."""

from __future__ import annotations

from slither.analyses.data_flow.analyses.rounding.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.high_level_call import HighLevelCall


class HighLevelCallHandler(InterproceduralHandler):
    """Handler for high level call operations.

    High level calls are external function calls. If the called function
    is resolvable and implemented, we can analyze it interprocedurally.
    Interface functions have no implementation and fall back to name inference.
    """

    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function from the high-level call.

        Returns the Function if resolvable and implemented, None otherwise.
        Interface functions have no implementation (0 nodes) and return None.
        """
        if not isinstance(operation, HighLevelCall):
            return None
        called_function = operation.function
        if not isinstance(called_function, Function):
            return None
        if not called_function.nodes:
            return None
        return called_function

    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""
        if not isinstance(operation, HighLevelCall):
            return ""
        return str(operation.function_name.value)
