from decimal import Decimal
from typing import Optional, Union

from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.type_system import TypeSystem
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.variables.constant import Constant


class VariableManager:
    """
    Handles variable operations including name canonicalization, type identification,
    and interval creation for variables.
    """

    def __init__(self, type_system: TypeSystem):
        self.type_system = type_system

    def get_canonical_name(self, variable: Variable) -> str:
        """Get canonical variable name."""
        if isinstance(variable, (StateVariable, LocalVariable)):
            variable_name: Optional[str] = variable.canonical_name
        else:
            variable_name: Optional[str] = variable.name
        if variable_name is None:
            raise ValueError(f"Variable name is None for variable: {variable}")
        return variable_name

    def is_variable_not_constant(self, var: Union[Variable, Constant]) -> bool:
        """Check if variable is a Variable but not a Constant."""
        return isinstance(var, Variable) and not isinstance(var, Constant)

    def create_interval_for_variable(
        self, variable: Variable, domain_state_info: dict
    ) -> IntervalInfo:
        """Get existing interval or create new one with type bounds."""
        var_name: str = self.get_canonical_name(variable)

        if var_name in domain_state_info:
            return domain_state_info[var_name]

        var_type: Optional[ElementaryType] = getattr(variable, "type", None)
        interval: IntervalInfo = IntervalInfo(var_type=var_type)

        if isinstance(var_type, ElementaryType) and self.type_system.is_numeric_type(var_type):
            min_val: Decimal
            max_val: Decimal
            min_val, max_val = self.type_system.get_type_bounds(var_type)
            interval.lower_bound = min_val
            interval.upper_bound = max_val

        return interval

    def get_variable_type(self, variable) -> Optional[ElementaryType]:
        """Safely get variable type."""
        return getattr(variable, "type", None) if hasattr(variable, "type") else None

    def create_constant_interval(self, constant: Constant, target_var: Variable) -> IntervalInfo:
        """Create an interval from a constant value."""
        value: Decimal = Decimal(str(constant.value))
        target_type: Optional[ElementaryType] = self.get_variable_type(target_var)
        return IntervalInfo(upper_bound=value, lower_bound=value, var_type=target_type)

    def apply_type_bounds_to_interval(
        self, interval: IntervalInfo, target_type: ElementaryType
    ) -> None:
        """Apply type bounds to an interval if necessary."""
        if self.type_system.is_numeric_type(target_type):
            target_min: Decimal
            target_max: Decimal
            target_min, target_max = self.type_system.get_type_bounds(target_type)
            interval.lower_bound = max(interval.lower_bound, target_min)
            interval.upper_bound = min(interval.upper_bound, target_max)
