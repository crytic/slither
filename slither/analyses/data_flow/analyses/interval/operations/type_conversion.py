"""Type conversion operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class TypeConversionHandler(BaseOperationHandler):
    """Handler for type conversion operations in interval analysis."""

    def handle(
        self,
        operation: Optional[TypeConversion],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """
        Handle a type conversion operation.
        """
        if operation is None or self.solver is None:
            return

        self.logger.debug(f"Handling type conversion operation: {operation}")

        lvalue = operation.lvalue
        variable = operation.variable
        target_type = operation.type

        # Only handle ElementaryType conversions for now
        if not isinstance(target_type, ElementaryType):
            self.logger.debug(
                f"Type conversion to non-elementary type {target_type}; skipping interval update."
            )
            return

        # Get variable name for lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Fetch or create SMT variable for lvalue (type conversion operations create new variables)
        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            # Check if target type is supported for interval analysis
            if IntervalSMTUtils.solidity_type_to_smt_sort(target_type) is None:
                self.logger.debug(
                    "Elementary type '%s' not supported for interval analysis; skipping.",
                    getattr(target_type, "type", target_type),
                )
                return
            lvalue_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, target_type
            )
            if lvalue_var is None:
                self.logger.error_and_raise(
                    "Failed to create tracked variable for type '{type_name}' and variable '{var_name}'",
                    ValueError,
                    var_name=lvalue_name,
                    type_name=getattr(target_type, "type", target_type),
                    embed_on_error=True,
                    node=node,
                    operation=operation,
                    domain=domain,
                )
            domain.state.set_range_variable(lvalue_name, lvalue_var)

        # Handle constant conversion
        if isinstance(variable, Constant):
            self._handle_constant_conversion(lvalue_var, variable, target_type)
        else:
            # Handle variable conversion
            variable_name = IntervalSMTUtils.resolve_variable_name(variable)
            if variable_name is None:
                return

            # Get source variable type
            source_type = IntervalSMTUtils.resolve_elementary_type(getattr(variable, "type", None))
            if source_type is None:
                self.logger.debug(
                    "Unsupported source type for type conversion; skipping interval update."
                )
                return

            # Fetch SMT variable for source variable (must already exist in domain)
            source_var = IntervalSMTUtils.get_tracked_variable(domain, variable_name)
            if source_var is None:
                self.logger.error_and_raise(
                    "Variable '{var_name}' not found in domain for type conversion source",
                    ValueError,
                    var_name=variable_name,
                    embed_on_error=True,
                    node=node,
                    operation=operation,
                    domain=domain,
                )

            # Handle type conversion: extend or truncate as needed
            source_width = self.solver.bv_size(source_var.term)
            target_width = self.solver.bv_size(lvalue_var.term)

            if source_width == target_width:
                # Same width, direct assignment
                constraint: SMTTerm = lvalue_var.term == source_var.term
            elif source_width < target_width:
                # Extend source to target width
                is_signed = IntervalSMTUtils.is_signed_type(source_type)
                extended_term = IntervalSMTUtils.extend_to_width(
                    self.solver, source_var.term, target_width, is_signed
                )
                constraint: SMTTerm = lvalue_var.term == extended_term
            else:
                # Truncate source to target width
                truncated_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, source_var.term, target_width
                )
                constraint: SMTTerm = lvalue_var.term == truncated_term

            self.solver.assert_constraint(constraint)

        # Type conversions don't cause overflow
        lvalue_var.assert_no_overflow(self.solver)

        # Update domain state
        domain.state.set_range_variable(lvalue_name, lvalue_var)

    def _handle_constant_conversion(
        self,
        lvalue_var: TrackedSMTVariable,
        constant: Constant,
        target_type: ElementaryType,
    ) -> None:
        """Handle type conversion from a constant value."""
        if self.solver is None:
            return

        # Get constant value
        const_value = constant.value
        if not isinstance(const_value, int):
            return

        # Create constant term using solver's create_constant method with target type width
        const_term: SMTTerm = self.solver.create_constant(const_value, lvalue_var.sort)

        # Add constraint: lvalue == constant
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)

        # Constants cannot overflow
        lvalue_var.assert_no_overflow(self.solver)
