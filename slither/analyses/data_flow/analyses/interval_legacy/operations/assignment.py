"""Assignment operation handler for interval analysis."""

from dataclasses import dataclass
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


@dataclass
class AssignmentContext:
    """Context for assignment operation handling."""

    operation: Assignment
    domain: "IntervalDomain"
    node: "Node"
    is_checked: bool


@dataclass
class RvalueInfo:
    """Info about the rvalue in an assignment."""

    value: object
    name: str


class AssignmentHandler(BaseOperationHandler):
    """Handler for assignment operations in interval analysis."""

    def handle(
        self,
        operation: Optional[Assignment],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle an assignment operation."""
        if operation is None or self.solver is None:
            return

        self.logger.debug(f"Handling assignment operation: {operation}")

        lvalue_info = self._resolve_lvalue_info(operation)
        if lvalue_info is None:
            return
        lvalue_name, lvalue_type = lvalue_info

        ctx = AssignmentContext(operation, domain, node, self._get_is_checked(node))
        lvalue_var = self._ensure_lvalue_tracked(lvalue_name, lvalue_type, ctx)
        if lvalue_var is None:
            return

        if not self._process_rvalue(lvalue_var, lvalue_name, lvalue_type, ctx):
            return

        domain.state.set_range_variable(lvalue_name, lvalue_var)
        self._update_references_if_needed(operation.lvalue, lvalue_var, ctx)

    def _resolve_lvalue_info(
        self, operation: Assignment
    ) -> Optional[tuple[str, ElementaryType]]:
        """Resolve lvalue name and type."""
        lvalue = operation.lvalue
        lvalue_name = self._get_variable_name(lvalue)
        if lvalue_name is None:
            return None

        lvalue_type_attr = lvalue.type if hasattr(lvalue, "type") else None
        lvalue_type = IntervalSMTUtils.resolve_elementary_type(
            operation.variable_return_type, lvalue_type_attr
        )
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for assignment; skipping.")
            return None

        return lvalue_name, lvalue_type

    def _get_is_checked(self, node: "Node") -> bool:
        """Get is_checked status from node scope."""
        if isinstance(node.scope, Scope):
            return node.scope.is_checked
        if isinstance(node.scope, Function):
            return node.scope.is_checked()
        return False

    def _ensure_lvalue_tracked(
        self,
        lvalue_name: str,
        lvalue_type: ElementaryType,
        ctx: AssignmentContext,
    ) -> Optional[TrackedSMTVariable]:
        """Ensure lvalue is tracked, creating if needed."""
        lvalue_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, lvalue_name)
        if lvalue_var is not None:
            return lvalue_var

        if IntervalSMTUtils.solidity_type_to_smt_sort(lvalue_type) is None:
            self.logger.debug(
                "Elementary type '%s' not supported; skipping.",
                getattr(lvalue_type, "type", lvalue_type),
            )
            return None

        lvalue_var = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, lvalue_type
        )
        if lvalue_var is None:
            self.logger.error_and_raise(
                "Failed to create tracked variable for '{var_name}'",
                ValueError,
                var_name=lvalue_name,
                embed_on_error=True,
                node=ctx.node, operation=ctx.operation, domain=ctx.domain,
            )
        ctx.domain.state.set_range_variable(lvalue_name, lvalue_var)
        return lvalue_var

    def _process_rvalue(
        self,
        lvalue_var: TrackedSMTVariable,
        lvalue_name: str,
        lvalue_type: ElementaryType,
        ctx: AssignmentContext,
    ) -> bool:
        """Process the rvalue of the assignment. Returns True if successful."""
        rvalue = ctx.operation.rvalue
        if isinstance(rvalue, Constant):
            self._handle_constant_assignment(lvalue_var, rvalue, lvalue_type, lvalue_name, ctx)
            return True

        rvalue_name = self._get_variable_name(rvalue)
        if rvalue_name is None:
            return True

        rvalue_info = RvalueInfo(rvalue, rvalue_name)
        return self._handle_variable_assignment(
            lvalue_var, rvalue_info, lvalue_name, lvalue_type, ctx
        )

    def _update_references_if_needed(
        self,
        lvalue: object,
        lvalue_var: TrackedSMTVariable,
        ctx: AssignmentContext,
    ) -> None:
        """Update struct/array references if lvalue points to them."""
        if not hasattr(lvalue, "points_to") or lvalue.points_to is None:
            return
        self._update_struct_member_if_reference(lvalue, lvalue_var, ctx)
        self._update_array_element_if_reference(lvalue, lvalue_var, ctx)

    def _get_variable_name(self, var: Union[object, Constant]) -> Optional[str]:
        """Extract variable name from SlitherIR variable."""
        return IntervalSMTUtils.resolve_variable_name(var)

    def _handle_variable_assignment(
        self,
        lvalue_var: TrackedSMTVariable,
        rvalue_info: RvalueInfo,
        lvalue_name: str,
        fallback_type: Optional[ElementaryType],
        ctx: AssignmentContext,
    ) -> bool:
        """Process assignment from another variable; return False if unsupported."""
        rvalue_var = self._resolve_rvalue_variable(
            rvalue_info.value, rvalue_info.name, fallback_type, ctx
        )
        if rvalue_var is None:
            return False

        self._apply_assignment_constraint(lvalue_var, rvalue_var)
        self._propagate_assignment_metadata(
            lvalue_var, rvalue_var, lvalue_name, rvalue_info.name, ctx.domain
        )
        self._handle_assignment_overflow(
            lvalue_var, rvalue_var, rvalue_info.name, ctx.is_checked
        )
        return True

    def _resolve_rvalue_variable(
        self,
        rvalue: object,
        rvalue_name: str,
        fallback_type: Optional[ElementaryType],
        ctx: AssignmentContext,
    ) -> Optional[TrackedSMTVariable]:
        """Resolve the rvalue to a tracked variable, creating if needed."""
        rvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(rvalue, "type", None))
        if rvalue_type is None:
            rvalue_type = fallback_type
            if rvalue_type is None:
                self.logger.debug("Unsupported rvalue type; skipping.")
                return None

        rvalue_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, rvalue_name)
        if rvalue_var is not None:
            return rvalue_var

        # Try to materialize struct fields
        rvalue_actual_type = getattr(rvalue, "type", None)
        if isinstance(rvalue_actual_type, UserDefinedType) and isinstance(
            rvalue_actual_type.type, Structure
        ):
            self._materialize_struct_fields(ctx.domain, rvalue_name, rvalue_actual_type.type)
            return None

        # Synthesize a tracked variable
        return self._synthesize_rvalue_variable(rvalue_name, rvalue_actual_type, rvalue_type, ctx)

    def _synthesize_rvalue_variable(
        self,
        rvalue_name: str,
        rvalue_actual_type: object,
        rvalue_type: ElementaryType,
        ctx: AssignmentContext,
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
                node=ctx.node, operation=ctx.operation, domain=ctx.domain,
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
                node=ctx.node, operation=ctx.operation, domain=ctx.domain,
            )
        ctx.domain.state.set_range_variable(rvalue_name, rvalue_var)
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
        var_type: ElementaryType,
        lvalue_name: str,
        ctx: AssignmentContext,
    ) -> None:
        """Handle assignment from a constant value."""
        if self.solver is None:
            return

        const_value, original_string = self._convert_constant_value(constant)
        if const_value is None:
            return

        if original_string is not None:
            self._store_byte_length_metadata(lvalue_var, original_string)

        const_term: SMTTerm = self.solver.create_constant(const_value, lvalue_var.sort)
        self.solver.assert_constraint(lvalue_var.term == const_term)
        lvalue_var.assert_no_overflow(self.solver)

        if original_string is not None:
            self._store_bytes_memory_constant(
                original_string, var_type, lvalue_name, ctx.domain
            )

    def _convert_constant_value(self, constant: Constant) -> tuple[Optional[int], Optional[str]]:
        """Convert constant to integer value and return original string if applicable."""
        const_value = constant.value
        original_string = None

        if isinstance(const_value, str):
            original_string = const_value
            try:
                const_value = convert_string_to_int(const_value)
            except (ValueError, TypeError):
                ascii_value = self._string_to_int(original_string)
                if ascii_value is not None:
                    const_value = ascii_value
                else:
                    self.logger.debug(
                        "Unable to convert constant string '%s' to integer; skipping.",
                        const_value,
                    )
                    return None, None

        if not isinstance(const_value, int):
            return None, None

        return const_value, original_string

    def _store_byte_length_metadata(
        self, lvalue_var: TrackedSMTVariable, original_string: str
    ) -> None:
        """Store byte length metadata for bytes/string constants."""
        byte_length = self._compute_byte_length(original_string)
        if byte_length is not None:
            lvalue_var.base.metadata["bytes_length"] = byte_length

    def _store_bytes_memory_constant(
        self,
        original_string: str,
        var_type: ElementaryType,
        lvalue_name: str,
        domain: "IntervalDomain",
    ) -> None:
        """Store bytes memory constant if this is a dynamic bytes type."""
        type_str = getattr(var_type, "type", None)
        if type_str != "bytes":
            return

        if not (original_string.startswith("0x") or original_string.startswith("0X")):
            return

        try:
            hex_part = original_string[2:].replace(" ", "").replace("\n", "")
            byte_content = bytes.fromhex(hex_part)
            domain.state.set_bytes_memory_constant(lvalue_name, byte_content)
            self.logger.debug(
                "Stored bytes memory constant for '{name}': {length} bytes",
                name=lvalue_name,
                length=len(byte_content),
            )
        except (ValueError, TypeError) as e:
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
        """Check if variable is a Solidity global (full range, not initialized to 0)."""
        return isinstance(var, (SolidityVariableComposed, SolidityVariable))

    def _initialize_variable_to_zero(self, var: TrackedSMTVariable) -> None:
        """Initialize a variable to 0 (Solidity default for uninitialized vars)."""
        if self.solver is None:
            return
        zero_constant = self.solver.create_constant(0, var.sort)
        self.solver.assert_constraint(var.term == zero_constant)

    def _update_struct_member_if_reference(
        self,
        lvalue: object,
        lvalue_var: TrackedSMTVariable,
        ctx: AssignmentContext,
    ) -> None:
        """Update struct member when assigning to a reference pointing to struct member."""
        ref_info = self._get_reference_info(lvalue)
        if ref_info is None:
            return
        lvalue_name, points_to_name = ref_info

        candidates = self._get_struct_member_candidates(points_to_name, ctx.domain)
        self._update_matching_variable(
            candidates, lvalue_var, lvalue_name, points_to_name, ctx.domain
        )

    def _update_array_element_if_reference(
        self,
        lvalue: object,
        lvalue_var: TrackedSMTVariable,
        ctx: AssignmentContext,
    ) -> None:
        """Update array element when assigning to a reference pointing to array element."""
        ref_info = self._get_reference_info(lvalue)
        if ref_info is None:
            return
        lvalue_name, points_to_name = ref_info

        candidates = self._get_array_element_candidates(points_to_name, ctx.domain)
        self._update_matching_variable(
            candidates, lvalue_var, lvalue_name, points_to_name, ctx.domain
        )

    def _get_reference_info(self, lvalue: object) -> Optional[tuple[str, str]]:
        """Get lvalue name and points_to name for a reference variable."""
        if self.solver is None:
            return None
        if not isinstance(lvalue, (ReferenceVariable, ReferenceVariableSSA)):
            return None

        points_to = getattr(lvalue, "points_to", None)
        if points_to is None:
            return None

        points_to_name = IntervalSMTUtils.resolve_variable_name(points_to)
        if points_to_name is None:
            return None

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        return lvalue_name, points_to_name

    def _get_struct_member_candidates(
        self, points_to_name: str, domain: "IntervalDomain"
    ) -> set[str]:
        """Get candidate struct member variables."""
        candidates = domain.state.get_variables_by_prefix(points_to_name + ".")
        points_to_base = points_to_name.split("|")[0] if "|" in points_to_name else None
        if points_to_base and points_to_base != points_to_name:
            candidates = candidates.union(
                domain.state.get_variables_by_prefix(points_to_base + ".")
            )
        return candidates

    def _get_array_element_candidates(
        self, points_to_name: str, domain: "IntervalDomain"
    ) -> set[str]:
        """Get candidate array element variables."""
        candidates = domain.state.get_variables_by_prefix(points_to_name + "[")
        points_to_base = points_to_name.split("|")[0] if "|" in points_to_name else points_to_name
        if points_to_base != points_to_name:
            candidates = candidates.union(
                domain.state.get_variables_by_prefix(points_to_base + "[")
            )
        return candidates

    def _update_matching_variable(
        self,
        candidates: set[str],
        lvalue_var: TrackedSMTVariable,
        lvalue_name: str,
        points_to_name: str,
        domain: "IntervalDomain",
    ) -> None:
        """Update the first matching variable to equal the reference."""
        points_to_base = points_to_name.split("|")[0] if "|" in points_to_name else points_to_name
        ref_width = self.solver.bv_size(lvalue_var.term)

        for var_name in candidates:
            tracked_var = domain.state.range_variables.get(var_name)
            if tracked_var is None:
                continue

            if not self._is_matching_base(var_name, points_to_name, points_to_base):
                continue

            var_width = self.solver.bv_size(tracked_var.term)
            if var_width != ref_width:
                continue

            self.solver.assert_constraint(tracked_var.term == lvalue_var.term)
            self.logger.debug(
                "Updated variable '{var}' to match reference '{ref}'",
                var=var_name,
                ref=lvalue_name,
            )
            break

    def _is_matching_base(
        self, var_name: str, points_to_name: str, points_to_base: str
    ) -> bool:
        """Check if variable base matches the points_to base."""
        # Determine separator based on variable name pattern
        separator = "." if "." in var_name and "[" not in var_name.split(".", 1)[0] else "["
        var_base = var_name.split(separator, 1)[0]
        var_base_clean = var_base.split("|")[0] if "|" in var_base else var_base

        if separator == ".":
            return var_base.startswith(points_to_name) or points_to_name.startswith(var_base_clean)

        return (
            var_base_clean == points_to_base
            or var_base.startswith(points_to_base)
            or points_to_base.startswith(var_base_clean)
        )
