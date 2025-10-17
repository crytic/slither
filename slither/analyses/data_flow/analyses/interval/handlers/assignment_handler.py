from decimal import Decimal

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable
from IPython import embed


class AssignmentHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:

        if operation.lvalue is None:
            logger.error("Assignment lvalue is None")
            raise ValueError("Assignment lvalue is None")

        written_variable: Variable = operation.lvalue
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)
        right_value = operation.rvalue

        #         # Skip assignments to non-numeric variables (address, bool, string, etc.)
        #         # Exception: Don't skip boolean assignments that come from integer comparisons
        #         should_skip = not (
        #             isinstance(written_variable_type, ElementaryType) and
        #             (self.variable_info_manager.is_type_numeric(written_variable_type) or
        #              self.variable_info_manager.is_type_bytes(written_variable_type))
        #         )

        #         # Check if this is a boolean assignment from a comparison operation
        #         if should_skip and isinstance(written_variable_type, ElementaryType) and written_variable_type.name == "bool":
        #             # Check if the rvalue is a temporary variable from a comparison
        #             if isinstance(right_value, TemporaryVariable):
        #                 # This is likely a boolean result from a comparison operation
        #                 # We should handle it to track the comparison result
        # #                logger.debug(f"Handling boolean assignment from comparison: {written_variable.name}")
        #                 should_skip = False

        #         if should_skip:
        # #            logger.debug(f"Skipping assignment to non-numeric variable: {written_variable.name} of type {written_variable_type}")
        #             return

        if isinstance(right_value, TemporaryVariable):
            self._handle_temporary_assignment(written_variable, right_value, domain)
        elif isinstance(right_value, Constant):
            self._handle_constant_assignment(written_variable, right_value, domain)
        elif isinstance(right_value, Variable):
            self._handle_variable_assignment(written_variable, right_value, domain, operation)

    def _handle_temporary_assignment(
        self,
        written_variable: Variable,
        source_variable: TemporaryVariable,
        domain: IntervalDomain,
    ) -> None:
        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)
        source_variable_name = self.variable_info_manager.get_variable_name(source_variable)

        # Handle bytes variables by creating offset and length variables
        if self.variable_info_manager.is_type_bytes(written_variable_type):
            range_variables = self.variable_info_manager.create_bytes_offset_and_length_variables(
                written_variable_name
            )
            # Add all created range variables to the domain state
            for var_name, range_variable in range_variables.items():
                domain.state.add_range_variable(var_name, range_variable)
            #            logger.debug(
            #     f"Created bytes variable {written_variable_name} with offset and length from temporary"
            # )
            return

        # Handle boolean variables specially
        if (
            isinstance(written_variable_type, ElementaryType)
            and written_variable_type.name == "bool"
        ):
            # For boolean assignments from comparisons, create a boolean range variable
            range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet({Decimal(0), Decimal(1)}),  # Boolean can be 0 or 1
                invalid_values=ValueSet(set()),
                var_type=written_variable_type,
            )
            domain.state.set_range_variable(written_variable_name, range_variable)
            #            logger.debug(f"Created boolean variable {written_variable_name} from temporary")
            return

        # copy the temporary variable to the target variable
        logger.debug(f"Looking for source variable: {source_variable_name}")
        logger.debug(
            f"Available variables in domain: {list(domain.state.get_range_variables().keys())}"
        )
        source_range_variable = domain.state.get_range_variable(source_variable_name)

        if source_range_variable is None:
            logger.error(f"Source variable {source_variable_name} does not exist in domain state")
            embed()
            raise ValueError(
                f"Source variable {source_variable_name} does not exist in domain state"
            )

        # Create range variable by copying from source
        range_variable = RangeVariable(
            interval_ranges=[ir.deep_copy() for ir in source_range_variable.get_interval_ranges()],
            valid_values=source_range_variable.get_valid_values().deep_copy(),
            invalid_values=source_range_variable.get_invalid_values().deep_copy(),
            var_type=written_variable_type,
        )

        # Store the relationship: local variable -> temporary variable
        domain.state.add_temp_var_mapping(written_variable_name, source_variable_name)

        domain.state.set_range_variable(written_variable_name, range_variable)

    def _handle_constant_assignment(
        self, written_variable: Variable, source_constant: Constant, domain: IntervalDomain
    ) -> None:
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)
        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)
        constant_val = source_constant.value

        # Handle bytes variables by creating offset and length variables
        if self.variable_info_manager.is_type_bytes(written_variable_type):
            range_variables = self.variable_info_manager.create_bytes_offset_and_length_variables(
                written_variable_name
            )
            # Add all created range variables to the domain state
            for var_name, range_variable in range_variables.items():
                domain.state.add_range_variable(var_name, range_variable)
            #            logger.debug(f"Created bytes variable {written_variable_name} with offset and length")
            return
        elif self.variable_info_manager.is_type_numeric(written_variable_type):
            # Convert constant to Decimal only for numeric targets
            if isinstance(constant_val, bool):
                value: Decimal = Decimal(1) if constant_val else Decimal(0)
            elif isinstance(constant_val, (bytes, bytearray)):
                # Treat as big-endian bytes to int
                value = Decimal(int.from_bytes(constant_val, byteorder="big"))
            elif isinstance(constant_val, str):
                s = constant_val
                if s.startswith("0x") or s.startswith("0X"):
                    value = Decimal(int(s, 16))
                else:
                    # If it looks like hex bytecode (only hex chars, even length), parse as hex
                    hs = s.strip()
                    if len(hs) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in hs):
                        try:
                            value = Decimal(int(hs, 16))
                        except Exception:
                            value = Decimal(0)
                    else:
                        value = Decimal(str(s))
            else:
                value = Decimal(str(constant_val))

            range_variable = RangeVariable(
                interval_ranges=None,
                valid_values=ValueSet([value]),
                invalid_values=None,
                var_type=written_variable_type,
            )
            domain.state.set_range_variable(written_variable_name, range_variable)
        else:
            logger.warning(
                f"Assignment to unsupported variable type: {written_variable_name} ({written_variable_type.name})"
            )

    def _handle_variable_assignment(
        self,
        written_variable: Variable,
        source_variable: Variable,
        domain: IntervalDomain,
        operation: Assignment,
    ) -> None:
        written_variable_name = self.variable_info_manager.get_variable_name(written_variable)
        written_variable_type = self.variable_info_manager.get_variable_type(written_variable)

        # Handle bytes variables by creating offset and length variables
        if self.variable_info_manager.is_type_bytes(written_variable_type):
            range_variables = self.variable_info_manager.create_bytes_offset_and_length_variables(
                written_variable_name
            )
            # Add all created range variables to the domain state
            for var_name, range_variable in range_variables.items():
                domain.state.add_range_variable(var_name, range_variable)
            #            logger.debug(
            #     f"Created bytes variable {written_variable_name} with offset and length from variable"
            # )
            return

        source_variable_name = self.variable_info_manager.get_variable_name(source_variable)
        if not domain.state.has_range_variable(source_variable_name):

            logger.error(f"Source variable {source_variable_name} does not exist in domain state")
            embed()
            raise ValueError(
                f"Source variable {source_variable_name} does not exist in domain state"
            )

        source_range_variable = domain.state.get_range_variable(source_variable_name)

        range_variable = RangeVariable(
            interval_ranges=[ir.deep_copy() for ir in source_range_variable.get_interval_ranges()],
            valid_values=source_range_variable.get_valid_values().deep_copy(),
            invalid_values=source_range_variable.get_invalid_values().deep_copy(),
            var_type=written_variable_type,
        )
        domain.state.set_range_variable(written_variable_name, range_variable)
