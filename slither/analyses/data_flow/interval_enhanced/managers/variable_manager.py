from decimal import Decimal
from typing import Optional, Set

from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable


class VariableManager:
    def __init__(self):
        """Initialize the variable manager"""
        self._tracked_variables: Set[str] = set()

    def get_variable_name(self, variable: Variable) -> str:
        """Get canonical variable name."""
        if isinstance(variable, (StateVariable, LocalVariable)):
            variable_name: Optional[str] = variable.canonical_name
        else:
            variable_name: Optional[str] = variable.name
        if variable_name is None:
            raise ValueError(f"Variable name is None for variable: {variable}")
        return variable_name

    def get_variable_type(self, variable) -> Optional[ElementaryType]:
        """Safely get variable type."""
        return getattr(variable, "type", None) if hasattr(variable, "type") else None

    def get_type_bounds(self, var_type: Optional[ElementaryType]) -> IntervalRange:
        if var_type is None:
            return IntervalRange(
                lower_bound=0,
                upper_bound=Decimal(
                    "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                ),
            )
        return IntervalRange(lower_bound=var_type.min, upper_bound=var_type.max)
