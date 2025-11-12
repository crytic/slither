"""Assignment operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTVariable, SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils

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
        lvalue_type = self._resolve_elementary_type(
            operation.variable_return_type, getattr(lvalue, "type", None)
        )
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for assignment; skipping interval update.")
            return

        # Fetch or create SMT variable for lvalue
        lvalue_smt_var = IntervalSMTUtils.get_smt_variable(domain, lvalue_name)
        if lvalue_smt_var is None:
            lvalue_smt_var = self._create_smt_variable(lvalue_name, lvalue_type)
            if lvalue_smt_var is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_smt_var)

        # Handle rvalue: constant or variable
        if isinstance(rvalue, Constant):
            # Handle constant assignment
            self.logger.debug(f"Handling constant assignment: {rvalue}")
            self._handle_constant_assignment(lvalue_smt_var, rvalue)
        else:
            # Handle variable assignment
            rvalue_name = self._get_variable_name(rvalue)
            if rvalue_name is not None:
                if not self._handle_variable_assignment(
                    lvalue_smt_var, rvalue, rvalue_name, domain
                ):
                    return  # Unsupported rvalue type; skip update

        # Update domain state
        self.logger.debug(f"Setting range variable {lvalue_name} to {lvalue_smt_var}")
        domain.state.set_range_variable(lvalue_name, lvalue_smt_var)

    def _get_variable_name(self, var: Union[object, Constant]) -> Optional[str]:
        """Extract variable name from SlitherIR variable."""
        return IntervalSMTUtils.resolve_variable_name(var)

    def _resolve_elementary_type(
        self, primary: Optional[object], fallback: Optional[object] = None
    ) -> Optional[ElementaryType]:
        """Return the first available ElementaryType from the provided candidates."""
        for candidate in (primary, fallback):
            if isinstance(candidate, ElementaryType):
                return candidate
            if candidate is not None and hasattr(candidate, "type"):
                nested_type = getattr(candidate, "type")
                if isinstance(nested_type, ElementaryType):
                    return nested_type
        return None

    def _handle_variable_assignment(
        self,
        lvalue_smt_var: SMTVariable,
        rvalue: object,
        rvalue_name: str,
        domain: "IntervalDomain",
    ) -> bool:
        """Process assignment from another variable; return False if unsupported."""
        rvalue_type = self._resolve_elementary_type(getattr(rvalue, "type", None))
        if rvalue_type is None:
            self.logger.debug("Unsupported rvalue type for assignment; skipping interval update.")
            return False

        rvalue_smt_var = IntervalSMTUtils.get_smt_variable(domain, rvalue_name)
        if rvalue_smt_var is None:
            rvalue_smt_var = self._create_smt_variable(rvalue_name, rvalue_type)
            if rvalue_smt_var is None:
                return False
            domain.state.set_range_variable(rvalue_name, rvalue_smt_var)

        if rvalue_smt_var is None:
            return False

        # Add constraint: lvalue == rvalue
        # Use the term property which supports operator overloading
        constraint: SMTTerm = lvalue_smt_var.term == rvalue_smt_var.term
        self.solver.assert_constraint(constraint)
        return True

    def _handle_constant_assignment(self, lvalue_smt_var: SMTVariable, constant: Constant) -> None:
        """Handle assignment from a constant value."""
        if self.solver is None:
            return

        # Get constant value
        const_value = constant.value
        if not isinstance(const_value, int):
            return

        # Create constant term using solver's create_constant method
        const_term: SMTTerm = self.solver.create_constant(const_value, lvalue_smt_var.sort)

        # Add constraint: lvalue == constant
        # Use the term property which supports operator overloading
        constraint: SMTTerm = lvalue_smt_var.term == const_term
        self.solver.assert_constraint(constraint)

    def _create_smt_variable(
        self, var_name: str, var_type: ElementaryType
    ) -> Optional[SMTVariable]:
        """Create a new SMT variable using the shared utilities with logging."""
        if self.solver is None:
            return None

        smt_var = IntervalSMTUtils.create_smt_variable(self.solver, var_name, var_type)
        if smt_var is None:
            self.logger.error(
                "Unsupported elementary type '%s' for variable '%s'; skipping interval update.",
                getattr(var_type, "type", var_type),
                var_name,
            )
        return smt_var
