from decimal import Decimal
from typing import Dict, List, Optional, Union

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.arithmetic_solver_manager import (
    ArithmeticSolverManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_application_manager import (
    ConstraintApplicationManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_range_manager import (
    ConstraintRangeManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ConstraintManager:
    """Main orchestrator for constraint management in interval analysis."""

    ARITHMETIC_OPERATORS: set[BinaryType] = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }

    # Comparison operators
    COMPARISON_OPERATORS: set[BinaryType] = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    # Logical operators
    LOGICAL_OPERATORS: set[BinaryType] = {
        BinaryType.ANDAND,
        BinaryType.OROR,
    }

    def __init__(self):
        self._pending_constraints: Dict[str, Union[Binary, Variable]] = {}
        self._temp_var_mappings: Dict[str, Binary] = (
            {}
        )  # Track temp vars to their source expressions

        # Initialize component managers
        self.variable_manager = VariableManager()
        self.operand_analyzer = OperandAnalysisManager(self.variable_manager)
        self.constraint_range_manager = ConstraintRangeManager(self.variable_manager)
        self.arithmetic_solver = ArithmeticSolverManager(
            self.operand_analyzer, self.constraint_range_manager
        )
        self.constraint_application_manager = ConstraintApplicationManager(
            self.operand_analyzer,
            self.constraint_range_manager,
            self.arithmetic_solver,
            self.variable_manager,
        )

    # Core constraint storage methods
    def add_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Add a pending constraint for a variable"""
        self._pending_constraints[var_name] = constraint

    def remove_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Remove and return a constraint for a variable"""
        constraint = self._pending_constraints.pop(var_name, None)
        return constraint

    def get_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Get constraint for a variable without removing it"""
        return self._pending_constraints.get(var_name)

    def has_constraint(self, var_name: str) -> bool:
        """Check if variable has a pending constraint"""
        return var_name in self._pending_constraints

    def get_all_constraints(self) -> Dict[str, Union[Binary, Variable]]:
        """Get all pending constraints"""
        return self._pending_constraints.copy()

    def clear_constraints(self, var_name: str = "") -> None:
        """Clear constraints for a specific variable or all constraints"""
        if var_name:
            if var_name in self._pending_constraints:
                del self._pending_constraints[var_name]
                logger.debug(f"Cleared constraint for variable '{var_name}'")
        else:
            self._pending_constraints.clear()
            logger.debug("Cleared all pending constraints")

    def get_constraint_count(self) -> int:
        """Get the number of pending constraints"""
        return len(self._pending_constraints)

    def list_constrained_variables(self) -> List[str]:
        """Get list of all variables with pending constraints"""
        return list(self._pending_constraints.keys())

    def enforce_constraints_on_variable(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Get and optionally remove constraint when enforcing (for one-time use constraints)"""
        return self.get_constraint(var_name)

    def peek_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Alias for get_constraint - clearer intent when just checking"""
        return self.get_constraint(var_name)

    # Temporary variable mapping methods
    def add_temp_var_mapping(self, temp_var_name: str, source_operationession: Binary) -> None:
        """Track a temporary variable's source arithmetic expression."""
        self._temp_var_mappings[temp_var_name] = source_operationession

    def get_temp_var_mapping(self, temp_var_name: str) -> Optional[Binary]:
        """Get the source expression for a temporary variable."""
        return self._temp_var_mappings.get(temp_var_name)

    def has_temp_var_mapping(self, temp_var_name: str) -> bool:
        """Check if a temporary variable has a source expression mapping."""
        return temp_var_name in self._temp_var_mappings

    # Constraint application orchestration
    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition variable"""
        variable_name = self.variable_manager.get_variable_name(condition_variable)
        constraint = self.get_constraint(variable_name)

        if isinstance(constraint, Binary):
            self.apply_constraint_from_binary_condition(constraint, domain)
        elif isinstance(constraint, Variable):
            self.apply_constraint_from_variable(constraint, domain)

    def apply_constraint_from_binary_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from a binary condition"""
        if condition.type in self.COMPARISON_OPERATORS:
            self.apply_constraint_from_comparison_condition(condition, domain)
        elif condition.type in self.LOGICAL_OPERATORS:
            self.apply_constraint_from_logical_condition(condition, domain)
        else:
            logger.error(f"Unknown binary operator: {condition.type}")
            raise ValueError(f"Unknown binary operator: {condition.type}")

    def apply_constraint_from_logical_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraints from a logical condition"""
        if not hasattr(condition, "variable_left") or not hasattr(condition, "variable_right"):
            return

        left_operand = condition.variable_left
        right_operand = condition.variable_right

        if not isinstance(left_operand, Variable) or not isinstance(right_operand, Variable):
            logger.debug(f"Unknown operand type: {left_operand} or {right_operand}")
            return

        self.apply_constraint_from_variable(left_operand, domain)
        self.apply_constraint_from_variable(right_operand, domain)

    def apply_constraint_from_comparison_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from comparison condition by refining variable bounds"""
        # Get the left and right operands
        left_operand = condition.variable_left
        right_operand = condition.variable_right

        left_is_variable = not self.operand_analyzer.is_operand_constant(left_operand, domain)
        right_is_variable = not self.operand_analyzer.is_operand_constant(right_operand, domain)

        if left_is_variable and not right_is_variable:
            # Check if this is a temporary variable with an arithmetic mapping

            if isinstance(left_operand, Variable):
                left_var_name = self.variable_manager.get_variable_name(left_operand)

                if self.has_temp_var_mapping(left_var_name):

                    source_operation = self.get_temp_var_mapping(left_var_name)
                    if source_operation:
                        # Handle as arithmetic constraint
                        if isinstance(right_operand, Constant):
                            self.arithmetic_solver.handle_arithmetic_comparison_constraint(
                                source_operation,
                                Decimal(right_operand.value),
                                condition.type,
                                domain,
                            )
                        elif isinstance(right_operand, Variable):
                            # Handle case where right operand is not a constant but has one valid value
                            right_var_name = self.variable_manager.get_variable_name(right_operand)
                            right_state_info = domain.state.info[right_var_name]

                            # Extract the single valid value
                            constant_value = list(right_state_info.valid_values)[0]
                            self.arithmetic_solver.handle_arithmetic_comparison_constraint(
                                source_operation,
                                constant_value,
                                condition.type,
                                domain,
                            )

                else:
                    # Handle as regular variable constraint
                    self.constraint_application_manager.apply_constraint_from_comparison_condition(
                        condition, domain
                    )

        elif right_is_variable and not left_is_variable:
            # Check if this is a temporary variable with an arithmetic mapping
            if isinstance(right_operand, Variable):
                right_var_name = self.variable_manager.get_variable_name(right_operand)
                if self.has_temp_var_mapping(right_var_name):
                    source_operation = self.get_temp_var_mapping(right_var_name)
                    if source_operation:
                        # Handle as arithmetic constraint
                        if isinstance(left_operand, Constant):
                            flipped_op_type = (
                                self.constraint_range_manager.flip_comparison_operator(
                                    condition.type
                                )
                            )
                            self.arithmetic_solver.handle_arithmetic_comparison_constraint(
                                source_operation,
                                Decimal(left_operand.value),
                                flipped_op_type,
                                domain,
                            )
                else:
                    # Handle as regular variable constraint
                    self.constraint_application_manager.apply_constraint_from_comparison_condition(
                        condition, domain
                    )

        elif left_is_variable and right_is_variable:
            # Handle as variable-to-variable comparison
            self.constraint_application_manager.apply_constraint_from_comparison_condition(
                condition, domain
            )

        else:
            # Case 4: constant < constant, constant > constant, etc.
            # This is a compile-time constant expression, no variables to constrain
            logger.debug(f"Constant comparison: {left_operand} {condition.type} {right_operand}")

    def propagate_constraints_from_caller_to_callee(
        self,
        operation_arguments: List[Variable],
        function_parameters: List[LocalVariable],
        domain: IntervalDomain,
    ) -> None:
        """Propagate constraints from caller arguments to callee parameters."""
        for arg, param in zip(operation_arguments, function_parameters):
            if not (
                isinstance(param.type, ElementaryType)
                and self.variable_manager.is_type_numeric(param.type)
            ):
                continue

            arg_name = self.variable_manager.get_variable_name(arg)
            param_name = self.variable_manager.get_variable_name(param)

            # The argument should be in the domain at this point
            if arg_name not in domain.state.info:
                logger.error(
                    f"Argument '{arg_name}' not found in domain state during interprocedural analysis"
                )
                raise ValueError(
                    f"Argument '{arg_name}' not found in domain state during interprocedural analysis"
                )

            arg_state_info = domain.state.info[arg_name]

            # Initialize parameter with deep copy of argument constraints
            domain.state.info[param_name] = arg_state_info.deep_copy()

    def propagate_constraints_from_callee_to_caller(
        self,
        operation_arguments: List[Variable],
        function_parameters: List[LocalVariable],
        domain: IntervalDomain,
    ) -> None:
        """Propagate constraints from callee parameters back to caller arguments."""
        for arg, param in zip(operation_arguments, function_parameters):
            if not (
                isinstance(param.type, ElementaryType)
                and self.variable_manager.is_type_numeric(param.type)
            ):
                continue

            arg_name = self.variable_manager.get_variable_name(arg)
            param_name = self.variable_manager.get_variable_name(param)

            # If the parameter has constraints in the callee, propagate them back to the argument
            if param_name in domain.state.info:
                param_state_info = domain.state.info[param_name]

                if arg_name in domain.state.info:
                    # Use constraint application manager to merge constraints
                    self.constraint_application_manager.merge_constraints_from_callee(
                        arg_name, param_state_info, domain
                    )
                else:
                    # Create new state info for the argument
                    domain.state.info[arg_name] = param_state_info.deep_copy()

    def apply_return_value_constraints(
        self,
        operation_lvalue: Variable,
        return_values: List[Variable],
        return_types: List,
        domain: IntervalDomain,
    ) -> None:
        """Apply return value constraints to the caller's domain using constraint manager."""
        if not operation_lvalue or not return_types:
            return

        # Handle single return value
        if len(return_values) == 1 and len(return_types) == 1:
            return_type = return_types[0]
            if isinstance(return_type, ElementaryType) and self.variable_manager.is_type_numeric(
                return_type
            ):
                return_value = return_values[0]
                result_var_name = self.variable_manager.get_variable_name(operation_lvalue)

                if isinstance(return_value, Variable):
                    return_var_name = self.variable_manager.get_variable_name(return_value)
                    # Look for the return value identifier created by OperationHandler
                    return_identifier = f"return_{return_var_name}"
                    if return_identifier in domain.state.info:
                        domain.state.info[result_var_name] = domain.state.info[
                            return_identifier
                        ].deep_copy()
                    elif return_var_name in domain.state.info:
                        # Fallback to original variable name
                        domain.state.info[result_var_name] = domain.state.info[
                            return_var_name
                        ].deep_copy()
                elif isinstance(return_value, Constant):
                    # Use constraint application manager to create constant constraint
                    self.constraint_application_manager.create_constant_constraint(
                        result_var_name, return_value, return_type, domain
                    )

        # Handle multiple return values
        elif len(return_values) > 1 and len(return_types) > 1:
            self._process_multiple_return_values(
                operation_lvalue, return_values, return_types, domain
            )

    def _process_multiple_return_values(
        self,
        operation_lvalue: Variable,
        return_values: List[Variable],
        return_types: List[Type],
        domain: IntervalDomain,
    ) -> None:
        """Process multiple return values and apply constraints."""
        if not operation_lvalue or not hasattr(operation_lvalue, "type"):
            return

        # Handle tuple return values
        if hasattr(operation_lvalue.type, "__iter__") and return_types:
            for i, (return_value, return_type) in enumerate(zip(return_values, return_types)):
                # Only process numeric types
                if not (
                    isinstance(return_type, ElementaryType)
                    and self.variable_manager.is_type_numeric(return_type)
                ):
                    continue

                # Create a variable name for this return value
                return_var_name = f"return_{i}"

                if isinstance(return_value, Constant):
                    # Use constraint application manager to create constant constraint
                    self.constraint_application_manager.create_constant_constraint(
                        return_var_name, return_value, return_type, domain
                    )
                elif isinstance(return_value, Variable):
                    # Return value is a variable
                    var_name = self.variable_manager.get_variable_name(return_value)
                    if var_name in domain.state.info:
                        domain.state.info[return_var_name] = domain.state.info[var_name].deep_copy()
