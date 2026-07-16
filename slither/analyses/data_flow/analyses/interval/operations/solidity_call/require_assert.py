"""Require and assert operation handlers for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
)
from slither.analyses.data_flow.smt_solver.facts import FactKind
from slither.analyses.data_flow.smt_solver.query import (
    FeasibilityStatus,
    QueryPurpose,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.slithir.operations.solidity_call import SolidityCall


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

REQUIRE_ASSERT_FUNCTIONS = frozenset(
    {
        "require(bool)",
        "require(bool,string)",
        "require(bool,error)",
        "assert(bool)",
    }
)


class RequireAssertHandler(BaseOperationHandler):
    """Handler for require() and assert() calls.

    Constrains the condition argument to be true, marking the path as
    unreachable (BOTTOM) if that makes constraints unsatisfiable.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process require/assert by constraining condition to true."""
        if not operation.arguments:
            return
        if domain.state is None:
            return

        condition = operation.arguments[0]
        condition_name = get_variable_name(condition)
        tracked = domain.state.get_variable(condition_name)

        if tracked is None:
            return

        one = self.solver.create_constant(1, Sort(SortKind.BITVEC, [1]))
        self._add_state_fact(
            operation,
            node,
            domain,
            tracked.term == one,
            "successful_require_or_assert",
            kind=FactKind.PATH_CONDITION,
        )

        purpose = QueryPurpose.ASSERT if str(operation.function).startswith("assert") else (
            QueryPurpose.REQUIRE
        )
        if self._is_unsatisfiable(domain, purpose):
            domain.variant = DomainVariant.BOTTOM

    def _is_unsatisfiable(
        self,
        domain: IntervalDomain,
        purpose: QueryPurpose,
    ) -> bool:
        """Check if current constraints are unsatisfiable (unreachable path)."""
        if domain.state is None:
            return False
        result = self.solver.check_feasibility(
            state_id=domain.state.semantic_id(),
            state_facts=domain.state.get_facts(),
            purpose=purpose,
        )
        return result.status is FeasibilityStatus.UNSAT
