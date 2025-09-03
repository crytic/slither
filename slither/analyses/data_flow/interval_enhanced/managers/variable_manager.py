from decimal import Decimal
from typing import Optional, Set

from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from loguru import logger


class VariableManager:
    def __init__(self):
        """Initialize the variable manager"""
        self._tracked_variables: Set[str] = set()

    def get_variable_name(self, variable: Variable) -> str:
        """Get canonical variable name."""
        try:
            if variable is None:
                raise ValueError("Variable is None")
            if isinstance(variable, (StateVariable, LocalVariable)):
                variable_name: Optional[str] = variable.canonical_name
            else:
                variable_name: Optional[str] = getattr(variable, "name", None)
            if variable_name is None:
                raise ValueError(f"Variable name is None for variable: {variable}")
            return variable_name
        except Exception as e:
            logger.error(f"Error getting variable name for {variable}: {e}")
            raise

    def get_variable_type(self, variable) -> Optional[ElementaryType]:
        """Safely get variable type."""
        return getattr(variable, "type", None) if hasattr(variable, "type") else None

    def get_type_bounds(self, var_type: Optional[ElementaryType]) -> IntervalRange:
        try:
            if var_type is None:
                return IntervalRange(
                    lower_bound=0,
                    upper_bound=Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    ),
                )

            # Check if this is a custom/user-defined type (like a struct)
            if hasattr(var_type, "type") and hasattr(var_type.type, "type"):
                # This is likely a UserDefinedType (custom struct)
                logger.info(f"Custom type detected: {var_type}, using default range")
                return IntervalRange(
                    lower_bound=0,
                    upper_bound=Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    ),
                )

            # Check if the type is numeric and has min/max attributes
            try:
                is_numeric = self.is_type_numeric(var_type)
            except Exception as e:
                logger.warning(f"Error checking if type {var_type} is numeric: {e}")
                is_numeric = False

            if is_numeric and hasattr(var_type, "min") and hasattr(var_type, "max"):
                try:
                    return IntervalRange(lower_bound=var_type.min, upper_bound=var_type.max)
                except Exception as bounds_error:
                    logger.warning(
                        f"Error accessing min/max bounds for type {var_type}: {bounds_error}"
                    )
                    # Fall through to default range

            # For non-numeric types or types without min/max, use a default range
            # This handles custom types, structs, arrays, etc.
            logger.warning(f"Type {var_type} does not have min/max bounds, using default range")
            return IntervalRange(
                lower_bound=0,
                upper_bound=Decimal(
                    "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                ),
            )
        except Exception as e:

            logger.error(f"Error getting type bounds: {e}")
            logger.error(f"Variable type: {var_type}")
            logger.error(f"Variable type attributes: {dir(var_type) if var_type else 'None'}")
            raise

    def is_type_numeric(self, elementary_type) -> bool:
        """Check if type is numeric."""
        try:
            if not elementary_type:
                return False

            # Check if the type has a 'name' attribute before accessing it
            if not hasattr(elementary_type, "name"):
                return False

            # Additional safety check - make sure name is not None
            if elementary_type.name is None:
                return False

            type_name = elementary_type.name
            return (
                type_name.startswith("int")
                or type_name.startswith("uint")
                or type_name.startswith("fixed")
                or type_name.startswith("ufixed")
            )
        except Exception as e:
            logger.warning(f"Error in is_type_numeric for type {elementary_type}: {e}")
            return False
