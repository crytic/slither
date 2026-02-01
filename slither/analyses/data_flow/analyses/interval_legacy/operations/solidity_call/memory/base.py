"""Shared helpers for memory builtin handlers."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.analyses.data_flow.smt_solver.types import SMTTerm


class MemoryBaseHandler(BaseOperationHandler):
    """Base class providing memory slot helpers."""

    def _resolve_memory_slot_name(self, offset: object, domain: "IntervalDomain") -> Optional[str]:
        # Branch: use concrete constant offsets directly to keep slots stable.
        if isinstance(offset, Constant) and isinstance(offset.value, int):
            return f"memory[{offset.value}]"

        concrete_offset = self._get_single_value(offset, domain)
        # Branch: reuse single-valued range metadata when available.
        if concrete_offset is not None:
            return f"memory[{concrete_offset}]"

        offset_name = IntervalSMTUtils.resolve_variable_name(offset)
        # Guard: skip when we cannot build a stable slot name.
        if offset_name is None:
            return None

        return f"memory[{offset_name}]"

    def _resolve_value_term(
        self,
        value: object,
        target_var: "TrackedSMTVariable",
        domain: "IntervalDomain",
        fallback_type: ElementaryType,
    ) -> Optional["SMTTerm"]:
        # Branch: literal constant stored to memory.
        if isinstance(value, Constant):
            if not isinstance(value.value, int):
                return None
            return IntervalSMTUtils.create_constant_term(self.solver, value.value, fallback_type)

        value_name = IntervalSMTUtils.resolve_variable_name(value)
        # Guard: skip if we cannot resolve the source variable.
        if value_name is None:
            return None

        source_var = IntervalSMTUtils.get_tracked_variable(domain, value_name)
        # Guard: skip if the source variable is not tracked.
        if source_var is None:
            return None

        value_term = source_var.term
        target_width = self.solver.bv_size(target_var.term)
        value_width = self.solver.bv_size(value_term)

        # Branch: extend to target width when storing smaller values.
        if value_width < target_width:
            is_signed = bool(source_var.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(
                self.solver, value_term, target_width, is_signed
            )

        # Branch: truncate when storing wider values.
        if value_width > target_width:
            return IntervalSMTUtils.truncate_to_width(self.solver, value_term, target_width)

        return value_term

    def _get_single_value(self, arg: object, domain: "IntervalDomain") -> Optional[int]:
        arg_name = IntervalSMTUtils.resolve_variable_name(arg)
        # Guard: skip when no stable name can be found.
        if arg_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, arg_name)
        # Guard: skip when the variable is not tracked.
        if tracked is None:
            return None

        metadata = getattr(tracked.base, "metadata", {})
        min_value = metadata.get("min_value")
        max_value = metadata.get("max_value")

        # Branch: only reuse when range collapses to a single value.
        if min_value is not None and max_value is not None and min_value == max_value:
            return min_value

        return None

    def _memory_elementary_type(self, byte_size: int) -> ElementaryType:
        # Branch: bytes1 for single-byte stores, uint256 otherwise.
        if byte_size == 1:
            return ElementaryType("bytes1")
        return ElementaryType("uint256")
