"""SSTORE operation handler for interval analysis."""

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

SSTORE_FUNCTIONS = frozenset({
    "sstore(uint256,uint256)",
})

STORAGE_BIT_WIDTH = 256


class SstoreHandler(BaseOperationHandler):
    """Handler for sstore(slot, value) operations.

    Models sstore as an assignment: storage[slot] = value.
    Tracks storage writes for later sload correlation.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process sstore as assignment to storage slot."""
        if len(operation.arguments) < 2:
            return

        if operation.lvalue is None:
            return

        slot_arg = operation.arguments[0]
        value_arg = operation.arguments[1]
        lvalue_name = get_variable_name(operation.lvalue)
        sort = Sort(SortKind.BITVEC, [STORAGE_BIT_WIDTH])

        tracked_lvalue = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=False, bit_width=STORAGE_BIT_WIDTH
        )

        constrain_to_value(self.solver, tracked_lvalue, value_arg, domain)
        domain.state.set_variable(lvalue_name, tracked_lvalue)

        slot_key = self._get_slot_key(slot_arg)
        domain.state.add_storage_write(slot_key, lvalue_name)

    def _get_slot_key(self, slot_arg: object) -> str:
        """Convert slot argument to a string key."""
        if isinstance(slot_arg, Constant):
            return str(slot_arg.value)
        return get_variable_name(slot_arg)
