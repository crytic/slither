"""Handler for memory loads (mload)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.solidity_call.memory.base import (
    MemoryBaseHandler,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class MemoryLoadHandler(MemoryBaseHandler):
    """Handle `mload` memory reads."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: only process SolidityCall operations.
        if operation is None or not isinstance(operation, SolidityCall):
            return

        # Guard: solver is required to build constraints.
        if self.solver is None:
            return

        # Guard: skip non-concrete states.
        if domain.variant != DomainVariant.STATE:
            return

        # Guard: need an offset argument to model the load.
        if not operation.arguments:
            return

        lvalue = operation.lvalue
        # Guard: memory loads without lvalues are irrelevant for tracking.
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name for the destination.
        if lvalue_name is None:
            return

        return_type: Optional[ElementaryType] = None
        type_call = getattr(operation, "type_call", None)
        # Branch: prefer explicit return type information from the call.
        if isinstance(type_call, list) and type_call:
            return_type = IntervalSMTUtils.resolve_elementary_type(type_call[0])

        # Branch: fall back to the lvalue type when explicit info is absent.
        if return_type is None and hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Branch: default to a full word when the type remains unknown.
        if return_type is None:
            return_type = self._memory_elementary_type(32)

        # Guard: ensure we can represent the return type.
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return

        tracked_lvalue = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked_lvalue is None:
            tracked_lvalue = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            # Guard: creation may fail for unsupported types.
            if tracked_lvalue is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked_lvalue)

        slot_name = self._resolve_memory_slot_name(operation.arguments[0], domain)
        # Branch: link with a previously stored memory slot when available.
        if slot_name is not None:
            memory_var = IntervalSMTUtils.get_tracked_variable(domain, slot_name)
            if memory_var is not None:
                memory_term = memory_var.term
                lvalue_width = self.solver.bv_size(tracked_lvalue.term)
                memory_width = self.solver.bv_size(memory_term)

                # Branch: extend or truncate memory value to match lvalue width.
                if memory_width < lvalue_width:
                    is_signed = bool(memory_var.base.metadata.get("is_signed", False))
                    memory_term = IntervalSMTUtils.extend_to_width(
                        self.solver, memory_term, lvalue_width, is_signed
                    )
                elif memory_width > lvalue_width:
                    memory_term = IntervalSMTUtils.truncate_to_width(
                        self.solver, memory_term, lvalue_width
                    )

                self.solver.assert_constraint(tracked_lvalue.term == memory_term)
                tracked_lvalue.assert_no_overflow(self.solver)
                domain.state.set_range_variable(lvalue_name, tracked_lvalue)
                return

        # Fallback: model as unconstrained within type bounds.
        tracked_lvalue.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, tracked_lvalue)

