"""MLOAD operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

MLOAD_FUNCTIONS = frozenset({
    "mload(uint256)",
})

MEMORY_BIT_WIDTH = 256


class MloadHandler(BaseOperationHandler):
    """Handler for mload(offset) operations.

    Looks up prior mstore writes to the same offset and constrains
    the result to be one of those values (OR).
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process mload by correlating with prior mstore writes."""
        if not operation.arguments:
            return

        if operation.lvalue is None:
            return

        offset_arg = operation.arguments[0]
        offset_key = self._get_offset_key(offset_arg)
        lvalue_name = get_variable_name(operation.lvalue)

        sort = Sort(SortKind.BITVEC, [MEMORY_BIT_WIDTH])
        tracked_lvalue = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=False, bit_width=MEMORY_BIT_WIDTH
        )
        domain.state.set_variable(lvalue_name, tracked_lvalue)

        write_vars = domain.state.get_memory_writes(offset_key)
        if not write_vars:
            return

        self._constrain_to_writes(tracked_lvalue, write_vars, domain)

    def _get_offset_key(self, offset_arg: object) -> str:
        """Convert offset argument to a string key."""
        if isinstance(offset_arg, Constant):
            return str(offset_arg.value)
        return get_variable_name(offset_arg)

    def _constrain_to_writes(
        self,
        tracked_lvalue: TrackedSMTVariable,
        write_vars: list[str],
        domain: "IntervalDomain",
    ) -> None:
        """Constrain lvalue to equal one of the written values (OR)."""
        terms = []
        for var_name in write_vars:
            tracked = domain.state.get_variable(var_name)
            if tracked is not None:
                terms.append(tracked_lvalue.term == tracked.term)

        if not terms:
            return

        if len(terms) == 1:
            self.solver.assert_constraint(terms[0])
        else:
            self.solver.assert_constraint(self.solver.Or(*terms))
