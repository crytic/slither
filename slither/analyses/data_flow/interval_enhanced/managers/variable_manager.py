from typing import Dict, Optional, Set, Union


from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
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
