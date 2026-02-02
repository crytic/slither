"""High-level call operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.interprocedural import (
    InterproceduralHandler,
)
from slither.core.declarations.function import Function
from slither.slithir.operations.high_level_call import HighLevelCall

if TYPE_CHECKING:
    from slither.slithir.operations.call import Call


class HighLevelCallHandler(InterproceduralHandler):
    """Handler for high-level (external) call operations.

    External calls invoke code in other contracts. When the called function
    is resolvable (e.g., calling a known contract in the same compilation),
    we perform interprocedural analysis. Otherwise, return values are
    unconstrained as a sound over-approximation.
    """

    _call_counter: int = 0

    def _get_called_function(self, operation: "Call") -> Function | None:
        """Extract the called Function from the high-level call.

        Returns the Function if resolvable and implemented, None otherwise.
        Interface functions have no implementation (0 nodes) and return None.
        """
        if not isinstance(operation, HighLevelCall):
            return None
        func = operation.function
        if not isinstance(func, Function):
            return None
        # Interface functions have no nodes - can't analyze them
        if not func.nodes:
            return None
        return func

    def _build_call_prefix(self, operation: "Call") -> str:
        """Build unique prefix for high-level call."""
        HighLevelCallHandler._call_counter += 1
        func_name = "unknown"
        if isinstance(operation, HighLevelCall) and operation.function:
            if isinstance(operation.function, Function):
                func_name = operation.function.name
            elif hasattr(operation, "function_name"):
                func_name = str(operation.function_name)
        return f"_ext{HighLevelCallHandler._call_counter}_{func_name}_"
