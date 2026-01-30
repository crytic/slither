"""Unary operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.unary import Unary, UnaryType
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class UnaryHandler(BaseOperationHandler):
    """Handler for unary operations (!, ~) in interval analysis."""

    def handle(
        self,
        operation: Optional[Unary],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle a unary operation."""
        if not self._validate_operation(operation, domain):
            return

        lvalue_name, lvalue_type = self._resolve_lvalue(operation)
        if lvalue_name is None or lvalue_type is None:
            return

        lvalue_tracked = self._get_or_create_lvalue_var(lvalue_name, lvalue_type, domain)
        if lvalue_tracked is None:
            return

        if not self._handle_rvalue(operation, lvalue_tracked, lvalue_type, domain):
            return

        lvalue_tracked.assert_no_overflow(self.solver)
        self.logger.debug(
            "Handled unary operation: {op_type} {rvalue} -> {lvalue}",
            op_type=operation.type,
            rvalue=operation.rvalue,
            lvalue=lvalue_name,
        )

    def _validate_operation(
        self, operation: Optional[Unary], domain: "IntervalDomain"
    ) -> bool:
        """Validate the operation can be processed."""
        if operation is None or not isinstance(operation, Unary):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        if operation.lvalue is None:
            return False
        return True

    def _resolve_lvalue(
        self, operation: Unary
    ) -> tuple[Optional[str], Optional[ElementaryType]]:
        """Resolve lvalue name and type."""
        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None, None

        lvalue_type: Optional[ElementaryType] = None
        if hasattr(lvalue, "type"):
            lvalue_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        if lvalue_type is None:
            return None, None
        if IntervalSMTUtils.solidity_type_to_smt_sort(lvalue_type) is None:
            return None, None

        return lvalue_name, lvalue_type

    def _get_or_create_lvalue_var(
        self,
        lvalue_name: str,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional[TrackedSMTVariable]:
        """Get or create tracked variable for the lvalue."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, lvalue_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(lvalue_name, tracked)
        return tracked

    def _handle_rvalue(
        self,
        operation: Unary,
        lvalue_tracked: TrackedSMTVariable,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> bool:
        """Handle the rvalue operand. Returns True if handled successfully."""
        rvalue = operation.rvalue
        if isinstance(rvalue, Constant):
            self._handle_constant_unary(
                lvalue_tracked, rvalue, operation.type, lvalue_type
            )
            return True

        rvalue_tracked = self._get_or_create_rvalue_var(rvalue, lvalue_type, domain)
        if rvalue_tracked is None:
            return False

        self._handle_variable_unary(
            lvalue_tracked, rvalue_tracked, operation.type, lvalue_type
        )
        return True

    def _get_or_create_rvalue_var(
        self,
        rvalue: object,
        fallback_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional[TrackedSMTVariable]:
        """Get or create tracked variable for the rvalue."""
        rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
        if rvalue_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
        if tracked is not None:
            return tracked

        rvalue_type = IntervalSMTUtils.resolve_elementary_type(
            getattr(rvalue, "type", None)
        )
        if rvalue_type is None:
            rvalue_type = fallback_type

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, rvalue_name, rvalue_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(rvalue_name, tracked)
        return tracked

    def _handle_constant_unary(
        self,
        lvalue_var: TrackedSMTVariable,
        constant: Constant,
        unary_type: UnaryType,
        result_type: ElementaryType,
    ) -> None:
        """Handle unary operation on a constant value."""
        if self.solver is None:
            return

        const_value = constant.value
        if not isinstance(const_value, int):
            return

        # Compute the result based on unary type
        if unary_type == UnaryType.BANG:
            # Logical NOT: result is 1 if operand is 0, else 0
            result_value = 1 if const_value == 0 else 0
        elif unary_type == UnaryType.TILD:
            # Bitwise NOT: flip all bits
            # Get bit width from result type
            bit_width = IntervalSMTUtils.type_bit_width(result_type)
            mask = (1 << bit_width) - 1
            result_value = (~const_value) & mask
        else:
            return

        # Create constant term for the result
        const_term: SMTTerm = self.solver.create_constant(result_value, lvalue_var.sort)

        # Add constraint: lvalue == result
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)

    def _handle_variable_unary(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue_var: TrackedSMTVariable,
        unary_type: UnaryType,
        result_type: ElementaryType,
    ) -> None:
        """Handle unary operation on a variable."""
        if self.solver is None:
            return

        if unary_type == UnaryType.BANG:
            # Logical NOT: result is 1 if operand is 0, else 0
            # This requires an if-then-else in SMT
            zero = self.solver.create_constant(0, rvalue_var.sort)
            one = self.solver.create_constant(1, lvalue_var.sort)
            zero_result = self.solver.create_constant(0, lvalue_var.sort)

            # Condition: rvalue == 0
            is_zero = rvalue_var.term == zero

            # If rvalue == 0, result is 1; else result is 0
            result_term = self.solver.make_ite(is_zero, one, zero_result)
            constraint: SMTTerm = lvalue_var.term == result_term
            self.solver.assert_constraint(constraint)

        elif unary_type == UnaryType.TILD:
            # Bitwise NOT: flip all bits using solver's bv_not
            not_term = self.solver.bv_not(rvalue_var.term)

            # Handle potential width mismatch
            lvalue_width = self.solver.bv_size(lvalue_var.term)
            rvalue_width = self.solver.bv_size(not_term)

            if lvalue_width != rvalue_width:
                # Extend or truncate as needed
                if rvalue_width < lvalue_width:
                    is_signed = IntervalSMTUtils.is_signed_type(result_type)
                    not_term = IntervalSMTUtils.extend_to_width(
                        self.solver, not_term, lvalue_width, is_signed
                    )
                else:
                    not_term = IntervalSMTUtils.truncate_to_width(
                        self.solver, not_term, lvalue_width
                    )

            constraint: SMTTerm = lvalue_var.term == not_term
            self.solver.assert_constraint(constraint)
