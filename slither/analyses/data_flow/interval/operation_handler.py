from decimal import Decimal
from typing import List, Optional, Union
from loguru import logger

from slither.analyses.data_flow.interval.domain import IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.interval_calculator import IntervalCalculator
from slither.analyses.data_flow.interval.type_system import TypeSystem
from slither.analyses.data_flow.interval.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.return_operation import Return
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class OperationHandler:
    """
    Handles operation processing including arithmetic operations, assignments,
    and return statement processing.
    """

    def __init__(
        self,
        type_system: TypeSystem,
        variable_manager: VariableManager,
        constraint_manager,
    ):
        self.type_system = type_system
        self.variable_manager = variable_manager
        self.constraint_manager = constraint_manager

    def handle_arithmetic_operation(
        self, domain: IntervalDomain, operation: Binary, node: Node
    ) -> None:
        """Handle arithmetic operations and compute result intervals."""
        # Check for division by zero BEFORE processing the operation
        if operation.type == BinaryType.DIVISION:
            self._check_division_by_zero(operation, domain, node)

        left_interval_info: IntervalInfo = self._retrieve_interval_info(
            operation.variable_left, domain, operation
        )
        right_interval_info: IntervalInfo = self._retrieve_interval_info(
            operation.variable_right, domain, operation
        )

        lower_bound: Decimal
        upper_bound: Decimal
        lower_bound, upper_bound = IntervalCalculator.calculate_arithmetic_bounds(
            left_interval_info.lower_bound,
            left_interval_info.upper_bound,
            right_interval_info.lower_bound,
            right_interval_info.upper_bound,
            operation.type,
        )

        if not isinstance(operation.lvalue, Variable):
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

        variable_name: str = self.variable_manager.get_canonical_name(operation.lvalue)
        target_type: Optional[ElementaryType] = self.type_system.determine_operation_result_type(
            operation
        )

        new_interval: IntervalInfo = IntervalInfo(
            upper_bound=upper_bound, lower_bound=lower_bound, var_type=target_type
        )
        domain.state.info[variable_name] = new_interval

        # Track the mapping between temporary variable and source arithmetic expression
        if isinstance(operation.lvalue, TemporaryVariable):
            self.constraint_manager.add_temp_var_mapping(variable_name, operation)

    def _check_division_by_zero(
        self, operation: Binary, domain: IntervalDomain, node: Node
    ) -> None:
        """Check if division by zero is possible in the division operation."""
        if operation.type != BinaryType.DIVISION:
            return

        # Get the right operand (divisor)
        right_operand = operation.variable_right

        # Get interval info for the divisor
        divisor_interval = self._retrieve_interval_info(right_operand, domain, operation)

        # Check if zero is within the divisor's range
        if divisor_interval.lower_bound <= Decimal("0") <= divisor_interval.upper_bound:
            # Get variable names for better error reporting
            left_var_name = self._get_variable_name_for_logging(operation.variable_left)
            right_var_name = self._get_variable_name_for_logging(operation.variable_right)

            logger.error(
                f"🚨 DIVISION BY ZERO DETECTED: "
                f"Division operation {left_var_name} / {right_var_name} "
                f"at node '{node.expression}' in function '{node.function.name}'. "
                f"Divisor range: {divisor_interval} contains zero."
            )

    def _get_variable_name_for_logging(
        self, var: Union[Variable, Constant, RVALUE, Function]
    ) -> str:
        """Get a readable name for a variable for logging purposes."""
        if isinstance(var, Constant):
            return str(var.value)
        elif isinstance(var, Variable):
            return self.variable_manager.get_canonical_name(var)
        else:
            return str(var)

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        """Handle assignment operations."""
        if operation.lvalue is None:
            return

        written_variable: Variable = operation.lvalue
        right_value = operation.rvalue
        writing_variable_name: str = self.variable_manager.get_canonical_name(written_variable)

        # Check if the assignment is a comparison or logical operation
        if isinstance(right_value, Binary) and (
            right_value.type in self.constraint_manager.COMPARISON_OPERATORS
            or right_value.type in self.constraint_manager.LOGICAL_OPERATORS
        ):
            # Store as pending constraint
            self.constraint_manager.add_pending_constraint(writing_variable_name, right_value)
        elif isinstance(right_value, TemporaryVariable):
            # Check if the temporary variable has a pending constraint
            temp_var_name: str = self.variable_manager.get_canonical_name(right_value)
            if self.constraint_manager.has_pending_constraint(temp_var_name):
                # Copy the constraint from the temporary variable to the local variable
                constraint = self.constraint_manager.get_pending_constraint(temp_var_name)
                if constraint is not None:
                    self.constraint_manager.add_pending_constraint(
                        writing_variable_name, constraint
                    )
                # Remove the constraint from the temporary variable
                self.constraint_manager.remove_pending_constraint(temp_var_name)

        if isinstance(right_value, Constant):
            self._handle_constant_assignment(
                writing_variable_name, right_value, written_variable, domain
            )
        elif isinstance(right_value, (TemporaryVariable, Variable)):
            self._handle_variable_assignment(
                writing_variable_name, right_value, written_variable, domain
            )

    def _handle_constant_assignment(
        self, var_name: str, constant: Constant, target_var: Variable, domain: IntervalDomain
    ) -> None:
        """Handle assignment of constant value."""
        value: Decimal = Decimal(str(constant.value))
        target_type: Optional[ElementaryType] = self.variable_manager.get_variable_type(target_var)
        domain.state.info[var_name] = IntervalInfo(
            upper_bound=value, lower_bound=value, var_type=target_type
        )

    def _handle_variable_assignment(
        self,
        var_name: str,
        source_var: Union[TemporaryVariable, Variable],
        target_var: Variable,
        domain: IntervalDomain,
    ) -> None:
        """Handle assignment from another variable."""
        source_name: str = self.variable_manager.get_canonical_name(source_var)
        if source_name in domain.state.info:
            source_interval: IntervalInfo = domain.state.info[source_name]
            target_type: Optional[ElementaryType] = self.variable_manager.get_variable_type(
                target_var
            )

            new_interval: IntervalInfo = source_interval.deep_copy()
            new_interval.var_type = target_type

            # Apply type bounds if necessary
            if isinstance(target_type, ElementaryType) and self.type_system.is_numeric_type(
                target_type
            ):
                self.variable_manager.apply_type_bounds_to_interval(new_interval, target_type)

            domain.state.info[var_name] = new_interval

    def handle_return_operation(
        self, node: Node, domain: IntervalDomain, operation: Return
    ) -> None:
        """Handle return operations by capturing return value constraints."""
        if not operation.values:
            return

        # Handle single return value
        if len(operation.values) == 1:
            self._handle_single_return_value(node, domain, operation.values[0])
        # Handle multiple return values
        elif len(operation.values) > 1:
            self._handle_multiple_return_values(node, domain, operation.values)

    def _handle_single_return_value(
        self, node: Node, domain: IntervalDomain, return_value: Variable
    ) -> None:
        """Handle a single return value."""
        if isinstance(return_value, Constant):
            const_value = Decimal(str(return_value.value))
            return_type = node.function.return_type[0] if node.function.return_type else None

            if return_type and isinstance(return_type, ElementaryType):
                var_type = return_type
            else:
                var_type = None

            return_var_name = str(const_value)
            domain.state.info[return_var_name] = IntervalInfo(
                upper_bound=const_value,
                lower_bound=const_value,
                var_type=var_type,
            )
        elif isinstance(return_value, Variable):
            return_var_name = self.variable_manager.get_canonical_name(return_value)
            if return_var_name in domain.state.info:
                # Create a return value entry with the variable's constraints
                return_type = node.function.return_type[0] if node.function.return_type else None
                var_type = return_type if isinstance(return_type, ElementaryType) else None

                # Create a return value identifier with the variable's constraints
                domain.state.info[f"return_{return_var_name}"] = domain.state.info[
                    return_var_name
                ].deep_copy()

    def _handle_multiple_return_values(
        self, node: Node, domain: IntervalDomain, return_values: List[Variable]
    ) -> None:
        """Handle multiple return values."""
        if not node.function.return_type or len(node.function.return_type) != len(return_values):
            return

        for i, (return_value, return_type) in enumerate(
            zip(return_values, node.function.return_type)
        ):
            # Only process numeric types
            if not isinstance(return_type, ElementaryType) or not self.type_system.is_numeric_type(
                return_type
            ):
                continue

            # Create a variable name for this return value
            return_var_name = f"return_{i}"

            if isinstance(return_value, Constant):
                # Return value is a literal constant
                const_value = Decimal(str(return_value.value))
                domain.state.info[return_var_name] = IntervalInfo(
                    upper_bound=const_value,
                    lower_bound=const_value,
                    var_type=return_type,
                )
            elif isinstance(return_value, Variable):
                # Return value is a variable
                var_name = self.variable_manager.get_canonical_name(return_value)
                if var_name in domain.state.info:
                    domain.state.info[return_var_name] = domain.state.info[var_name].deep_copy()

    def _retrieve_interval_info(
        self,
        var: Union[Variable, Constant, RVALUE, Function],
        domain: IntervalDomain,
        operation: Binary,
    ) -> IntervalInfo:
        """Retrieve interval information for a variable or constant."""
        if isinstance(var, Constant):
            value: Decimal = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            var_name: str = self.variable_manager.get_canonical_name(var)
            return domain.state.info.get(var_name, IntervalInfo(var_type=None))
        return IntervalInfo(var_type=None)
