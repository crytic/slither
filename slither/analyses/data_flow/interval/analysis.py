from decimal import Decimal
from typing import List

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
            domain.variant = DomainVariant.STATE
            domain.state = IntervalState({})
            for parameter in node.function.parameters:
                if isinstance(parameter.type, ElementaryType) and self.is_numeric_type(
                    parameter.type
                ):
                    domain.state.info[parameter.canonical_name] = IntervalInfo(
                        upper_bound=Decimal(str(parameter.type.max)),
                        lower_bound=Decimal(str(parameter.type.min)),
                        var_type=parameter.type,
                    )

            self._analyze_operation_by_type(operation, domain, node)

        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

    def is_numeric_type(self, elementary_type: ElementaryType):
        type_name = elementary_type.name
        return (
            type_name.startswith("int")
            or type_name.startswith("uint")
            or type_name.startswith("fixed")
            or type_name.startswith("ufixed")
        )

    def _analyze_operation_by_type(self, operation: Operation, domain: IntervalDomain, node: Node):
        if isinstance(operation, Binary):
            if operation.type in [
                BinaryType.ADDITION,
                BinaryType.SUBTRACTION,
                BinaryType.MULTIPLICATION,
                BinaryType.DIVISION,
            ]:
                self.handle_arithmetic_operation_with_target_type(domain, operation, node)
            elif operation.type in [
                BinaryType.GREATER,
                BinaryType.LESS,
                BinaryType.GREATER_EQUAL,
                BinaryType.LESS_EQUAL,
                BinaryType.EQUAL,
                BinaryType.NOT_EQUAL,
            ]:
                self.handle_comparison_operation(node, domain, operation)

        elif isinstance(operation, Assignment):
            self.handle_assignment(node, domain, operation)

        elif isinstance(operation, SolidityCall):
            self.handle_solidity_call(node, domain, operation)

    def handle_solidity_call(self, node: Node, domain: IntervalDomain, operation: SolidityCall):
        if operation.function.name in ["require(bool)", "assert(bool)"]:
            print(f"🔄 {operation.function.name} called")

    def handle_comparison_operation(self, node: Node, domain: IntervalDomain, operation: Binary):
        if operation.type not in [
            BinaryType.LESS,
            BinaryType.LESS_EQUAL,
            BinaryType.GREATER,
            BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        ]:
            return

        left_var = operation.variable_left
        right_var = operation.variable_right

        left_is_variable = isinstance(left_var, Variable) and not isinstance(left_var, Constant)
        right_is_variable = isinstance(right_var, Variable) and not isinstance(right_var, Constant)
        left_is_constant = isinstance(left_var, Constant)
        right_is_constant = isinstance(right_var, Constant)

        left_interval = self.retrieve_interval_info(left_var, domain, operation)
        right_interval = self.retrieve_interval_info(right_var, domain, operation)

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

    def _flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
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
        var_name = self.get_variable_name(variable)

        if var_name in domain.state.info:
            current_interval = domain.state.info[var_name]
        else:
            var_type = getattr(variable, "type", None)
            current_interval = IntervalInfo(var_type=var_type)
            if var_type and isinstance(var_type, ElementaryType) and self.is_numeric_type(var_type):
                current_interval.lower_bound = Decimal(str(var_type.min))
                current_interval.upper_bound = Decimal(str(var_type.max))

        constraint_value = constraint_interval.lower_bound
        new_interval = current_interval.deep_copy()

        if op_type == BinaryType.GREATER_EQUAL:
            new_interval.lower_bound = max(new_interval.lower_bound, constraint_value)

        elif op_type == BinaryType.GREATER:
            new_interval.lower_bound = max(
                new_interval.lower_bound, constraint_value + Decimal("1")
            )

        elif op_type == BinaryType.LESS_EQUAL:
            new_interval.upper_bound = min(new_interval.upper_bound, constraint_value)

        elif op_type == BinaryType.LESS:
            new_interval.upper_bound = min(
                new_interval.upper_bound, constraint_value - Decimal("1")
            )

        elif op_type == BinaryType.EQUAL:
            if (
                constraint_value >= new_interval.lower_bound
                and constraint_value <= new_interval.upper_bound
            ):
                new_interval.lower_bound = constraint_value
                new_interval.upper_bound = constraint_value
            else:
                new_interval.lower_bound = Decimal("1")
                new_interval.upper_bound = Decimal("0")

        elif op_type == BinaryType.NOT_EQUAL:
            if constraint_value == new_interval.lower_bound == new_interval.upper_bound:
                new_interval.lower_bound = Decimal("1")
                new_interval.upper_bound = Decimal("0")
            elif constraint_value == new_interval.lower_bound:
                new_interval.lower_bound = constraint_value + Decimal("1")
            elif constraint_value == new_interval.upper_bound:
                new_interval.upper_bound = constraint_value - Decimal("1")

        if new_interval.lower_bound > new_interval.upper_bound:
            domain.variant = DomainVariant.BOTTOM
            return

        domain.state.info[var_name] = new_interval

    def _handle_variable_to_variable_comparison(
        self,
        left_var: Variable,
        right_var: Variable,
        op_type: BinaryType,
        domain: IntervalDomain,
    ):
        left_name = self.get_variable_name(left_var)
        right_name = self.get_variable_name(right_var)

        left_interval = domain.state.info.get(left_name)
        right_interval = domain.state.info.get(right_name)

        if not left_interval or not right_interval:
            return

        new_left = left_interval.deep_copy()
        new_right = right_interval.deep_copy()

        if op_type == BinaryType.EQUAL:
            common_lower = max(new_left.lower_bound, new_right.lower_bound)
            common_upper = min(new_left.upper_bound, new_right.upper_bound)

            if common_lower <= common_upper:
                new_left.lower_bound = new_left.upper_bound = common_lower
                new_right.lower_bound = new_right.upper_bound = common_lower

                if common_lower == common_upper:
                    new_left.lower_bound = new_left.upper_bound = common_lower
                    new_right.lower_bound = new_right.upper_bound = common_lower
                else:
                    new_left.lower_bound = new_right.lower_bound = common_lower
                    new_left.upper_bound = new_right.upper_bound = common_upper
            else:
                domain.variant = DomainVariant.BOTTOM
                return

        elif op_type == BinaryType.NOT_EQUAL:
            if (
                new_left.lower_bound == new_left.upper_bound
                and new_right.lower_bound == new_right.upper_bound
                and new_left.lower_bound == new_right.lower_bound
            ):
                domain.variant = DomainVariant.BOTTOM
                return

        elif op_type == BinaryType.LESS:
            if new_right.lower_bound != Decimal("-Infinity"):
                new_left.upper_bound = min(
                    new_left.upper_bound, new_right.upper_bound - Decimal("1")
                )
            if new_left.upper_bound != Decimal("Infinity"):
                new_right.lower_bound = max(
                    new_right.lower_bound, new_left.lower_bound + Decimal("1")
                )

        elif op_type == BinaryType.LESS_EQUAL:
            if new_right.lower_bound != Decimal("-Infinity"):
                new_left.upper_bound = min(new_left.upper_bound, new_right.upper_bound)
            if new_left.upper_bound != Decimal("Infinity"):
                new_right.lower_bound = max(new_right.lower_bound, new_left.lower_bound)

        elif op_type == BinaryType.GREATER:
            if new_left.lower_bound != Decimal("-Infinity"):
                new_right.upper_bound = min(
                    new_right.upper_bound, new_left.upper_bound - Decimal("1")
                )
            if new_right.upper_bound != Decimal("Infinity"):
                new_left.lower_bound = max(
                    new_left.lower_bound, new_right.lower_bound + Decimal("1")
                )

        elif op_type == BinaryType.GREATER_EQUAL:
            if new_left.lower_bound != Decimal("-Infinity"):
                new_right.upper_bound = min(new_right.upper_bound, new_left.upper_bound)
            if new_right.upper_bound != Decimal("Infinity"):
                new_left.lower_bound = max(new_left.lower_bound, new_right.lower_bound)

        if (
            new_left.lower_bound > new_left.upper_bound
            or new_right.lower_bound > new_right.upper_bound
        ):
            domain.variant = DomainVariant.BOTTOM
            return

        domain.state.info[left_name] = new_left
        domain.state.info[right_name] = new_right

    def handle_arithmetic_operation_with_target_type(
        self, domain: IntervalDomain, operation: Binary, node: Node
    ):
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
            target_type = getattr(operation.lvalue, "type", None)

            # For temporary variables, infer the appropriate type from operands
            if target_type is None and isinstance(operation.lvalue, TemporaryVariable):
                left_type = (
                    getattr(operation.variable_left, "type", None)
                    if hasattr(operation.variable_left, "type")
                    else None
                )
                right_type = (
                    getattr(operation.variable_right, "type", None)
                    if hasattr(operation.variable_right, "type")
                    else None
                )

                if left_type and right_type:
                    target_type = self._get_promotion_type(left_type, right_type)
                elif left_type:
                    target_type = left_type
                elif right_type:
                    target_type = right_type

            # Create interval with the full computed bounds and proper type
            new_interval = IntervalInfo(
                upper_bound=upper_bound, lower_bound=lower_bound, var_type=target_type
            )

            # Store the interval with computed bounds - test.py will check for overflow
            domain.state.info[variable_name] = new_interval
        else:
            logger.error(f"lvalue is not a variable for operation: {operation}")
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):
        if operation.lvalue is None:
            return

        written_variable = operation.lvalue
        right_value = operation.rvalue
        writing_variable_name = self.get_variable_name(written_variable)

        if isinstance(right_value, Constant):
            value = Decimal(str(right_value.value))
            target_type = getattr(written_variable, "type", None)
            domain.state.info[writing_variable_name] = IntervalInfo(
                upper_bound=value, lower_bound=value, var_type=target_type
            )

        elif isinstance(right_value, TemporaryVariable):
            temp_var_name = right_value.name
            if temp_var_name in domain.state.info:
                temp_var_range = domain.state.info[temp_var_name]
                target_type = getattr(written_variable, "type", None)

                new_interval = temp_var_range.deep_copy()
                new_interval.var_type = target_type

                if (
                    target_type
                    and isinstance(target_type, ElementaryType)
                    and self.is_numeric_type(target_type)
                ):
                    target_min, target_max = self._get_type_bounds_for_elementary_type(target_type)

                    new_interval.lower_bound = max(new_interval.lower_bound, target_min)
                    new_interval.upper_bound = min(new_interval.upper_bound, target_max)

                domain.state.info[writing_variable_name] = new_interval

        elif isinstance(right_value, Variable):
            right_var_name = self.get_variable_name(right_value)
            if right_var_name in domain.state.info:
                right_interval = domain.state.info[right_var_name]
                target_type = getattr(written_variable, "type", None)

                new_interval = right_interval.deep_copy()
                new_interval.var_type = target_type

                if (
                    target_type
                    and isinstance(target_type, ElementaryType)
                    and self.is_numeric_type(target_type)
                ):
                    target_min, target_max = self._get_type_bounds_for_elementary_type(target_type)

                    new_interval.lower_bound = max(new_interval.lower_bound, target_min)
                    new_interval.upper_bound = min(new_interval.upper_bound, target_max)

                domain.state.info[writing_variable_name] = new_interval

    def retrieve_interval_info(
        self, var: RVALUE | Function, domain: IntervalDomain, operation: Binary
    ) -> IntervalInfo:
        if isinstance(var, Constant):
            value = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            left_var_name = self.get_variable_name(var)
            if left_var_name in domain.state.info:
                return domain.state.info[left_var_name]
            else:
                return IntervalInfo(Decimal(0), Decimal(0), var_type=None)

        return IntervalInfo(var_type=None)

    def get_variable_name(self, variable: Variable) -> str:
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
        operations = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }

        op = operations[operation_type]

        r1 = op(a, c)
        r2 = op(a, d)
        r3 = op(b, c)
        r4 = op(b, d)

        results = [r1, r2, r3, r4]

        return min(results), max(results)

    def _get_type_bounds_for_elementary_type(
        self, elem_type: ElementaryType
    ) -> tuple[Decimal, Decimal]:
        type_name = elem_type.name

        if type_name.startswith("uint"):
            if type_name == "uint" or type_name == "uint256":
                return Decimal("0"), Decimal(
                    "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                )
            else:
                try:
                    bits = int(type_name[4:])
                    max_val = (2**bits) - 1
                    return Decimal("0"), Decimal(str(max_val))
                except ValueError:
                    return Decimal("0"), Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    )

        elif type_name.startswith("int"):
            if type_name == "int" or type_name == "int256":
                return Decimal(
                    "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
                ), Decimal(
                    "57896044618658097711785492504343953926634992332820282019728792003956564819967"
                )
            else:
                try:
                    bits = int(type_name[3:])
                    max_val = (2 ** (bits - 1)) - 1
                    min_val = -(2 ** (bits - 1))
                    return Decimal(str(min_val)), Decimal(str(max_val))
                except ValueError:
                    return Decimal(
                        "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
                    ), Decimal(
                        "57896044618658097711785492504343953926634992332820282019728792003956564819967"
                    )

        return Decimal("0"), Decimal(
            "115792089237316195423570985008687907853269984665640564039457584007913129639935"
        )

    def _get_promotion_type(self, type1: ElementaryType, type2: ElementaryType) -> ElementaryType:
        def get_type_size(elem_type: ElementaryType) -> int:
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

        size1 = get_type_size(type1)
        size2 = get_type_size(type2)

        return type1 if size1 >= size2 else type2
