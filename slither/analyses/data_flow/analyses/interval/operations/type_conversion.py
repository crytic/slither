"""Type conversion operation handler for interval analysis."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.utils.integer_conversion import convert_string_to_int

# Import for global Solidity variables
try:
    from slither.core.declarations.solidity_variables import (
        SolidityVariable,
        SolidityVariableComposed,
    )
except ImportError:
    SolidityVariable = None
    SolidityVariableComposed = None

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


@dataclass
class ConversionContext:
    """Context for type conversion operation."""

    domain: "IntervalDomain"
    node: "Node"
    operation: TypeConversion


class TypeConversionHandler(BaseOperationHandler):
    """Handler for type conversion operations in interval analysis."""

    def handle(
        self,
        operation: Optional[TypeConversion],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle a type conversion operation."""
        if operation is None or self.solver is None:
            return

        self.logger.debug(f"Handling type conversion operation: {operation}")

        target_type = operation.type
        if not isinstance(target_type, ElementaryType):
            self.logger.debug(
                f"Type conversion to non-elementary type {target_type}; skipping interval update."
            )
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if lvalue_name is None:
            return

        ctx = ConversionContext(domain, node, operation)
        lvalue_var = self._get_or_create_lvalue(lvalue_name, target_type, ctx)
        if lvalue_var is None:
            return

        if isinstance(operation.variable, Constant):
            self._handle_constant_conversion(lvalue_var, operation.variable, target_type)
        else:
            self._handle_variable_conversion(operation.variable, lvalue_var, target_type, ctx)

        lvalue_var.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, lvalue_var)

    def _get_or_create_lvalue(
        self,
        lvalue_name: str,
        target_type: ElementaryType,
        ctx: ConversionContext,
    ) -> Optional[TrackedSMTVariable]:
        """Get or create lvalue variable for type conversion."""
        lvalue_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, lvalue_name)
        if lvalue_var is not None:
            return lvalue_var

        if IntervalSMTUtils.solidity_type_to_smt_sort(target_type) is None:
            self.logger.debug(
                "Elementary type '%s' not supported for interval analysis; skipping.",
                getattr(target_type, "type", target_type),
            )
            return None

        lvalue_var = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, target_type
        )
        if lvalue_var is None:
            self.logger.error_and_raise(
                "Failed to create tracked variable for "
                "type '{type_name}' and variable '{var_name}'",
                ValueError,
                var_name=lvalue_name,
                type_name=getattr(target_type, "type", target_type),
                embed_on_error=True,
                node=ctx.node,
                operation=ctx.operation,
                domain=ctx.domain,
            )
            return None

        ctx.domain.state.set_range_variable(lvalue_name, lvalue_var)
        return lvalue_var

    def _handle_variable_conversion(
        self,
        variable: object,
        lvalue_var: TrackedSMTVariable,
        target_type: ElementaryType,
        ctx: ConversionContext,
    ) -> None:
        """Handle type conversion from a variable."""
        variable_name = IntervalSMTUtils.resolve_variable_name(variable)
        if variable_name is None:
            return

        source_type = self._resolve_source_type(variable, target_type)
        if source_type is None:
            self.logger.debug(
                "Unsupported source type for type conversion; skipping interval update."
            )
            return

        source_var = self._get_or_create_source_variable(variable, variable_name, source_type, ctx)
        if source_var is None:
            return

        self._apply_type_conversion_constraint(
            lvalue_var, source_var, source_type, target_type
        )

    def _resolve_source_type(
        self, variable: object, target_type: ElementaryType
    ) -> Optional[ElementaryType]:
        """Resolve source type for variable conversion."""
        source_type = IntervalSMTUtils.resolve_elementary_type(getattr(variable, "type", None))
        if source_type is not None:
            return source_type

        is_solidity_var = (
            SolidityVariable is not None
            and SolidityVariableComposed is not None
            and isinstance(variable, (SolidityVariable, SolidityVariableComposed))
        )
        if is_solidity_var:
            return target_type

        return None

    def _get_or_create_source_variable(
        self,
        variable: object,
        variable_name: str,
        source_type: ElementaryType,
        ctx: ConversionContext,
    ) -> Optional[TrackedSMTVariable]:
        """Get or create source variable for type conversion."""
        source_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, variable_name)
        if source_var is not None:
            return source_var

        is_solidity_var = (
            SolidityVariable is not None
            and SolidityVariableComposed is not None
            and isinstance(variable, (SolidityVariable, SolidityVariableComposed))
        )

        if is_solidity_var and IntervalSMTUtils.solidity_type_to_smt_sort(source_type) is not None:
            source_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, variable_name, source_type
            )
            if source_var is not None:
                ctx.domain.state.set_range_variable(variable_name, source_var)
                return source_var

        self.logger.error_and_raise(
            "Variable '{var_name}' not found in domain for type conversion source",
            ValueError,
            var_name=variable_name,
            embed_on_error=True,
            node=ctx.node,
            operation=ctx.operation,
            domain=ctx.domain,
        )
        return None

    def _apply_type_conversion_constraint(
        self,
        lvalue_var: TrackedSMTVariable,
        source_var: TrackedSMTVariable,
        source_type: ElementaryType,
        target_type: ElementaryType,
    ) -> None:
        """Apply type conversion constraint (extend or truncate as needed)."""
        source_width = self.solver.bv_size(source_var.term)
        target_width = self.solver.bv_size(lvalue_var.term)

        if source_width == target_width:
            constraint: SMTTerm = lvalue_var.term == source_var.term
        elif source_width < target_width:
            is_signed = IntervalSMTUtils.is_signed_type(source_type)
            extended_term = IntervalSMTUtils.extend_to_width(
                self.solver, source_var.term, target_width, is_signed
            )
            constraint: SMTTerm = lvalue_var.term == extended_term
        else:
            truncated_term = IntervalSMTUtils.truncate_to_width(
                self.solver, source_var.term, target_width
            )
            constraint: SMTTerm = lvalue_var.term == truncated_term

        self.solver.assert_constraint(constraint)

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
        original_string_value = None

        # Convert hex string constants (e.g., bytes32) to integers
        if isinstance(const_value, str):
            original_string_value = const_value
            # Store byte length metadata for bytes/string conversions (for Length handler)
            byte_length = self._compute_byte_length(const_value)
            if byte_length is not None:
                lvalue_var.base.metadata["bytes_length"] = byte_length

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
                    # Still stored bytes_length, so Length handler can use it
                    return

        if not isinstance(const_value, int):
            return

        # Create constant term using solver's create_constant method with target type width
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
        # Handle regular string literals (length in bytes = length in chars for ASCII)
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
