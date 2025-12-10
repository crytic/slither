"""New elementary type operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.cfg.scope import Scope
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.new_elementary_type import NewElementaryType
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class NewElementaryTypeHandler(BaseOperationHandler):
    """Handler for new elementary type operations (e.g., new bytes(0)) in interval analysis."""

    def handle(
        self,
        operation: Optional[NewElementaryType],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle a new elementary type operation."""
        if operation is None or self.solver is None:
            return

        self.logger.debug(f"Handling new elementary type operation: {operation}")

        lvalue = operation.lvalue
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Resolve type: operation.type -> variable_return_type -> lvalue.type
        lvalue_type_attr = lvalue.type if hasattr(lvalue, "type") else None
        variable_return_type = getattr(operation, "variable_return_type", None)
        lvalue_type = IntervalSMTUtils.resolve_elementary_type(
            operation.type, variable_return_type
        )
        if lvalue_type is None:
            lvalue_type = IntervalSMTUtils.resolve_elementary_type(
                variable_return_type, lvalue_type_attr
            )
        if lvalue_type is None:
            self.logger.debug(
                "Unsupported lvalue type for new elementary type operation; skipping interval update."
            )
            return

        # Check if type is supported for interval analysis (numeric types, bool, address, bytes)
        if IntervalSMTUtils.solidity_type_to_smt_sort(lvalue_type) is None:
            self.logger.debug(
                "Elementary type '%s' not supported for interval analysis; skipping.",
                getattr(lvalue_type, "type", lvalue_type),
            )
            return

        # Fetch or create SMT variable for lvalue (new elementary type operations create new variables)
        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            lvalue_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, lvalue_type
            )
            if lvalue_var is None:
                self.logger.error_and_raise(
                    "Failed to create tracked variable for type '{type_name}' and variable '{var_name}'",
                    ValueError,
                    var_name=lvalue_name,
                    type_name=getattr(lvalue_type, "type", lvalue_type),
                    embed_on_error=True,
                    node=node,
                    operation=operation,
                    domain=domain,
                )
            domain.state.set_range_variable(lvalue_name, lvalue_var)

        # Initialize based on arguments
        if not operation.arguments:
            self._initialize_to_zero(lvalue_var)
        else:
            self._handle_argument_initialization(operation.arguments[0], lvalue_var, domain, node, operation)

        lvalue_var.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, lvalue_var)

    def _handle_argument_initialization(
        self,
        first_arg: object,
        lvalue_var: TrackedSMTVariable,
        domain: "IntervalDomain",
        node: "Node",
        operation: NewElementaryType,
    ) -> None:
        """Initialize lvalue from operation argument (constant or variable)."""
        if isinstance(first_arg, Constant):
            const_value = first_arg.value
            if isinstance(const_value, int):
                self._initialize_to_constant(lvalue_var, const_value)
                return
            self._initialize_to_zero(lvalue_var)
            return

        # Variable argument
        arg_name = IntervalSMTUtils.resolve_variable_name(first_arg)
        if arg_name is None:
            self._initialize_to_zero(lvalue_var)
            return

        arg_var = IntervalSMTUtils.get_tracked_variable(domain, arg_name)
        if arg_var is None:
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain for new elementary type argument",
                ValueError,
                var_name=arg_name,
                embed_on_error=True,
                node=node,
                operation=operation,
                domain=domain,
            )

        self._initialize_from_variable(lvalue_var, arg_var)

    def _initialize_to_zero(self, var: TrackedSMTVariable) -> None:
        """Initialize a variable to 0 (default value for new elementary types)."""
        self._initialize_to_constant(var, 0)

    def _initialize_to_constant(self, var: TrackedSMTVariable, value: int) -> None:
        """Initialize a variable to a constant value."""
        if self.solver is None:
            return
        const_term: SMTTerm = self.solver.create_constant(value, var.sort)
        constraint: SMTTerm = var.term == const_term
        self.solver.assert_constraint(constraint)

    def _initialize_from_variable(
        self, target_var: TrackedSMTVariable, source_var: TrackedSMTVariable
    ) -> None:
        """Initialize target variable from source variable with proper width handling."""
        if self.solver is None:
            return

        target_width = self.solver.bv_size(target_var.term)
        source_width = self.solver.bv_size(source_var.term)

        if target_width == source_width:
            # Same width, direct assignment
            constraint: SMTTerm = target_var.term == source_var.term
        elif source_width < target_width:
            # Extend source to target width (sign-extend if signed)
            is_signed = bool(source_var.base.metadata.get("is_signed", False))
            extended_term = IntervalSMTUtils.extend_to_width(
                self.solver, source_var.term, target_width, is_signed
            )
            constraint: SMTTerm = target_var.term == extended_term
        else:
            # Truncate source to target width
            truncated_term = IntervalSMTUtils.truncate_to_width(
                self.solver, source_var.term, target_width
            )
            constraint: SMTTerm = target_var.term == truncated_term

        self.solver.assert_constraint(constraint)


