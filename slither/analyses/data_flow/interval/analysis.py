from decimal import Decimal
from typing import List, Optional, Dict, Union, TypedDict, Callable

from loguru import logger

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval.domain import DomainVariant, IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.state import IntervalState
from slither.analyses.data_flow.interval.util import (
    _create_interval_from_type,
    _determine_target_type,
    _get_type_bounds_for_elementary_type,
    _is_numeric_type,
)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.operation import Operation

from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class TempVarRelationship(TypedDict):
    operation_type: BinaryType
    left_var: Union[Variable, Constant, RVALUE, Function]
    right_var: Union[Variable, Constant, RVALUE, Function]


class IntervalAnalysis(Analysis):
    # Class constants for commonly used values

    # Arithmetic operators
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

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        # Track pending constraints that haven't been enforced yet
        self._pending_constraints: Dict[str, Union[Binary, Variable]] = {}
        # Track relationships between temporary variables and their source variables
        self._temp_var_sources: Dict[str, TempVarRelationship] = {}

    def domain(self) -> Domain:
        return IntervalDomain.with_state({})

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom()

    def transfer_function(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
        functions: List[Function],
    ) -> None:
        self.transfer_function_helper(node, domain, operation)

    def transfer_function_helper(
        self, node: Node, domain: IntervalDomain, operation: Operation
    ) -> None:
        if domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.BOTTOM:
            self._initialize_domain_from_bottom(node, domain)
            self._analyze_operation_by_type(operation, domain, node)
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with function parameters."""
        domain.variant = DomainVariant.STATE
        domain.state = IntervalState({})

        for parameter in node.function.parameters:
            if isinstance(parameter.type, ElementaryType) and _is_numeric_type(parameter.type):
                domain.state.info[parameter.canonical_name] = _create_interval_from_type(
                    parameter.type, parameter.type.min, parameter.type.max
                )

    def _analyze_operation_by_type(
        self, operation: Operation, domain: IntervalDomain, node: Node
    ) -> None:
        """Route operation to appropriate handler based on type."""
        if isinstance(operation, Binary):
            if operation.type in self.ARITHMETIC_OPERATORS:
                self.handle_arithmetic_operation(domain, operation, node)
            elif (
                operation.type in self.COMPARISON_OPERATORS
                or operation.type in self.LOGICAL_OPERATORS
            ):
                self.handle_comparison_operation(node, domain, operation)
        elif isinstance(operation, Assignment):
            self.handle_assignment(node, domain, operation)
        elif isinstance(operation, SolidityCall):
            self.handle_solidity_call(node, domain, operation)

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        if operation.function.name not in require_assert_functions:
            return

        if operation.arguments and len(operation.arguments) > 0:
            condition = operation.arguments[0]
            self._apply_constraint_from_condition(condition, domain, operation)

    def _apply_constraint_from_condition(
        self, condition: Union[Binary, Variable], domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Extract and apply constraint from a condition in require/assert."""
        if isinstance(condition, Binary) and condition.type in self.COMPARISON_OPERATORS:
            # This is a comparison operation, apply the constraint
            self._apply_comparison_constraint_from_operation(condition, domain)
        elif isinstance(condition, Binary) and condition.type in self.LOGICAL_OPERATORS:
            # This is a logical operation, recursively extract constraints from operands
            self._apply_logical_constraint_from_operation(condition, domain)
        elif isinstance(condition, Variable):
            # The condition is a variable, check if we have a pending constraint for it
            self._apply_pending_constraint_for_variable(condition, domain)

    def _apply_pending_constraint_for_variable(self, var: Variable, domain: IntervalDomain) -> None:
        """Apply pending constraint for a variable if it exists."""
        var_name: str = self.get_variable_name(var)

        if var_name not in self._pending_constraints:
            logger.debug(f"No pending constraint found for {var_name}")
            return

        constraint_operation: Union[Binary, Variable] = self._pending_constraints[var_name]

        # Apply the constraint based on its type
        if isinstance(constraint_operation, Binary):
            if constraint_operation.type in self.LOGICAL_OPERATORS:
                self._apply_logical_constraint_from_operation(constraint_operation, domain)
            elif constraint_operation.type in self.COMPARISON_OPERATORS:
                self._apply_comparison_constraint_from_operation(constraint_operation, domain)

        # Remove the constraint from pending since it's now applied
        del self._pending_constraints[var_name]

    def _apply_comparison_constraint_from_operation(
        self, operation: Binary, domain: IntervalDomain
    ) -> None:
        if not hasattr(operation, "variable_left") or not hasattr(operation, "variable_right"):
            return

        left_var: Union[Variable, Constant, RVALUE, Function] = operation.variable_left
        right_var: Union[Variable, Constant, RVALUE, Function] = operation.variable_right
        left_interval: IntervalInfo = self.retrieve_interval_info(left_var, domain, operation)
        right_interval: IntervalInfo = self.retrieve_interval_info(right_var, domain, operation)

        # Determine variable types
        left_is_variable: bool = self._is_variable_not_constant(left_var)
        right_is_variable: bool = self._is_variable_not_constant(right_var)

        # Handle different comparison scenarios
        if left_is_variable and not right_is_variable:
            if isinstance(left_var, Variable):
                self._update_variable_bounds_from_comparison(
                    left_var, right_interval, operation.type, domain
                )
        elif not left_is_variable and right_is_variable:
            flipped_op: BinaryType = self._flip_comparison_operator(operation.type)
            if isinstance(right_var, Variable):
                self._update_variable_bounds_from_comparison(
                    right_var, left_interval, flipped_op, domain
                )
        elif left_is_variable and right_is_variable:
            if isinstance(left_var, Variable) and isinstance(right_var, Variable):
                self._handle_variable_to_variable_comparison(
                    left_var, right_var, operation.type, domain
                )

    def _is_variable_not_constant(self, var: Union[Variable, Constant, RVALUE, Function]) -> bool:
        """Check if variable is a Variable but not a Constant."""
        return isinstance(var, Variable) and not isinstance(var, Constant)

    def _flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip comparison operator for handling constant-variable comparisons."""
        flip_map: Dict[BinaryType, BinaryType] = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,
        }
        return flip_map[op_type]

    def _update_variable_bounds_from_comparison(
        self,
        variable: Variable,
        constraint_interval: IntervalInfo,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Update variable bounds based on comparison operation."""
        var_name: str = self.get_variable_name(variable)
        current_interval: IntervalInfo = self._get_or_create_interval_for_variable(variable, domain)
        constraint_value: Decimal = constraint_interval.lower_bound
        new_interval: IntervalInfo = current_interval.deep_copy()

        # Apply comparison constraints
        self._apply_comparison_constraint(new_interval, constraint_value, op_type)

        # Check for invalid interval
        if new_interval.lower_bound > new_interval.upper_bound:
            domain.variant = DomainVariant.BOTTOM
            logger.error(f"Invalid interval: {new_interval}")
            raise ValueError(f"Invalid interval: {new_interval}")

        domain.state.info[var_name] = new_interval

    def _get_or_create_interval_for_variable(
        self, variable: Variable, domain: IntervalDomain
    ) -> IntervalInfo:
        """Get existing interval or create new one with type bounds."""
        var_name: str = self.get_variable_name(variable)

        if var_name in domain.state.info:
            return domain.state.info[var_name]

        var_type: Optional[ElementaryType] = getattr(variable, "type", None)
        interval: IntervalInfo = IntervalInfo(var_type=var_type)

        if isinstance(var_type, ElementaryType) and _is_numeric_type(var_type):
            min_val: Decimal
            max_val: Decimal
            min_val, max_val = _get_type_bounds_for_elementary_type(var_type)
            interval.lower_bound = min_val
            interval.upper_bound = max_val

        return interval

    def _apply_comparison_constraint(
        self, interval: IntervalInfo, constraint_value: Decimal, op_type: BinaryType
    ) -> None:
        """Apply comparison constraint to interval bounds."""
        if op_type == BinaryType.GREATER_EQUAL:
            interval.lower_bound = max(interval.lower_bound, constraint_value)
        elif op_type == BinaryType.GREATER:
            interval.lower_bound = max(interval.lower_bound, constraint_value + Decimal("1"))
        elif op_type == BinaryType.LESS_EQUAL:
            interval.upper_bound = min(interval.upper_bound, constraint_value)
        elif op_type == BinaryType.LESS:
            interval.upper_bound = min(interval.upper_bound, constraint_value - Decimal("1"))
        elif op_type == BinaryType.EQUAL:
            if (
                constraint_value >= interval.lower_bound
                and constraint_value <= interval.upper_bound
            ):
                interval.lower_bound = interval.upper_bound = constraint_value
            else:
                interval.lower_bound = Decimal("1")
                interval.upper_bound = Decimal("0")
        elif op_type == BinaryType.NOT_EQUAL:
            if constraint_value == interval.lower_bound == interval.upper_bound:
                interval.lower_bound = Decimal("1")
                interval.upper_bound = Decimal("0")
            elif constraint_value == interval.lower_bound:
                interval.lower_bound = constraint_value + Decimal("1")
            elif constraint_value == interval.upper_bound:
                interval.upper_bound = constraint_value - Decimal("1")

    def _handle_variable_to_variable_comparison(
        self,
        left_var: Variable,
        right_var: Variable,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Handle comparison between two variables."""
        left_name: str = self.get_variable_name(left_var)
        right_name: str = self.get_variable_name(right_var)

        left_interval: Optional[IntervalInfo] = domain.state.info.get(left_name)
        right_interval: Optional[IntervalInfo] = domain.state.info.get(right_name)

        if not left_interval or not right_interval:
            return

        new_left: IntervalInfo = left_interval.deep_copy()
        new_right: IntervalInfo = right_interval.deep_copy()

        # Apply variable-to-variable comparison constraints
        self._apply_variable_comparison_constraints(new_left, new_right, op_type)

        # Check for invalid intervals
        if (
            new_left.lower_bound > new_left.upper_bound
            or new_right.lower_bound > new_right.upper_bound
        ):
            domain.variant = DomainVariant.BOTTOM
            return

        domain.state.info[left_name] = new_left
        domain.state.info[right_name] = new_right

    def _apply_variable_comparison_constraints(
        self, left: IntervalInfo, right: IntervalInfo, op_type: BinaryType
    ) -> None:
        """Apply constraints for variable-to-variable comparisons."""
        if op_type == BinaryType.EQUAL:
            self._apply_equality_constraints(left, right)
        elif op_type == BinaryType.NOT_EQUAL:
            self._apply_inequality_constraints(left, right)
        elif op_type == BinaryType.LESS:
            self._apply_less_than_constraints(left, right)
        elif op_type == BinaryType.LESS_EQUAL:
            self._apply_less_equal_constraints(left, right)
        elif op_type == BinaryType.GREATER:
            self._apply_greater_than_constraints(left, right)
        elif op_type == BinaryType.GREATER_EQUAL:
            self._apply_greater_equal_constraints(left, right)

    def _apply_equality_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply equality constraints between two intervals."""
        common_lower: Decimal = max(left.lower_bound, right.lower_bound)
        common_upper: Decimal = min(left.upper_bound, right.upper_bound)

        if common_lower <= common_upper:
            left.lower_bound = right.lower_bound = common_lower
            left.upper_bound = right.upper_bound = common_upper

    def _apply_inequality_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply inequality constraints between two intervals."""
        if (
            left.lower_bound == left.upper_bound
            and right.lower_bound == right.upper_bound
            and left.lower_bound == right.lower_bound
        ):
            # Both intervals are single points with same value - impossible inequality
            left.lower_bound = Decimal("1")
            left.upper_bound = Decimal("0")
            right.lower_bound = Decimal("1")
            right.upper_bound = Decimal("0")

    def _apply_less_than_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply less than constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound - Decimal("1"))
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound + Decimal("1"))

    def _apply_less_equal_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply less than or equal constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound)
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound)

    def _apply_greater_than_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply greater than constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound - Decimal("1"))
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound + Decimal("1"))

    def _apply_greater_equal_constraints(self, left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply greater than or equal constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound)
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound)

    def handle_arithmetic_operation(
        self, domain: IntervalDomain, operation: Binary, node: Node
    ) -> None:
        """Handle arithmetic operations and compute result intervals."""
        left_interval_info: IntervalInfo = self.retrieve_interval_info(
            operation.variable_left, domain, operation
        )
        right_interval_info: IntervalInfo = self.retrieve_interval_info(
            operation.variable_right, domain, operation
        )

        lower_bound: Decimal
        upper_bound: Decimal
        lower_bound, upper_bound = self.calculate_min_max(
            left_interval_info.lower_bound,
            left_interval_info.upper_bound,
            right_interval_info.lower_bound,
            right_interval_info.upper_bound,
            operation.type,
        )

        if not isinstance(operation.lvalue, Variable):
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

        variable_name: str = self.get_variable_name(operation.lvalue)
        target_type: Optional[ElementaryType] = _determine_target_type(operation)

        new_interval: IntervalInfo = IntervalInfo(
            upper_bound=upper_bound, lower_bound=lower_bound, var_type=target_type
        )
        domain.state.info[variable_name] = new_interval

        # Track relationship between temporary variable and source variables
        if isinstance(operation.lvalue, TemporaryVariable):
            self._track_temp_var_relationship(operation, domain)

    def _track_temp_var_relationship(self, operation: Binary, domain: IntervalDomain) -> None:
        """Track the relationship between a temporary variable and its source variables."""
        if operation.lvalue is None:
            return

        temp_var_name: str = self.get_variable_name(operation.lvalue)

        # Store the relationship: temp_var -> (operation_type, left_var, right_var)
        self._temp_var_sources[temp_var_name] = {
            "operation_type": operation.type,
            "left_var": operation.variable_left,
            "right_var": operation.variable_right,
        }

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        """Handle assignment operations."""
        if operation.lvalue is None:
            return

        written_variable: Variable = operation.lvalue
        right_value = operation.rvalue
        writing_variable_name: str = self.get_variable_name(written_variable)

        # Check if the assignment is a comparison or logical operation
        if isinstance(right_value, Binary) and (
            right_value.type in self.COMPARISON_OPERATORS
            or right_value.type in self.LOGICAL_OPERATORS
        ):
            # Store as pending constraint
            self._pending_constraints[writing_variable_name] = right_value
        elif isinstance(right_value, TemporaryVariable):
            # Check if the temporary variable has a pending constraint
            temp_var_name: str = self.get_variable_name(right_value)
            if temp_var_name in self._pending_constraints:
                # Copy the constraint from the temporary variable to the local variable
                self._pending_constraints[writing_variable_name] = self._pending_constraints[
                    temp_var_name
                ]
                # Remove the constraint from the temporary variable
                del self._pending_constraints[temp_var_name]

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
        target_type: Optional[ElementaryType] = getattr(target_var, "type", None)
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
        source_name: str = self.get_variable_name(source_var)
        if source_name in domain.state.info:
            source_interval: IntervalInfo = domain.state.info[source_name]
            target_type: Optional[ElementaryType] = getattr(target_var, "type", None)

            new_interval: IntervalInfo = source_interval.deep_copy()
            new_interval.var_type = target_type

            # Apply type bounds if necessary
            if isinstance(target_type, ElementaryType) and _is_numeric_type(target_type):
                target_min: Decimal
                target_max: Decimal
                target_min, target_max = _get_type_bounds_for_elementary_type(target_type)
                new_interval.lower_bound = max(new_interval.lower_bound, target_min)
                new_interval.upper_bound = min(new_interval.upper_bound, target_max)

            domain.state.info[var_name] = new_interval

    def retrieve_interval_info(
        self, var: Union[RVALUE, Function], domain: IntervalDomain, operation: Binary
    ) -> IntervalInfo:
        """Retrieve interval information for a variable or constant."""
        if isinstance(var, Constant):
            value: Decimal = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            var_name: str = self.get_variable_name(var)
            return domain.state.info.get(
                var_name, IntervalInfo(Decimal(0), Decimal(0), var_type=None)
            )

        return IntervalInfo(var_type=None)

    def get_variable_name(self, variable: Variable) -> str:
        """Get canonical variable name."""
        if isinstance(variable, (StateVariable, LocalVariable)):
            variable_name: Optional[str] = variable.canonical_name
        else:
            variable_name: Optional[str] = variable.name

        if variable_name is None:
            raise ValueError(f"Variable name is None for variable: {variable}")

        return variable_name

    def calculate_min_max(
        self, a: Decimal, b: Decimal, c: Decimal, d: Decimal, operation_type: BinaryType
    ) -> tuple[Decimal, Decimal]:
        """Calculate min and max bounds for arithmetic operations."""

        operations: Dict[BinaryType, Callable[[Decimal, Decimal], Decimal]] = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }

        op: Callable[[Decimal, Decimal], Decimal] = operations[operation_type]
        results: List[Decimal] = [op(a, c), op(a, d), op(b, c), op(b, d)]

        return min(results), max(results)

    def handle_comparison_operation(
        self, node: Node, domain: IntervalDomain, operation: Binary
    ) -> None:
        """Handle comparison operations by storing them as pending constraints."""

        if hasattr(operation, "lvalue") and operation.lvalue:
            var_name: str = self.get_variable_name(operation.lvalue)
            self._pending_constraints[var_name] = operation

    def _apply_logical_constraint_from_operation(
        self, operation: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraints from a logical operation by recursively extracting constraints from operands."""
        if not hasattr(operation, "variable_left") or not hasattr(operation, "variable_right"):
            return

        left_operand: Union[Variable, Constant, RVALUE, Function] = operation.variable_left
        right_operand: Union[Variable, Constant, RVALUE, Function] = operation.variable_right

        # Recursively apply constraints
        self._apply_constraint_from_operand(left_operand, domain)
        self._apply_constraint_from_operand(right_operand, domain)

    def _apply_constraint_from_operand(
        self, operand: Union[Variable, Constant, RVALUE, Function], domain: IntervalDomain
    ) -> None:
        """Apply constraint from a single operand of a logical operation."""

        if isinstance(operand, Binary) and operand.type in self.COMPARISON_OPERATORS:
            self._apply_comparison_constraint_from_operation(operand, domain)
        elif isinstance(operand, Binary) and operand.type in self.LOGICAL_OPERATORS:
            self._apply_logical_constraint_from_operation(operand, domain)
        elif isinstance(operand, Variable):
            # The operand is a variable, check if we have a pending constraint for it
            self._apply_pending_constraint_for_variable(operand, domain)
        else:
            logger.error(f"Unknown operand type: {operand}")
            raise ValueError(f"Unknown operand type: {operand}")
