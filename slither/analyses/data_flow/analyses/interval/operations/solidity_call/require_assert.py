"""Require and assert operation handlers for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.solidity_call import SolidityCall

from slither.analyses.data_flow.smt_solver.types import CheckSatResult, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

REQUIRE_ASSERT_FUNCTIONS = frozenset({
    "require(bool)",
    "require(bool,string)",
    "require(bool,error)",
    "assert(bool)",
})


class RequireAssertHandler(BaseOperationHandler):
    """Handler for require() and assert() calls.

    Constrains the condition argument to be true, marking the path as
    unreachable (BOTTOM) if that makes constraints unsatisfiable.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process require/assert by constraining condition to true."""
        if not operation.arguments:
            return

        condition = operation.arguments[0]
        condition_name = get_variable_name(condition)
        tracked = domain.state.get_variable(condition_name)

        if tracked is None:
            return

        one = self.solver.create_constant(1, Sort(SortKind.BITVEC, [1]))
        self.solver.assert_constraint(tracked.term == one)

        if self._is_unsatisfiable():
            domain.variant = DomainVariant.BOTTOM

    def _is_unsatisfiable(self) -> bool:
        """Check if current constraints are unsatisfiable (unreachable path)."""
        result = self.solver.check_sat()
        return result == CheckSatResult.UNSAT
