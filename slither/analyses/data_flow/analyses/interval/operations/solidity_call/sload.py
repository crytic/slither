"""SLOAD operation handler for interval analysis."""

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
    get_variable_name,
)
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

SLOAD_FUNCTIONS = frozenset(
    {
        "sload(uint256)",
    }
)

STORAGE_BIT_WIDTH = 256


class SloadHandler(BaseOperationHandler):
    """Handler for sload(slot) operations.

    Looks up all modeled prior writes to the same slot and transfers their
    conservative interval hull to the loaded value.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process sload by correlating with prior sstore writes."""
        if not operation.arguments:
            return

        if operation.lvalue is None:
            return

        slot_arg = operation.arguments[0]
        slot_key = self._get_slot_key(slot_arg)
        lvalue_name = get_variable_name(operation.lvalue)

        sort = Sort(SortKind.BITVEC, [STORAGE_BIT_WIDTH])
        tracked_lvalue = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=False, bit_width=STORAGE_BIT_WIDTH
        )
        write_vars = domain.state.get_storage_writes(slot_key)
        if write_vars and not domain.state.storage_may_be_unwritten(slot_key):
            interval = self._written_interval(write_vars, domain)
            if interval is not None:
                tracked_lvalue = tracked_lvalue.with_interval(interval)
        domain.state.set_variable(lvalue_name, tracked_lvalue)

    def _get_slot_key(self, slot_arg: object) -> str:
        """Convert slot argument to a string key."""
        if isinstance(slot_arg, Constant):
            return str(slot_arg.value)
        return get_variable_name(slot_arg)

    @staticmethod
    def _written_interval(
        write_vars: list[str],
        domain: IntervalDomain,
    ) -> NumericInterval | None:
        """Return the hull of every modeled value that may occupy a slot."""
        interval = None
        for variable_name in write_vars:
            tracked = domain.state.get_variable(variable_name)
            if tracked is None or not tracked.is_total:
                return None
            interval = tracked.interval if interval is None else interval.hull(tracked.interval)
        return interval
