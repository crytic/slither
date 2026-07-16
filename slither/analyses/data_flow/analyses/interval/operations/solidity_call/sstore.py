"""SSTORE operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    ValueConstraintOrigin,
    constrain_to_value,
    get_variable_name,
)
from slither.analyses.data_flow.smt_solver.facts import FactOriginKind
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

SSTORE_FUNCTIONS = frozenset(
    {
        "sstore(uint256,uint256)",
    }
)

STORAGE_BIT_WIDTH = 256


class SstoreHandler(BaseOperationHandler):
    """Handler for sstore(slot, value) operations.

    Models sstore as an assignment: storage[slot] = value.
    Tracks storage writes for later sload correlation.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: IntervalDomain,
        node: Node,
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

        slot_key = self._get_slot_key(slot_arg)
        constrain_to_value(
            self.solver,
            tracked_lvalue,
            value_arg,
            domain,
            ValueConstraintOrigin(
                operation,
                node,
                "storage_write_value",
                context_id=domain.context_id.for_storage(slot_key),
                origin_kind=FactOriginKind.STORAGE,
            ),
        )
        tracked_lvalue = tracked_lvalue.with_interval(
            self._value_interval(value_arg, tracked_lvalue, domain)
        )
        domain.state.set_variable(lvalue_name, tracked_lvalue)

        domain.state.add_storage_write(slot_key, lvalue_name)

    @staticmethod
    def _value_interval(
        value: object,
        target: TrackedSMTVariable,
        domain: IntervalDomain,
    ) -> NumericInterval:
        if isinstance(value, Constant):
            constant = value.value
            if isinstance(constant, bool):
                constant = int(constant)
            if isinstance(constant, int) and target.type_interval.lower <= constant <= (
                target.type_interval.upper
            ):
                return NumericInterval(constant, constant)
            return target.type_interval
        tracked = domain.state.get_variable(get_variable_name(value))
        if tracked is None or not tracked.is_total:
            return target.type_interval
        return tracked.interval.intersection(target.type_interval) or target.type_interval

    def _get_slot_key(self, slot_arg: object) -> str:
        """Convert slot argument to a string key."""
        if isinstance(slot_arg, Constant):
            return str(slot_arg.value)
        return get_variable_name(slot_arg)
