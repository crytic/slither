"""Assignment operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind, SMTVariable, SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant

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

        lvalue = operation.lvalue
        rvalue = operation.rvalue

        # Get variable name for lvalue
        lvalue_name = self._get_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Get or create SMT variable for lvalue
        lvalue_smt_var = self._get_or_create_smt_variable(
            lvalue_name, operation.variable_return_type, domain
        )
        if lvalue_smt_var is None:
            return

        # Handle rvalue: constant or variable
        if isinstance(rvalue, Constant):
            # Handle constant assignment
            self._handle_constant_assignment(lvalue_smt_var, rvalue)
        else:
            # Handle variable assignment
            rvalue_name = self._get_variable_name(rvalue)
            if rvalue_name is not None:
                rvalue_smt_var = self._get_or_create_smt_variable(rvalue_name, rvalue.type, domain)
                if rvalue_smt_var is not None:
                    # Add constraint: lvalue == rvalue
                    # Use the term property which supports operator overloading
                    constraint: SMTTerm = lvalue_smt_var.term == rvalue_smt_var.term
                    self.solver.assert_constraint(constraint)

        # Update domain state
        domain.state.set_range_variable(lvalue_name, lvalue_smt_var)

    def _get_variable_name(self, var: Union[object, Constant]) -> Optional[str]:
        """Extract variable name from SlitherIR variable."""
        if hasattr(var, "name") and var.name:
            return var.name
        if hasattr(var, "ssa_name") and var.ssa_name:
            return var.ssa_name
        return None

    def _get_or_create_smt_variable(
        self, var_name: str, var_type: object, domain: "IntervalDomain"
    ) -> Optional[SMTVariable]:
        """Get existing SMT variable from domain or create a new one."""
        # Check if variable already exists in domain
        existing_var = domain.state.get_range_variable(var_name)
        if existing_var is not None:
            return existing_var

        # Create new SMT variable
        sort = self._solidity_type_to_smt_sort(var_type)
        if sort is None:
            return None

        if self.solver is None:
            return None

        smt_var = self.solver.declare_const(var_name, sort)
        return smt_var

    def _solidity_type_to_smt_sort(self, solidity_type: object) -> Optional[Sort]:
        """Convert Solidity type to SMT sort."""
        if not isinstance(solidity_type, ElementaryType):
            return None

        type_str = str(solidity_type.type)

        # Handle uint types
        if type_str in Uint:
            # Extract bit width (default to 256)
            if type_str == "uint":
                width = 256
            else:
                width = int(type_str.replace("uint", ""))
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        # Handle int types
        if type_str in Int:
            # Extract bit width (default to 256)
            if type_str == "int":
                width = 256
            else:
                width = int(type_str.replace("int", ""))
            return Sort(kind=SortKind.BITVEC, parameters=[width])

        # Handle bool
        if type_str == "bool":
            return Sort(kind=SortKind.BOOL)

        return None

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
