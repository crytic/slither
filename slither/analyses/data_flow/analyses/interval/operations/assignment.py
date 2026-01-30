"""Assignment operation handler for interval analysis."""

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.cfg.scope import Scope
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.declarations.structure import Structure
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
            self._handle_constant_assignment(lvalue_var, rvalue, is_checked, lvalue_type, lvalue_name, domain)
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

        # If lvalue is a ReferenceVariable that points to a struct member or array element, also update it
        if hasattr(lvalue, "points_to") and lvalue.points_to is not None:
            self._update_struct_member_if_reference(lvalue, lvalue_var, domain, node, operation)
            self._update_array_element_if_reference(lvalue, lvalue_var, domain, node, operation)

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
        rvalue_var = self._resolve_rvalue_variable(
            rvalue, rvalue_name, fallback_type, domain, node, operation
        )
        if rvalue_var is None:
            return False

        self._apply_assignment_constraint(lvalue_var, rvalue_var)
        self._propagate_assignment_metadata(lvalue_var, rvalue_var, lvalue_name, rvalue_name, domain)
        self._handle_assignment_overflow(lvalue_var, rvalue_var, rvalue_name, is_checked)
        return True

    def _resolve_rvalue_variable(
        self,
        rvalue: object,
        rvalue_name: str,
        fallback_type: Optional[ElementaryType],
        domain: "IntervalDomain",
        node: "Node",
        operation: Assignment,
    ) -> Optional[TrackedSMTVariable]:
        """Resolve the rvalue to a tracked variable, creating if needed."""
        rvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(rvalue, "type", None))
        if rvalue_type is None:
            rvalue_type = fallback_type
            if rvalue_type is None:
                self.logger.debug("Unsupported rvalue type; skipping.")
                return None

        rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
        if rvalue_var is not None:
            return rvalue_var

        # Try to materialize struct fields
        rvalue_actual_type = getattr(rvalue, "type", None)
        if isinstance(rvalue_actual_type, UserDefinedType) and isinstance(
            rvalue_actual_type.type, Structure
        ):
            self._materialize_struct_fields(domain, rvalue_name, rvalue_actual_type.type)
            return None

        # Synthesize a tracked variable
        return self._synthesize_rvalue_variable(
            rvalue_name, rvalue_actual_type, rvalue_type, domain, node, operation
        )

    def _synthesize_rvalue_variable(
        self,
        rvalue_name: str,
        rvalue_actual_type: object,
        rvalue_type: ElementaryType,
        domain: "IntervalDomain",
        node: "Node",
        operation: Assignment,
    ) -> Optional[TrackedSMTVariable]:
        """Create a new tracked variable for the rvalue."""
        candidate_type = IntervalSMTUtils.resolve_elementary_type(rvalue_actual_type) or rvalue_type
        if (
            candidate_type is None
            or IntervalSMTUtils.solidity_type_to_smt_sort(candidate_type) is None
            or self.solver is None
        ):
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain",
                ValueError,
                var_name=rvalue_name,
                embed_on_error=True,
                node=node, operation=operation, domain=domain,
            )

        rvalue_var = IntervalSMTUtils.create_tracked_variable(
            self.solver, rvalue_name, candidate_type
        )
        if rvalue_var is None:
            self.logger.error_and_raise(
                "Could not synthesize variable '{var_name}'",
                ValueError,
                var_name=rvalue_name,
                embed_on_error=True,
                node=node, operation=operation, domain=domain,
            )
        domain.state.set_range_variable(rvalue_name, rvalue_var)
        return rvalue_var

    def _apply_assignment_constraint(
        self, lvalue_var: TrackedSMTVariable, rvalue_var: TrackedSMTVariable
    ) -> None:
        """Apply the equality constraint between lvalue and rvalue."""
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        rvalue_width = self.solver.bv_size(rvalue_var.term)

        if lvalue_width != rvalue_width:
            rvalue_term = self._adjust_term_width(rvalue_var, lvalue_width, rvalue_width)
            constraint = lvalue_var.term == rvalue_term
        else:
            constraint = lvalue_var.term == rvalue_var.term
        self.solver.assert_constraint(constraint)

    def _adjust_term_width(
        self, rvalue_var: TrackedSMTVariable, target_width: int, current_width: int
    ) -> SMTTerm:
        """Adjust rvalue term width to match target."""
        rvalue_term = rvalue_var.term
        if current_width < target_width:
            is_signed = bool(rvalue_var.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(
                self.solver, rvalue_term, target_width, is_signed
            )
        return IntervalSMTUtils.truncate_to_width(self.solver, rvalue_term, target_width)

    def _propagate_assignment_metadata(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue_var: TrackedSMTVariable,
        lvalue_name: str,
        rvalue_name: str,
        domain: "IntervalDomain",
    ) -> None:
        """Propagate metadata from rvalue to lvalue."""
        # Propagate binary operation mapping
        rvalue_binary_op = domain.state.get_binary_operation(rvalue_name)
        if rvalue_binary_op is not None:
            domain.state.set_binary_operation(lvalue_name, rvalue_binary_op)

        # Propagate bytes_length metadata
        rvalue_bytes_length = rvalue_var.base.metadata.get("bytes_length")
        if rvalue_bytes_length is not None:
            lvalue_var.base.metadata["bytes_length"] = rvalue_bytes_length

        # Propagate safety context
        self._propagate_safety_context(rvalue_name, lvalue_name)

    def _handle_assignment_overflow(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue_var: TrackedSMTVariable,
        rvalue_name: str,
        is_checked: bool,
    ) -> None:
        """Handle overflow propagation for assignment."""
        if self._is_temporary_name(rvalue_name):
            lvalue_var.copy_overflow_from(self.solver, rvalue_var)
            if is_checked:
                lvalue_var.assert_no_overflow(self.solver)
        else:
            lvalue_var.assert_no_overflow(self.solver)

    def _materialize_struct_fields(
        self, domain: "IntervalDomain", base_name: str, struct_type: Structure
    ) -> None:
        """Recursively create tracked variables for struct fields down to elementary leaves."""
        if self.solver is None:
            return

        for member in struct_type.elems_ordered:
            member_type = getattr(member, "type", None)
            member_name = getattr(member, "name", None)
            if member_name is None or member_type is None:
                continue

            member_base = f"{base_name}.{member_name}"

            if isinstance(member_type, ElementaryType):
                if IntervalSMTUtils.solidity_type_to_smt_sort(member_type) is None:
                    continue
                tracked = IntervalSMTUtils.create_tracked_variable(
                    self.solver, member_base, member_type
                )
                if tracked:
                    domain.state.set_range_variable(member_base, tracked)
                continue

            if isinstance(member_type, UserDefinedType) and isinstance(member_type.type, Structure):
                self._materialize_struct_fields(domain, member_base, member_type.type)
                continue

            # Skip unsupported member types (arrays/mappings) for now.

    def _handle_constant_assignment(
        self,
        lvalue_var: TrackedSMTVariable,
        constant: Constant,
        is_checked: bool,
        var_type: ElementaryType,
        lvalue_name: Optional[str] = None,
        domain: Optional["IntervalDomain"] = None,
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
        
        # Track bytes memory constants: if this is a bytes memory variable with hex string content,
        # store the concrete byte content for memory load operations
        if original_string_value is not None and var_type is not None and lvalue_name is not None and domain is not None:
            # Check if this is a bytes memory type (dynamic bytes, not bytes32/bytes1/etc)
            type_str = getattr(var_type, "type", None)
            # bytes (dynamic) has type "bytes" exactly, bytes32 has type "bytes32"
            if type_str == "bytes":
                # Convert hex string to bytes
                try:
                    if original_string_value.startswith("0x") or original_string_value.startswith("0X"):
                        hex_part = original_string_value[2:]
                        # Remove any whitespace
                        hex_part = hex_part.replace(" ", "").replace("\n", "")
                        # Convert to bytes
                        byte_content = bytes.fromhex(hex_part)
                        # Store in domain state for memory load tracking
                        domain.state.set_bytes_memory_constant(lvalue_name, byte_content)
                        self.logger.debug(
                            "Stored bytes memory constant for '{name}': {length} bytes",
                            name=lvalue_name,
                            length=len(byte_content),
                        )
                except (ValueError, TypeError) as e:
                    # Not a valid hex string, skip
                    self.logger.debug(
                        "Could not convert hex string to bytes for '{name}': {error}",
                        name=lvalue_name,
                        error=str(e),
                    )

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

    def _propagate_safety_context(self, rvalue_name: str, lvalue_name: str) -> None:
        """Propagate safety context from rvalue to lvalue for memory safety analysis.

        This ensures that when a temporary variable (e.g., TMP_0 from mload(0x40))
        is assigned to a named variable (e.g., ptr), the safety context is preserved.
        """
        if self.analysis is None:
            return

        safety_ctx = self.analysis.safety_context

        # Propagate free memory pointer tracking
        if rvalue_name in safety_ctx.free_memory_pointers:
            safety_ctx.free_memory_pointers.add(lvalue_name)
            self.logger.debug(
                "Propagated free memory pointer from '{rvalue}' to '{lvalue}'",
                rvalue=rvalue_name,
                lvalue=lvalue_name,
            )

        # Propagate calldata variable tracking
        if rvalue_name in safety_ctx.calldata_variables:
            safety_ctx.calldata_variables.add(lvalue_name)
            self.logger.debug(
                "Propagated calldata variable from '{rvalue}' to '{lvalue}'",
                rvalue=rvalue_name,
                lvalue=lvalue_name,
            )

        # Propagate pointer arithmetic tracking
        if rvalue_name in safety_ctx.pointer_arithmetic:
            arith_info = safety_ctx.pointer_arithmetic[rvalue_name]
            safety_ctx.pointer_arithmetic[lvalue_name] = arith_info.copy()
            self.logger.debug(
                "Propagated pointer arithmetic from '{rvalue}' to '{lvalue}'",
                rvalue=rvalue_name,
                lvalue=lvalue_name,
            )

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

        # Use prefix index for fast lookup of struct member variables
        # Look for "{points_to_name}." prefix
        prefix = points_to_name + "."
        candidate_vars = domain.state.get_variables_by_prefix(prefix)

        # Also check with base name (without SSA version) if different
        points_to_base = points_to_name.split("|")[0] if "|" in points_to_name else None
        if points_to_base and points_to_base != points_to_name:
            candidate_vars = candidate_vars.union(domain.state.get_variables_by_prefix(points_to_base + "."))

        for var_name in candidate_vars:
            tracked_var = domain.state.range_variables.get(var_name)
            if tracked_var is None:
                continue

            # Check if this variable name matches the pattern of a struct member
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

    def _update_array_element_if_reference(
        self,
        lvalue: object,
        lvalue_var: TrackedSMTVariable,
        domain: "IntervalDomain",
        node: "Node",
        operation: Assignment,
    ) -> None:
        """Update array element when assigning to a reference variable that points to an array element."""
        if self.solver is None:
            return

        # Guard: only process ReferenceVariable lvalues
        if not isinstance(lvalue, (ReferenceVariable, ReferenceVariableSSA)):
            return

        # Find array element variables that might be constrained to equal this reference
        # Look for variables with pattern "array[index]" where the array matches points_to
        points_to = getattr(lvalue, "points_to", None)
        if points_to is None:
            return

        points_to_name = IntervalSMTUtils.resolve_variable_name(points_to)
        if points_to_name is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Use prefix index for fast lookup of array element variables
        # Look for "{points_to_name}[" prefix
        points_to_base = points_to_name.split("|")[0] if "|" in points_to_name else points_to_name

        # Get candidate variables using prefix index
        prefix = points_to_name + "["
        candidate_vars = domain.state.get_variables_by_prefix(prefix)

        # Also check with base name (without SSA version) if different
        if points_to_base != points_to_name:
            candidate_vars = candidate_vars.union(domain.state.get_variables_by_prefix(points_to_base + "["))

        for var_name in candidate_vars:
            tracked_var = domain.state.range_variables.get(var_name)
            if tracked_var is None:
                continue

            # Extract array base name (before the first "[")
            var_base = var_name.split("[", 1)[0]
            var_base_clean = var_base.split("|")[0] if "|" in var_base else var_base

            # Match base names, ignoring SSA versions (e.g., "Index.fixedArray" matches "Index.fixedArray|fixedArray_0")
            if not (
                var_base_clean == points_to_base
                or var_base.startswith(points_to_base)
                or points_to_base.startswith(var_base_clean)
            ):
                continue

            # Update array element to match the reference (constraint REF == array[index] exists from Index handler)
            element_width = self.solver.bv_size(tracked_var.term)
            ref_width = self.solver.bv_size(lvalue_var.term)

            if element_width != ref_width:
                continue

            # Explicitly constrain array element to equal the reference
            constraint: SMTTerm = tracked_var.term == lvalue_var.term
            self.solver.assert_constraint(constraint)
            self.logger.debug(
                "Updated array element '{element}' to match reference '{ref}'",
                element=var_name,
                ref=lvalue_name,
            )
            # Only update the first matching array element (should be unique per reference)
            break
