"""SLOAD operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
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

SLOAD_FUNCTIONS = frozenset(
    {
        "sload(uint256)",
    }
)

STORAGE_BIT_WIDTH = 256


class SloadHandler(BaseOperationHandler):
    """Handler for sload(slot) operations.

    Looks up prior sstore writes to the same slot and constrains
    the result to be one of those values (OR).
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
        domain.state.set_variable(lvalue_name, tracked_lvalue)

        write_vars = domain.state.get_storage_writes(slot_key)
        if not write_vars:
            return

        self._constrain_to_writes(
            operation,
            node,
            slot_key,
            tracked_lvalue,
            write_vars,
            domain,
        )

    def _get_slot_key(self, slot_arg: object) -> str:
        """Convert slot argument to a string key."""
        if isinstance(slot_arg, Constant):
            return str(slot_arg.value)
        return get_variable_name(slot_arg)

    def _constrain_to_writes(
        self,
        operation: SolidityCall,
        node: Node,
        slot_key: str,
        tracked_lvalue: TrackedSMTVariable,
        write_vars: list[str],
        domain: IntervalDomain,
    ) -> None:
        """Constrain lvalue to equal one of the written values (OR)."""
        terms = []
        for var_name in write_vars:
            tracked = domain.state.get_variable(var_name)
            if tracked is not None:
                terms.append(tracked_lvalue.term == tracked.term)

        if not terms:
            return

        formula = terms[0]
        if len(terms) == 1:
            formula = terms[0]
        elif len(terms) > 1:
            formula = self.solver.Or(*terms)
        self._register_equation(
            operation,
            node,
            domain,
            formula,
            "storage_read_value",
            origin_kind=FactOriginKind.STORAGE,
            context_id=domain.context_id.for_storage(slot_key),
        )
