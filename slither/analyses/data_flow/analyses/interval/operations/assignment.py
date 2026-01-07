"""Assignment operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.cfg.scope import Scope
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.core.declarations.solidity_variables import (
    SolidityVariableComposed,
    SolidityVariable,
)
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.reference_ssa import ReferenceVariableSSA
from slither.utils.integer_conversion import convert_string_to_int

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
        lvalue_type_attr = lvalue.type if hasattr(lvalue, "type") else None
        lvalue_type = IntervalSMTUtils.resolve_elementary_type(
            operation.variable_return_type, lvalue_type_attr
        )
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for assignment; skipping interval update.")
            return

        # Get is_checked from scope (Scope has attribute, Function has method)
        is_checked = False
        if isinstance(node.scope, Scope):
            is_checked = node.scope.is_checked
        elif isinstance(node.scope, Function):
            is_checked = node.scope.is_checked()

        # Fetch or create SMT variable for lvalue (assignments may create new variables)
        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            # Check if type is supported for interval analysis
            if IntervalSMTUtils.solidity_type_to_smt_sort(lvalue_type) is None:
                self.logger.debug(
                    "Elementary type '%s' not supported for interval analysis; skipping.",
                    getattr(lvalue_type, "type", lvalue_type),
                )
                return
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

        # Handle rvalue: constant or variable
        if isinstance(rvalue, Constant):
            # Handle constant assignment
            self.logger.debug(f"Handling constant assignment: {rvalue}")
            self._handle_constant_assignment(lvalue_var, rvalue, is_checked, lvalue_type)
        else:
            # Handle variable assignment
            rvalue_name = self._get_variable_name(rvalue)
            if rvalue_name is not None:
                if not self._handle_variable_assignment(
                    lvalue_var,
                    rvalue,
                    rvalue_name,
                    lvalue_name,
                    domain,
                    is_checked,
                    lvalue_type,
                    node,
                    operation,
                ):
                    return  # Unsupported rvalue type; skip update

        # Update domain state
        self.logger.debug(f"Setting range variable {lvalue_name} to {lvalue_var}")
        domain.state.set_range_variable(lvalue_name, lvalue_var)

        # If lvalue is a ReferenceVariable that points to a struct member, also update the struct member
        if hasattr(lvalue, "points_to") and lvalue.points_to is not None:
            self._update_struct_member_if_reference(lvalue, lvalue_var, domain, node, operation)

    def _get_variable_name(self, var: Union[object, Constant]) -> Optional[str]:
        """Extract variable name from SlitherIR variable."""
        return IntervalSMTUtils.resolve_variable_name(var)

    def _handle_variable_assignment(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue: object,
        rvalue_name: str,
        lvalue_name: str,
        domain: "IntervalDomain",
        is_checked: bool,
        fallback_type: Optional[ElementaryType],
        node: "Node",
        operation: Assignment,
    ) -> bool:
        """Process assignment from another variable; return False if unsupported."""
        rvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(rvalue, "type", None))
        if rvalue_type is None:
            rvalue_type = fallback_type
            if rvalue_type is None:
                self.logger.debug(
                    "Unsupported rvalue type for assignment; skipping interval update."
                )
                return False

        rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
        if rvalue_var is None:
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain for assignment rvalue",
                ValueError,
                var_name=rvalue_name,
                embed_on_error=True,
                node=node,
                operation=operation,
                domain=domain,
            )

        # Add constraint: lvalue == rvalue
        # First check if sizes match
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        rvalue_width = self.solver.bv_size(rvalue_var.term)
        if lvalue_width != rvalue_width:
            self.logger.error(
                f"Size mismatch in assignment: lvalue width={lvalue_width}, rvalue width={rvalue_width}"
            )
            # Extend or truncate rvalue to match lvalue
            rvalue_term = rvalue_var.term
            if rvalue_width < lvalue_width:
                # Extend rvalue - check if signed from metadata
                is_signed = bool(rvalue_var.base.metadata.get("is_signed", False))
                rvalue_term = IntervalSMTUtils.extend_to_width(
                    self.solver, rvalue_term, lvalue_width, is_signed
                )
            else:
                # Truncate rvalue
                rvalue_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, rvalue_term, lvalue_width
                )
            constraint: SMTTerm = lvalue_var.term == rvalue_term
        else:
            constraint: SMTTerm = lvalue_var.term == rvalue_var.term
        self.solver.assert_constraint(constraint)

        # Propagate binary operation mapping if rvalue has one
        # This allows require(condition) to find the original comparison when condition = TMP_0
        rvalue_binary_op = domain.state.get_binary_operation(rvalue_name)
        if rvalue_binary_op is not None:
            domain.state.set_binary_operation(lvalue_name, rvalue_binary_op)

        # Propagate bytes_length metadata if rvalue has it (for Length handler)
        rvalue_bytes_length = rvalue_var.base.metadata.get("bytes_length")
        if rvalue_bytes_length is not None:
            lvalue_var.base.metadata["bytes_length"] = rvalue_bytes_length

        # Handle overflow propagation
        if self._is_temporary_name(rvalue_name):
            # Temporary from an operation - copy its overflow status
            lvalue_var.copy_overflow_from(self.solver, rvalue_var)
            # In checked mode, operations must not overflow
            if is_checked:
                # Assert that the operation didn't overflow
                # This makes the solver UNSAT if overflow occurred
                lvalue_var.assert_no_overflow(self.solver)
        else:
            # Regular variable-to-variable assignment
            # The assignment itself doesn't cause overflow
            lvalue_var.assert_no_overflow(self.solver)

        return True

    def _handle_constant_assignment(
        self,
        lvalue_var: TrackedSMTVariable,
        constant: Constant,
        is_checked: bool,
        var_type: ElementaryType,
    ) -> None:
        """Handle assignment from a constant value."""
        if self.solver is None:
            return

        # Get constant value
        const_value = constant.value
        original_string_value = None

        # Convert hex string constants (e.g., bytes32) to integers
        if isinstance(const_value, str):
            original_string_value = const_value
            # Try to convert to integer - first try hex, then try ASCII string
            try:
                const_value = convert_string_to_int(const_value)
            except (ValueError, TypeError):
                # Not a hex string - try converting as ASCII string
                ascii_value = self._string_to_int(original_string_value)
                if ascii_value is not None:
                    const_value = ascii_value
                else:
                    self.logger.debug(
                        "Unable to convert constant string '%s' to integer; skipping.",
                        const_value,
                    )
                    return

        if not isinstance(const_value, int):
            return

        # Store byte length metadata for bytes/string constants
        # This allows the Length handler to get the actual length
        if original_string_value is not None:
            byte_length = self._compute_byte_length(original_string_value)
            if byte_length is not None:
                lvalue_var.base.metadata["bytes_length"] = byte_length

        # Create constant term using solver's create_constant method
        const_term: SMTTerm = self.solver.create_constant(const_value, lvalue_var.sort)

        # Add constraint: lvalue == constant
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)

        # Constants cannot overflow
        lvalue_var.assert_no_overflow(self.solver)

    @staticmethod
    def _compute_byte_length(string_value: str) -> Optional[int]:
        """Compute the byte length of a hex string or regular string constant."""
        # Handle hex strings (0x prefix)
        if string_value.startswith("0x") or string_value.startswith("0X"):
            hex_part = string_value[2:]
            # Each 2 hex chars = 1 byte
            return len(hex_part) // 2
        # Handle regular string literals
        return len(string_value)

    @staticmethod
    def _string_to_int(string_value: str) -> Optional[int]:
        """Convert a regular ASCII string to its big-endian integer representation."""
        # Handle hex strings with convert_string_to_int
        if string_value.startswith("0x") or string_value.startswith("0X"):
            return None  # Let convert_string_to_int handle it
        # Convert ASCII string to bytes, then to big-endian integer
        try:
            string_bytes = string_value.encode("utf-8")
            return int.from_bytes(string_bytes, byteorder="big")
        except (UnicodeEncodeError, ValueError):
            return None

    @staticmethod
    def _is_temporary_name(name: str) -> bool:
        """Heuristic detection of compiler-generated temporaries."""
        if not name:
            return False
        short_name = name.split(".")[-1]
        return short_name.startswith("TMP")

    @staticmethod
    def _is_solidity_variable(var: object) -> bool:
        """Check if variable is a Solidity global variable (should have full range, not initialized to 0)."""
        return isinstance(var, (SolidityVariableComposed, SolidityVariable))

    def _initialize_variable_to_zero(self, var: TrackedSMTVariable) -> None:
        """Initialize a variable to 0 (Solidity default value for uninitialized variables)."""
        if self.solver is None:
            return
        zero_constant = self.solver.create_constant(0, var.sort)
        self.solver.assert_constraint(var.term == zero_constant)

    def _update_struct_member_if_reference(
        self,
        lvalue: object,
        lvalue_var: TrackedSMTVariable,
        domain: "IntervalDomain",
        node: "Node",
        operation: Assignment,
    ) -> None:
        """Update struct member when assigning to a reference variable that points to a struct member."""
        if self.solver is None:
            return

        # Guard: only process ReferenceVariable lvalues
        if not isinstance(lvalue, (ReferenceVariable, ReferenceVariableSSA)):
            return

        # Find struct member variables that might be constrained to equal this reference
        # Look for variables with pattern "*.member_name" where the base matches points_to
        points_to = getattr(lvalue, "points_to", None)
        if points_to is None:
            return

        points_to_name = IntervalSMTUtils.resolve_variable_name(points_to)
        if points_to_name is None:
            return

        # Search for struct member variables that start with the points_to name
        # and are constrained to equal this reference
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Find all variables in domain that match the pattern "{points_to_name}.*"
        # and check if they're constrained to equal lvalue_var
        for var_name, tracked_var in domain.state.get_range_variables().items():
            # Check if this variable name matches the pattern of a struct member
            if "." in var_name:
                base_name = var_name.split(".", 1)[0]
                # Check if base name matches (accounting for SSA versions)
                if base_name.startswith(points_to_name) or points_to_name.startswith(
                    base_name.split("|")[0]
                ):
                    # This might be the struct member - update it to match the reference
                    # The constraint REF == struct.member should already exist from Member handler
                    # We just need to ensure the struct member is updated when REF is updated
                    # Since they're constrained to be equal, updating REF should propagate
                    # But we can explicitly update the struct member to be safe
                    member_width = self.solver.bv_size(tracked_var.term)
                    ref_width = self.solver.bv_size(lvalue_var.term)

                    if member_width == ref_width:
                        # Explicitly constrain struct member to equal the reference
                        constraint: SMTTerm = tracked_var.term == lvalue_var.term
                        self.solver.assert_constraint(constraint)
                        self.logger.debug(
                            "Updated struct member '{member}' to match reference '{ref}'",
                            member=var_name,
                            ref=lvalue_name,
                        )
                        # Only update the first matching struct member (should be unique per reference)
                        break
