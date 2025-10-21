from typing import Optional

from loguru import logger

from slither.core.cfg.node import Node
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
    ReferenceHandler,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.slithir.operations.member import Member
from IPython import embed


class MemberHandler:
    """Handler for Member operations (e.g., struct.field, array.length, msg.sender)."""

    def __init__(self, reference_handler: ReferenceHandler) -> None:
        self._variable_info_manager = VariableInfoManager()
        self._reference_handler = reference_handler

    def handle_member(self, node: Node, domain: IntervalDomain, operation: Member) -> None:
        """Handle Member operations by creating appropriate range variables."""
        if not operation.lvalue:
            raise ValueError("Member operation has no lvalue")

        result_var_name = self._variable_info_manager.get_variable_name(operation.lvalue)
        result_type = operation.lvalue.type

        # Track reference mapping before creating variables
        self._reference_handler.track_member_reference(operation, result_var_name)

        # Create the appropriate range variable
        self._create_range_variable(domain, result_var_name, result_type, operation)

    def _create_range_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType, operation: Member
    ) -> None:
        """Create and add a range variable to the domain state."""
        # Check if variable already exists
        if domain.state.has_range_variable(var_name):
            #            logger.debug(f"Variable {var_name} already exists in state")
            return

        # Handle struct types - recursively create range variables for their fields
        if isinstance(var_type, UserDefinedType):
            self._variable_info_manager.create_struct_field_variables_for_domain(
                domain, var_name, var_type
            )
            # Also create a placeholder variable for the struct itself
            placeholder = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.add_range_variable(var_name, placeholder)
            return

        # Create the appropriate range variable based on type
        if self._variable_info_manager.is_type_numeric(var_type):
            self._create_numeric_variable(domain, var_name, var_type, operation)
        elif self._variable_info_manager.is_type_bytes(var_type):
            self._create_bytes_variable(domain, var_name, var_type)
        else:
            # For all other types (address, bool, string, etc.), create a placeholder
            placeholder = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.add_range_variable(var_name, placeholder)

    def _create_numeric_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType, operation: Member
    ) -> None:
        """Create a numeric range variable."""
        # Check if this reference should inherit constraints from its target
        target_var_name = self._reference_handler.get_target_for_reference(var_name)
        if target_var_name:
            if not domain.state.has_range_variable(target_var_name):
                logger.error(
                    f"Target variable {target_var_name} not found for reference {var_name}"
                )
                # embed()
                raise ValueError(
                    f"Target variable {target_var_name} not found for reference {var_name}"
                )

            # Inherit constraints from the target variable
            target_range_var = domain.state.get_range_variable(target_var_name)
            range_variable = target_range_var.deep_copy()
        #            logger.debug(f"Inherited constraints from {target_var_name} for {var_name}")
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

    #        logger.debug(f"Created numeric variable {var_name} with type {var_type}")

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


#        logger.debug(f"Created bytes variable {var_name} with type {var_type}")
