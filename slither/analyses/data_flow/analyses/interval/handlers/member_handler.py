from typing import Optional

from loguru import logger

from slither.core.cfg.node import Node
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.slithir.operations.member import Member


class MemberHandler:
    """Handler for Member operations (e.g., struct.field, array.length, msg.sender)."""

    def __init__(self) -> None:
        self._variable_info_manager = VariableInfoManager()
        # Track reference-to-target mappings for constraint propagation
        self._reference_mappings: dict[str, str] = {}

    def handle_member(self, node: Node, domain: IntervalDomain, operation: Member) -> None:
        """Handle Member operations by creating appropriate range variables."""
        if not operation.lvalue:
            raise ValueError("Member operation has no lvalue")

        result_var_name = self._variable_info_manager.get_variable_name(operation.lvalue)
        result_type = operation.lvalue.type

        # Track reference mapping before creating variables
        self._track_reference_mapping(operation, result_var_name)

        # Create the appropriate range variable
        self._create_range_variable(domain, result_var_name, result_type, operation)

    def _create_range_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType, operation: Member
    ) -> None:
        """Create and add a range variable to the domain state."""
        # Check if variable already exists
        if domain.state.has_range_variable(var_name):
            logger.debug(f"Variable {var_name} already exists in state")
            return

        # Handle struct types - recursively create range variables for their fields
        if isinstance(var_type, UserDefinedType):
            self._variable_info_manager.create_struct_field_variables_for_domain(
                domain, var_name, var_type
            )
            return

        # Only add numeric and bytes types to state
        if not self._should_add_to_state(var_type):
            raise ValueError(f"Cannot create range variable for unsupported type: {var_type}")

        # Create the appropriate range variable
        if self._variable_info_manager.is_type_numeric(var_type):
            self._create_numeric_variable(domain, var_name, var_type)
        elif self._variable_info_manager.is_type_bytes(var_type):
            self._create_bytes_variable(domain, var_name, var_type)
        else:
            raise ValueError(f"Unsupported variable type for range analysis: {var_type}")

    def _create_numeric_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType
    ) -> None:
        """Create a numeric range variable."""
        # Check if this reference should inherit constraints from its target
        target_var_name = self.get_target_for_reference(var_name)
        if target_var_name:
            if not domain.state.has_range_variable(target_var_name):
                raise ValueError(
                    f"Target variable {target_var_name} not found for reference {var_name}"
                )
            # Inherit constraints from the target variable
            target_range_var = domain.state.get_range_variable(target_var_name)
            range_variable = target_range_var.deep_copy()
            logger.debug(f"Inherited constraints from {target_var_name} for {var_name}")
        else:
            # Create new range variable with type bounds
            interval_range = IntervalRange(
                lower_bound=var_type.min,
                upper_bound=var_type.max,
            )
            range_variable = RangeVariable(
                interval_ranges=[interval_range],
                valid_values=None,
                invalid_values=None,
                var_type=var_type,
            )

        domain.state.add_range_variable(var_name, range_variable)
        logger.debug(f"Created numeric variable {var_name} with type {var_type}")

    def _create_bytes_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType
    ) -> None:
        """Create bytes range variables (offset and length)."""
        range_variables = self._variable_info_manager.create_bytes_offset_and_length_variables(
            var_name
        )
        # Add all created range variables to the domain state
        for var_name_bytes, range_variable in range_variables.items():
            domain.state.add_range_variable(var_name_bytes, range_variable)
        logger.debug(f"Created bytes variable {var_name} with type {var_type}")

    def _track_reference_mapping(self, operation: Member, result_var_name: str) -> None:
        """Track reference-to-target mapping for constraint propagation."""
        if not operation.variable_left or not operation.variable_right:
            raise ValueError("Member operation missing left or right variable")

        # Get the target field variable name
        base_var_name = self._variable_info_manager.get_variable_name(operation.variable_left)
        field_name = (
            operation.variable_right.value
            if hasattr(operation.variable_right, "value")
            else str(operation.variable_right)
        )
        target_field_name = f"{base_var_name}.{field_name}"

        # Store the mapping: reference -> target
        self._reference_mappings[result_var_name] = target_field_name
        logger.debug(f"Tracked reference mapping: {result_var_name} -> {target_field_name}")

    def _should_add_to_state(self, var_type: ElementaryType) -> bool:
        """Check if a variable type should be added to the interval analysis state."""
        if not var_type:
            return False

        if isinstance(var_type, UserDefinedType):
            return False

        return self._variable_info_manager.is_type_numeric(
            var_type
        ) or self._variable_info_manager.is_type_bytes(var_type)

    def get_target_for_reference(self, ref_var_name: str) -> Optional[str]:
        """Get the target variable name for a reference variable."""
        return self._reference_mappings.get(ref_var_name)
