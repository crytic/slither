from decimal import Decimal
from typing import List, Optional, Tuple

from loguru import logger

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval.domain import DomainVariant, IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.analyses.data_flow.interval.state import IntervalState
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class IntervalAnalysis(Analysis):
    # Class constants for commonly used values
    UINT256_MAX = Decimal(
        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
    )
    INT256_MAX = Decimal(
        "57896044618658097711785492504343953926634992332820282019728792003956564819967"
    )
    INT256_MIN = Decimal(
        "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
    )

    # Comparison operators that can be flipped
    FLIPPABLE_COMPARISON_OPERATORS = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    # Arithmetic operators
    ARITHMETIC_OPERATORS = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }

    # Comparison operators
    COMPARISON_OPERATORS = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    def __init__(self):
        self._direction = Forward()

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
    ):
        self.transfer_function_helper(node, domain, operation)

    def transfer_function_helper(self, node: Node, domain: IntervalDomain, operation: Operation):
        if domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.BOTTOM:
            self._initialize_domain_from_bottom(node, domain)
            self._analyze_operation_by_type(operation, domain, node)
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain):
        """Initialize domain state from bottom variant with function parameters."""
        domain.variant = DomainVariant.STATE
        domain.state = IntervalState({})

        for parameter in node.function.parameters:
            if isinstance(parameter.type, ElementaryType) and self._is_numeric_type(parameter.type):
                domain.state.info[parameter.canonical_name] = self._create_interval_from_type(
                    parameter.type, parameter.type.min, parameter.type.max
                )

    def _analyze_operation_by_type(self, operation: Operation, domain: IntervalDomain, node: Node):
        """Route operation to appropriate handler based on type."""
        if isinstance(operation, Binary):
            if operation.type in self.ARITHMETIC_OPERATORS:
                self.handle_arithmetic_operation(domain, operation, node)
        elif isinstance(operation, Assignment):
            self.handle_assignment(node, domain, operation)
        elif isinstance(operation, SolidityCall):
            self.handle_solidity_call(node, domain, operation)

    def handle_solidity_call(self, node: Node, domain: IntervalDomain, operation: SolidityCall):
        require_assert_functions = [
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
        self, condition, domain: IntervalDomain, operation: SolidityCall
    ):

        # Check if the condition is a comparison operation
        if hasattr(condition, "type") and condition.type in self.COMPARISON_OPERATORS:
            # This is a comparison operation, apply the constraint
            self._apply_comparison_constraint_from_operation(condition, domain)
        elif hasattr(condition, "variable_left") and hasattr(condition, "variable_right"):
            # This might be a Binary operation (comparison)
            if condition.type in self.COMPARISON_OPERATORS:
                self._apply_comparison_constraint_from_operation(condition, domain)
        elif isinstance(condition, TemporaryVariable):
            # The condition is a temporary variable, we need to find the operation that created it
            self._find_and_apply_constraint_from_temporary(condition, domain, operation.node)
        # TODO: handle condition that is a variable

    def _find_and_apply_constraint_from_temporary(
        self, temp_var: TemporaryVariable, domain: IntervalDomain, node: Node
    ):
        # Look through the node's IR operations to find the operation that created this temporary variable
        for ir in node.irs:
            if (
                isinstance(ir, Binary)
                and ir.lvalue == temp_var
                and ir.type in self.COMPARISON_OPERATORS
            ):
                # Found the comparison operation that created this temporary variable
                self._apply_comparison_constraint_from_operation(ir, domain)
                return

    def _apply_comparison_constraint_from_operation(self, operation, domain: IntervalDomain):
        if not hasattr(operation, "variable_left") or not hasattr(operation, "variable_right"):
            return

        left_var, right_var = operation.variable_left, operation.variable_right
        left_interval = self.retrieve_interval_info(left_var, domain, operation)
        right_interval = self.retrieve_interval_info(right_var, domain, operation)

        # Determine variable types
        left_is_variable = self._is_variable_not_constant(left_var)
        right_is_variable = self._is_variable_not_constant(right_var)
        left_is_constant = isinstance(left_var, Constant)
        right_is_constant = isinstance(right_var, Constant)

        # Handle different comparison scenarios
        if left_is_variable and right_is_constant:
            if isinstance(left_var, Variable):
                self._update_variable_bounds_from_comparison(
                    left_var, right_interval, operation.type, domain
                )
        elif left_is_constant and right_is_variable:
            flipped_op = self._flip_comparison_operator(operation.type)
            if isinstance(right_var, Variable):
                self._update_variable_bounds_from_comparison(
                    right_var, left_interval, flipped_op, domain
                )
        elif left_is_variable and right_is_variable:
            if isinstance(left_var, Variable) and isinstance(right_var, Variable):
                self._handle_variable_to_variable_comparison(
                    left_var, right_var, operation.type, domain
                )

    def _is_variable_not_constant(self, var) -> bool:
        """Check if variable is a Variable but not a Constant."""
        return isinstance(var, Variable) and not isinstance(var, Constant)

    def _flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip comparison operator for handling constant-variable comparisons."""
        flip_map = {
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
    ):
        """Update variable bounds based on comparison operation."""
        var_name = self.get_variable_name(variable)
        current_interval = self._get_or_create_interval_for_variable(variable, domain)
        constraint_value = constraint_interval.lower_bound
        new_interval = current_interval.deep_copy()

        # Apply comparison constraints
        self._apply_comparison_constraint(new_interval, constraint_value, op_type)

        # Check for invalid interval
        if new_interval.lower_bound > new_interval.upper_bound:
            domain.variant = DomainVariant.BOTTOM
            logger.error(f"Invalid interval: {new_interval}")
            raise ValueError(f"Invalid interval: {new_interval}")
            return

        domain.state.info[var_name] = new_interval

    def _get_or_create_interval_for_variable(
        self, variable: Variable, domain: IntervalDomain
    ) -> IntervalInfo:
        """Get existing interval or create new one with type bounds."""
        var_name = self.get_variable_name(variable)

        if var_name in domain.state.info:
            return domain.state.info[var_name]

        var_type = getattr(variable, "type", None)
        interval = IntervalInfo(var_type=var_type)

        if isinstance(var_type, ElementaryType) and self._is_numeric_type(var_type):
            min_val, max_val = self._get_type_bounds_for_elementary_type(var_type)
            interval.lower_bound = min_val
            interval.upper_bound = max_val

        return interval

    def _apply_comparison_constraint(
        self, interval: IntervalInfo, constraint_value: Decimal, op_type: BinaryType
    ):
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
    ):
        """Handle comparison between two variables."""
        left_name = self.get_variable_name(left_var)
        right_name = self.get_variable_name(right_var)

        left_interval = domain.state.info.get(left_name)
        right_interval = domain.state.info.get(right_name)

        if not left_interval or not right_interval:
            return

        new_left = left_interval.deep_copy()
        new_right = right_interval.deep_copy()

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
    ):
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

    def _apply_equality_constraints(self, left: IntervalInfo, right: IntervalInfo):
        """Apply equality constraints between two intervals."""
        common_lower = max(left.lower_bound, right.lower_bound)
        common_upper = min(left.upper_bound, right.upper_bound)

        if common_lower <= common_upper:
            left.lower_bound = left.upper_bound = common_lower
            right.lower_bound = right.upper_bound = common_lower

            if common_lower == common_upper:
                left.lower_bound = left.upper_bound = common_lower
                right.lower_bound = right.upper_bound = common_lower
            else:
                left.lower_bound = right.lower_bound = common_lower
                left.upper_bound = right.upper_bound = common_upper

    def _apply_inequality_constraints(self, left: IntervalInfo, right: IntervalInfo):
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

    def _apply_less_than_constraints(self, left: IntervalInfo, right: IntervalInfo):
        """Apply less than constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound - Decimal("1"))
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound + Decimal("1"))

    def _apply_less_equal_constraints(self, left: IntervalInfo, right: IntervalInfo):
        """Apply less than or equal constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound)
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound)

    def _apply_greater_than_constraints(self, left: IntervalInfo, right: IntervalInfo):
        """Apply greater than constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound - Decimal("1"))
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound + Decimal("1"))

    def _apply_greater_equal_constraints(self, left: IntervalInfo, right: IntervalInfo):
        """Apply greater than or equal constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound)
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound)

    def handle_arithmetic_operation(self, domain: IntervalDomain, operation: Binary, node: Node):
        """Handle arithmetic operations and compute result intervals."""
        left_interval_info = self.retrieve_interval_info(operation.variable_left, domain, operation)
        right_interval_info = self.retrieve_interval_info(
            operation.variable_right, domain, operation
        )

        lower_bound, upper_bound = self.calculate_min_max(
            left_interval_info.lower_bound,
            left_interval_info.upper_bound,
            right_interval_info.lower_bound,
            right_interval_info.upper_bound,
            operation.type,
        )

        if isinstance(operation.lvalue, Variable):
            variable_name = self.get_variable_name(operation.lvalue)
            target_type = self._determine_target_type(operation)

            new_interval = IntervalInfo(
                upper_bound=upper_bound, lower_bound=lower_bound, var_type=target_type
            )
            domain.state.info[variable_name] = new_interval
        else:
            logger.error(f"lvalue is not a variable for operation: {operation}")
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

    def _determine_target_type(self, operation: Binary) -> Optional[ElementaryType]:
        """Determine the target type for the operation result."""
        target_type = getattr(operation.lvalue, "type", None)

        # For temporary variables, infer type from operands
        if target_type is None and isinstance(operation.lvalue, TemporaryVariable):
            left_type = self._get_variable_type(operation.variable_left)
            right_type = self._get_variable_type(operation.variable_right)

            if left_type and right_type:
                target_type = self._get_promotion_type(left_type, right_type)
            elif left_type:
                target_type = left_type
            elif right_type:
                target_type = right_type

        return target_type

    def _get_variable_type(self, variable) -> Optional[ElementaryType]:
        """Safely get variable type."""
        return getattr(variable, "type", None) if hasattr(variable, "type") else None

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):
        """Handle assignment operations."""
        if operation.lvalue is None:
            return

        written_variable = operation.lvalue
        right_value = operation.rvalue
        writing_variable_name = self.get_variable_name(written_variable)

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
    ):
        """Handle assignment of constant value."""
        value = Decimal(str(constant.value))
        target_type = getattr(target_var, "type", None)
        domain.state.info[var_name] = IntervalInfo(
            upper_bound=value, lower_bound=value, var_type=target_type
        )

    def _handle_variable_assignment(
        self, var_name: str, source_var, target_var: Variable, domain: IntervalDomain
    ):
        """Handle assignment from another variable."""
        source_name = self.get_variable_name(source_var)
        if source_name in domain.state.info:
            source_interval = domain.state.info[source_name]
            target_type = getattr(target_var, "type", None)

            new_interval = source_interval.deep_copy()
            new_interval.var_type = target_type

            # Apply type bounds if necessary
            if isinstance(target_type, ElementaryType) and self._is_numeric_type(target_type):
                target_min, target_max = self._get_type_bounds_for_elementary_type(target_type)
                new_interval.lower_bound = max(new_interval.lower_bound, target_min)
                new_interval.upper_bound = min(new_interval.upper_bound, target_max)

            domain.state.info[var_name] = new_interval

    def retrieve_interval_info(
        self, var: RVALUE | Function, domain: IntervalDomain, operation: Binary
    ) -> IntervalInfo:
        """Retrieve interval information for a variable or constant."""
        if isinstance(var, Constant):
            value = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            var_name = self.get_variable_name(var)
            return domain.state.info.get(
                var_name, IntervalInfo(Decimal(0), Decimal(0), var_type=None)
            )

        return IntervalInfo(var_type=None)

    def get_variable_name(self, variable: Variable) -> str:
        """Get canonical variable name."""
        if isinstance(variable, (StateVariable, LocalVariable)):
            variable_name = variable.canonical_name
        else:
            variable_name = variable.name

        if variable_name is None:
            logger.error(f"Variable name is None for variable: {variable}")
            raise ValueError(f"Variable name is None for variable: {variable}")

        return variable_name

    def calculate_min_max(
        self, a: Decimal, b: Decimal, c: Decimal, d: Decimal, operation_type: BinaryType
    ) -> tuple[Decimal, Decimal]:
        """Calculate min and max bounds for arithmetic operations."""
        operations = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }

        op = operations[operation_type]
        results = [op(a, c), op(a, d), op(b, c), op(b, d)]

        return min(results), max(results)

    def _is_numeric_type(self, elementary_type: ElementaryType) -> bool:
        """Check if type is numeric."""
        if not elementary_type:
            return False
        type_name = elementary_type.name
        return (
            type_name.startswith("int")
            or type_name.startswith("uint")
            or type_name.startswith("fixed")
            or type_name.startswith("ufixed")
        )

    def _get_type_bounds_for_elementary_type(
        self, elem_type: ElementaryType
    ) -> tuple[Decimal, Decimal]:
        """Get min/max bounds for elementary type."""
        type_name = elem_type.name

        if type_name.startswith("uint"):
            return self._get_uint_bounds(type_name)
        elif type_name.startswith("int"):
            return self._get_int_bounds(type_name)

        return Decimal("0"), self.UINT256_MAX

    def _get_uint_bounds(self, type_name: str) -> tuple[Decimal, Decimal]:
        """Get bounds for unsigned integer types."""
        if type_name == "uint" or type_name == "uint256":
            return Decimal("0"), self.UINT256_MAX

        try:
            bits = int(type_name[4:])
            max_val = (2**bits) - 1
            return Decimal("0"), Decimal(str(max_val))
        except ValueError:
            return Decimal("0"), self.UINT256_MAX

    def _get_int_bounds(self, type_name: str) -> tuple[Decimal, Decimal]:
        """Get bounds for signed integer types."""
        if type_name == "int" or type_name == "int256":
            return self.INT256_MIN, self.INT256_MAX

        try:
            bits = int(type_name[3:])
            max_val = (2 ** (bits - 1)) - 1
            min_val = -(2 ** (bits - 1))
            return Decimal(str(min_val)), Decimal(str(max_val))
        except ValueError:
            return self.INT256_MIN, self.INT256_MAX

    def _get_promotion_type(self, type1: ElementaryType, type2: ElementaryType) -> ElementaryType:
        """Get the promoted type from two elementary types."""
        size1 = self._get_type_size(type1)
        size2 = self._get_type_size(type2)
        return type1 if size1 >= size2 else type2

    def _get_type_size(self, elem_type: ElementaryType) -> int:
        """Get the bit size of an elementary type."""
        type_name = elem_type.name

        if type_name.startswith("uint"):
            if type_name == "uint" or type_name == "uint256":
                return 256
            try:
                return int(type_name[4:])
            except ValueError:
                return 256
        elif type_name.startswith("int"):
            if type_name == "int" or type_name == "int256":
                return 256
            try:
                return int(type_name[3:])
            except ValueError:
                return 256
        return 256

    def _create_interval_from_type(
        self, var_type: ElementaryType, min_val, max_val
    ) -> IntervalInfo:
        """Create interval from type with min/max bounds."""
        return IntervalInfo(
            upper_bound=Decimal(str(max_val)),
            lower_bound=Decimal(str(min_val)),
            var_type=var_type,
        )
