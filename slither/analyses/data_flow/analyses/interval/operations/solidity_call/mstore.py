"""MSTORE operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    constrain_to_value,
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

MSTORE_FUNCTIONS = frozenset({
    "mstore(uint256,uint256)",
})

MEMORY_BIT_WIDTH = 256


class MstoreHandler(BaseOperationHandler):
    """Handler for mstore(offset, value) operations.

    Models mstore as an assignment: memory[offset] = value.
    Tracks memory writes for later mload correlation.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process mstore as assignment to memory offset."""
        if len(operation.arguments) < 2:
            return

        if operation.lvalue is None:
            return

        offset_arg = operation.arguments[0]
        value_arg = operation.arguments[1]
        lvalue_name = get_variable_name(operation.lvalue)
        sort = Sort(SortKind.BITVEC, [MEMORY_BIT_WIDTH])

        tracked_lvalue = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=False, bit_width=MEMORY_BIT_WIDTH
        )

        constrain_to_value(self.solver, tracked_lvalue, value_arg, domain)
        domain.state.set_variable(lvalue_name, tracked_lvalue)

        offset_key = self._get_offset_key(offset_arg)
        domain.state.add_memory_write(offset_key, lvalue_name)

    def _get_offset_key(self, offset_arg: object) -> str:
        """Convert offset argument to a string key."""
        if isinstance(offset_arg, Constant):
            return str(offset_arg.value)
        return get_variable_name(offset_arg)
