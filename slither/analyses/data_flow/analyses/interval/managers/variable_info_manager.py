from typing import Union, TYPE_CHECKING

from loguru import logger

from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.core.solidity_types.elementary_type import (
    ElementaryType,
    Int,
    Uint,
    Byte,
    Fixed,
    Ufixed,
)
from slither.core.variables import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable


class VariableInfoManager:
    def __init__(self):
        """Initialize the variable manager"""

    def get_variable_name(self, variable: Variable | None) -> str:
        """Get canonical variable name."""
        if variable is None:
            logger.error("Variable is None")
            raise ValueError("Variable is None")

        if isinstance(variable, Union[StateVariable, LocalVariable]):
            return variable.canonical_name

        variable_name = getattr(variable, "name", None)
        if variable_name is None:
            logger.error(f"Variable name is None for variable: {variable}")
            raise ValueError(f"Variable name is None for variable: {variable}")

        return variable_name

    def get_variable_type(self, variable: Variable) -> ElementaryType:
        """Safely get variable type."""
        return variable.type

    def get_type_bounds(self, var_type: ElementaryType) -> IntervalRange:
        """Get type bounds using ElementaryType min/max properties."""
        if not self.is_type_numeric(var_type):
            logger.error(f"Type {var_type} is not numeric, cannot get bounds")
            raise ValueError(f"Type {var_type} is not numeric, cannot get bounds")

        try:
            # Use the min/max properties from ElementaryType
            return IntervalRange(var_type.min, var_type.max)
        except Exception as e:
            logger.error(f"Error getting bounds for type {var_type}: {e}")
            raise ValueError(f"Could not get bounds for type {var_type}: {e}")

    def is_type_numeric(self, elementary_type: ElementaryType) -> bool:
        """Check if type is numeric using ElementaryType properties."""
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        try:
            type_name = elementary_type.name
            # Use the predefined lists from ElementaryType
            is_numeric = (
                type_name in Int or type_name in Uint or type_name in Fixed or type_name in Ufixed
            )

            logger.debug(f"Type {type_name} is numeric: {is_numeric}")
            return is_numeric
        except Exception as e:
            logger.warning(f"Error checking if type {elementary_type} is numeric: {e}")
            return False

    def is_type_bytes(self, elementary_type: ElementaryType) -> bool:
        """Check if type is bytes using ElementaryType properties."""
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        try:
            type_name = elementary_type.name
            # Use the predefined Byte list from ElementaryType
            is_bytes = type_name in Byte

            logger.debug(f"Type {type_name} is bytes: {is_bytes}")
            return is_bytes
        except Exception as e:
            logger.warning(f"Error checking if type {elementary_type} is bytes: {e}")
            return False

    def is_type_dynamic(self, elementary_type: ElementaryType) -> bool:
        """Check if type is dynamic using ElementaryType properties."""
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        try:
            # Use the is_dynamic property from ElementaryType
            is_dynamic = elementary_type.is_dynamic
            logger.debug(f"Type {elementary_type.name} is dynamic: {is_dynamic}")
            return is_dynamic
        except Exception as e:
            logger.warning(f"Error checking if type {elementary_type} is dynamic: {e}")
            return False

    def create_bytes_offset_and_length_variables(self, var_name: str) -> dict[str, "RangeVariable"]:
        """Create offset and length variables for bytes variables.

        Returns:
            Dictionary mapping variable names to their corresponding RangeVariable objects.
        """
        from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
            RangeVariable,
        )
        from slither.core.solidity_types.elementary_type import ElementaryType

        range_variables = {}

        # Create a base variable for the bytes parameter itself
        # This represents the bytes parameter as a whole
        base_type = ElementaryType("uint256")  # Treat bytes as uint256 for now
        base_interval_range = IntervalRange(
            lower_bound=base_type.min,
            upper_bound=base_type.max,
        )
        base_range_variable = RangeVariable(
            interval_ranges=[base_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=base_type,
        )
        range_variables[var_name] = base_range_variable

        # Create offset variable (uint256 type)
        offset_var_name = f"{var_name}.offset"
        offset_type = ElementaryType("uint256")
        offset_interval_range = IntervalRange(
            lower_bound=offset_type.min,
            upper_bound=offset_type.max,
        )
        offset_range_variable = RangeVariable(
            interval_ranges=[offset_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=offset_type,
        )
        range_variables[offset_var_name] = offset_range_variable

        # Create length variable (uint256 type)
        length_var_name = f"{var_name}.length"
        length_type = ElementaryType("uint256")
        length_interval_range = IntervalRange(
            lower_bound=length_type.min,
            upper_bound=length_type.max,
        )
        length_range_variable = RangeVariable(
            interval_ranges=[length_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=length_type,
        )
        range_variables[length_var_name] = length_range_variable

        return range_variables
