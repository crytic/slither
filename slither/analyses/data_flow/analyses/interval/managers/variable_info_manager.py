from typing import Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.core.types.interval_range import \
    IntervalRange
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable


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
        """Get type bounds for numeric types only."""
        if not self.is_type_numeric(var_type):
            logger.error(f"Type {var_type} is not numeric, cannot get bounds")
            raise ValueError(f"Type {var_type} is not numeric, cannot get bounds")

        return IntervalRange(var_type.min, var_type.max)

    def is_type_numeric(self, elementary_type: ElementaryType) -> bool:
        """Check if type is numeric."""
        if not elementary_type or not hasattr(elementary_type, "name"):
            logger.warning(f"Type {elementary_type} does not have name attribute")
            return False

        type_name = elementary_type.name
        is_numeric = (
            type_name.startswith("int")
            or type_name.startswith("uint")
            or type_name.startswith("fixed")
            or type_name.startswith("ufixed")
        )

        logger.debug(f"Type {type_name} is numeric: {is_numeric}")
        return is_numeric
