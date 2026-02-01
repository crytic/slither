"""Handler for the `byte(uint256,uint256)` Solidity builtin in interval analysis."""

from typing import TYPE_CHECKING, List, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node
    from slither.core.variables.variable import Variable


class ByteHandler(BaseOperationHandler):
    """Handle `byte(uint256,uint256)`, modeling byte extraction as unconstrained uint8."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_preconditions(operation, domain):
            return

        lvalue_name, return_type = self._resolve_lvalue_info(operation)
        if lvalue_name is None or return_type is None:
            return

        tracked = self._get_or_create_tracked(domain, lvalue_name, return_type)
        if tracked is None:
            return

        self._apply_byte_constraints(operation, tracked, domain)

    def _validate_preconditions(
        self, operation: Optional[SolidityCall], domain: "IntervalDomain"
    ) -> bool:
        """Validate operation, solver, and domain state."""
        if operation is None or not isinstance(operation, SolidityCall):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        return True

    def _resolve_lvalue_info(
        self, operation: SolidityCall
    ) -> tuple[Optional[str], Optional[ElementaryType]]:
        """Resolve lvalue name and return type from operation."""
        lvalue: Optional["Variable"] = operation.lvalue
        if lvalue is None:
            return None, None

        lvalue_name: Optional[str] = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None, None

        return_type = self._resolve_return_type(operation, lvalue)
        if return_type is None or IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return None, None

        return lvalue_name, return_type

    def _resolve_return_type(
        self, operation: SolidityCall, lvalue: "Variable"
    ) -> Optional[ElementaryType]:
        """Resolve return type from operation or lvalue."""
        type_call: Union[str, List[ElementaryType], None] = getattr(operation, "type_call", None)
        if isinstance(type_call, list) and type_call:
            candidate: Union[str, ElementaryType] = type_call[0]
            resolved = IntervalSMTUtils.resolve_elementary_type(candidate)
            if resolved is not None:
                return resolved

        if hasattr(lvalue, "type"):
            return IntervalSMTUtils.resolve_elementary_type(lvalue.type)
        return None

    def _get_or_create_tracked(
        self, domain: "IntervalDomain", lvalue_name: str, return_type: ElementaryType
    ) -> Optional["TrackedSMTVariable"]:
        """Get existing or create new tracked variable."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(self.solver, lvalue_name, return_type)
        if tracked is None:
            return None
        domain.state.set_range_variable(lvalue_name, tracked)
        return tracked

    def _apply_byte_constraints(
        self, operation: SolidityCall, tracked: "TrackedSMTVariable", domain: "IntervalDomain"
    ) -> None:
        """Apply byte extraction constraints or fallback to unconstrained."""
        if operation.arguments and len(operation.arguments) >= 2:
            index_arg = operation.arguments[0]
            value_arg = operation.arguments[1]
            byte_constraint = self._extract_byte_constraint(index_arg, value_arg, tracked, domain)
            if byte_constraint is not None:
                self.solver.assert_constraint(byte_constraint)
                tracked.assert_no_overflow(self.solver)
                return

        tracked.assert_no_overflow(self.solver)

    def _extract_byte_constraint(
        self,
        index_arg: object,
        value_arg: object,
        result_var: "TrackedSMTVariable",
        domain: "IntervalDomain",
    ) -> Optional[SMTTerm]:
        """Extract byte constraint only if both arguments are constants or have range [x,x]."""
        if self.solver is None:
            return None

        # Get index value: must be constant or have range [x,x].
        index_value: Optional[int] = None
        if isinstance(index_arg, Constant):
            index_value = index_arg.value
            if not isinstance(index_value, int):
                return None
        else:
            # Check if index variable has single-value range [x,x].
            index_value = self._get_single_value(index_arg, domain)
            if index_value is None:
                return None

        # If index >= 32, byte() returns 0.
        if index_value >= 32:
            zero_const = self.solver.create_constant(0, result_var.sort)
            return result_var.term == zero_const

        # Get value: must be constant or have range [x,x].
        value: Optional[int] = None
        if isinstance(value_arg, Constant):
            value = value_arg.value
            if not isinstance(value, int):
                return None
        else:
            # Check if value variable has single-value range [x,x].
            value = self._get_single_value(value_arg, domain)
            if value is None:
                return None

        # Both are constants or single values: compute the byte directly.
        byte_value = (value >> ((31 - index_value) * 8)) & 0xFF
        byte_const = self.solver.create_constant(byte_value, result_var.sort)
        return result_var.term == byte_const

    def _get_single_value(self, arg: object, domain: "IntervalDomain") -> Optional[int]:
        """Check if variable has a single-value range [x,x], returning x if so, None otherwise."""
        arg_name = IntervalSMTUtils.resolve_variable_name(arg)
        if arg_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, arg_name)
        if tracked is None:
            return None

        # Check metadata for min/max values.
        metadata = getattr(tracked.base, "metadata", {})
        min_value = metadata.get("min_value")
        max_value = metadata.get("max_value")

        # If min == max, it's a single value.
        if min_value is not None and max_value is not None and min_value == max_value:
            return min_value

        return None
