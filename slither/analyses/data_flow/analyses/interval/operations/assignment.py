"""Assignment operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class AssignmentHandler(BaseOperationHandler):
    """Handler for assignment operations in interval analysis."""

    def handle(
        self,
        operation: Optional[Assignment],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """
        Handle an assignment operation.

        Args:
            operation: The assignment operation
            domain: The current interval domain
            node: The CFG node containing the operation
        """
        if operation is None or self.solver is None:
            return

        self.logger.debug(f"Handling assignment operation: {operation}")

        lvalue = operation.lvalue
        rvalue = operation.rvalue

        # Get variable name for lvalue
        lvalue_name = self._get_variable_name(lvalue)
        self._logger.debug(f"Lvalue name: {lvalue_name}")
        if lvalue_name is None:
            return

        # Determine the best type information available for the lvalue
        lvalue_type = IntervalSMTUtils.resolve_elementary_type(
            operation.variable_return_type, getattr(lvalue, "type", None)
        )
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for assignment; skipping interval update.")
            return

        # Fetch or create SMT variable for lvalue
        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            lvalue_var = self._create_tracked_variable(lvalue_name, lvalue_type)
            if lvalue_var is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_var)

        # Handle rvalue: constant or variable
        if isinstance(rvalue, Constant):
            # Handle constant assignment
            self.logger.debug(f"Handling constant assignment: {rvalue}")
            self._handle_constant_assignment(lvalue_var, rvalue)
        else:
            # Handle variable assignment
            rvalue_name = self._get_variable_name(rvalue)
            if rvalue_name is not None:
                if not self._handle_variable_assignment(lvalue_var, rvalue, rvalue_name, domain):
                    return  # Unsupported rvalue type; skip update

        # Update domain state
        self.logger.debug(f"Setting range variable {lvalue_name} to {lvalue_var}")
        domain.state.set_range_variable(lvalue_name, lvalue_var)

    def _get_variable_name(self, var: Union[object, Constant]) -> Optional[str]:
        """Extract variable name from SlitherIR variable."""
        return IntervalSMTUtils.resolve_variable_name(var)

    def _handle_variable_assignment(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue: object,
        rvalue_name: str,
        domain: "IntervalDomain",
    ) -> bool:
        """Process assignment from another variable; return False if unsupported."""
        rvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(rvalue, "type", None))
        if rvalue_type is None:
            self.logger.debug("Unsupported rvalue type for assignment; skipping interval update.")
            return False

        rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
        if rvalue_var is None:
            rvalue_var = self._create_tracked_variable(rvalue_name, rvalue_type)
            if rvalue_var is None:
                return False
            domain.state.set_range_variable(rvalue_name, rvalue_var)

        # Add constraint: lvalue == rvalue
        constraint: SMTTerm = lvalue_var.term == rvalue_var.term
        self.solver.assert_constraint(constraint)

        if self._is_temporary_name(rvalue_name):
            lvalue_var.copy_overflow_from(self.solver, rvalue_var)
        else:
            lvalue_var.assert_no_overflow(self.solver)
        return True

    def _handle_constant_assignment(
        self, lvalue_var: TrackedSMTVariable, constant: Constant
    ) -> None:
        """Handle assignment from a constant value."""
        if self.solver is None:
            return

        # Get constant value
        const_value = constant.value
        if not isinstance(const_value, int):
            return

        # Create constant term using solver's create_constant method
        const_term: SMTTerm = self.solver.create_constant(const_value, lvalue_var.sort)

        # Add constraint: lvalue == constant
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)

        # Constants cannot overflow
        lvalue_var.assert_no_overflow(self.solver)

    def _create_tracked_variable(
        self, var_name: str, var_type: ElementaryType
    ) -> Optional[TrackedSMTVariable]:
        """Create a new SMT variable using the shared utilities with logging."""
        if self.solver is None:
            return None

        tracked_var = IntervalSMTUtils.create_tracked_variable(self.solver, var_name, var_type)
        if tracked_var is None:
            self.logger.error(
                "Unsupported elementary type '%s' for variable '%s'; skipping interval update.",
                getattr(var_type, "type", var_type),
                var_name,
            )
            return None

        return tracked_var

    @staticmethod
    def _is_temporary_name(name: str) -> bool:
        """Heuristic detection of compiler-generated temporaries."""
        if not name:
            return False
        short_name = name.split(".")[-1]
        return short_name.startswith("TMP")
