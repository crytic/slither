from enum import Enum, auto
import math
from decimal import Decimal, getcontext
from typing import List, Mapping, Optional, Union

from loguru import logger

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable

# Set high precision for Decimal operations
getcontext().prec = 100


class IntervalInfo:
    def __init__(
        self,
        upper_bound: Union[int, Decimal] = Decimal("Infinity"),
        lower_bound: Union[int, Decimal] = Decimal("-Infinity"),
        var_type: Optional[ElementaryType] = None,
    ):
        # Convert to Decimal to maintain precision
        if isinstance(upper_bound, (int, float)):
            self.upper_bound = Decimal(str(upper_bound))
        else:
            self.upper_bound = upper_bound

        if isinstance(lower_bound, (int, float)):
            self.lower_bound = Decimal(str(lower_bound))
        else:
            self.lower_bound = lower_bound
        self.var_type = var_type

    def __eq__(self, other):
        return self.upper_bound == other.upper_bound and self.lower_bound == other.lower_bound

    def __hash__(self):
        return hash((self.upper_bound, self.lower_bound))

    def deep_copy(self) -> "IntervalInfo":
        return IntervalInfo(self.upper_bound, self.lower_bound, self.var_type)

    def join(self, other: "IntervalInfo") -> None:
        self.lower_bound = min(self.lower_bound, other.lower_bound)
        self.upper_bound = max(self.upper_bound, other.upper_bound)

    def get_type_bounds(self) -> tuple[Decimal, Decimal]:
        """Get the theoretical min/max bounds for this variable's type"""
        if self.var_type and hasattr(self.var_type, "max") and hasattr(self.var_type, "min"):
            return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
        else:
            # Default to uint256 bounds for temporary variables or unknown types
            return Decimal("0"), Decimal(
                "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            )

    def has_overflow(self) -> bool:
        """Check if current bounds exceed the variable's type bounds"""
        type_min, type_max = self.get_type_bounds()
        return self.upper_bound > type_max

    def has_underflow(self) -> bool:
        """Check if current bounds go below the variable's type bounds"""
        type_min, type_max = self.get_type_bounds()
        return self.lower_bound < type_min

    def __str__(self):
        lower_str = (
            str(int(self.lower_bound))
            if self.lower_bound == int(self.lower_bound)
            else str(self.lower_bound)
        )
        upper_str = (
            str(int(self.upper_bound))
            if self.upper_bound == int(self.upper_bound)
            else str(self.upper_bound)
        )
        return f"[{lower_str}, {upper_str}]"


class IntervalState:
    def __init__(self, info: Mapping[str, IntervalInfo]):
        self.info = dict(info)  # Convert to dict to make it mutable

    def __eq__(self, other):
        if not isinstance(other, IntervalState):
            return False
        return self.info == other.info

    def deep_copy(self) -> "IntervalState":
        copied_info = {key: value.deep_copy() for key, value in self.info.items()}
        return IntervalState(copied_info)


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class IntervalDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[IntervalState] = None):
        self.variant = variant

        if state is None:
            self.state = IntervalState({})
        else:
            self.state = state

    @classmethod
    def bottom(cls) -> "IntervalDomain":
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "IntervalDomain":
        return cls(DomainVariant.TOP)

    @classmethod
    def with_state(cls, info: Mapping[str, IntervalInfo]) -> "IntervalDomain":
        return cls(DomainVariant.STATE, IntervalState(info))

    def join(self, other: "IntervalDomain") -> bool:
        if self.variant == DomainVariant.TOP or other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            changed = False
            for variable_name, variable_range in other.state.info.items():
                if variable_name in self.state.info:
                    old_range = self.state.info[variable_name].deep_copy()
                    self.state.info[variable_name].join(variable_range)
                    if self.state.info[variable_name] != old_range:
                        changed = True
                else:
                    self.state.info[variable_name] = variable_range.deep_copy()
                    changed = True

            return changed

        else:
            self.variant = DomainVariant.TOP

        return True


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
                    # Use Decimal for precise bounds
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

    def _analyze_operation_by_type(
        self,
        operation: Operation,
        domain: IntervalDomain,
        node: Node,
    ):
        print(f"Operation: {operation}, type: {type(operation)}")
        if isinstance(operation, Binary):
            self.handle_binary(node, domain, operation)
        if isinstance(operation, Assignment):
            self.handle_assignment(node, domain, operation)
        if isinstance(operation, SolidityCall):
            self.handle_solidity_call(node, domain, operation)

    def handle_solidity_call(self, node: Node, domain: IntervalDomain, operation: SolidityCall):
        print(f"Solidity call: {operation}")

    def handle_binary(self, node: Node, domain: IntervalDomain, operation: Binary):
        if operation.type in [
            BinaryType.ADDITION,
            BinaryType.SUBTRACTION,
            BinaryType.MULTIPLICATION,
            BinaryType.DIVISION,
        ]:
            self.handle_arithmetic_operation(domain, operation)
        elif operation.type in [
            BinaryType.GREATER,
            BinaryType.LESS,
            BinaryType.GREATER_EQUAL,
            BinaryType.LESS_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        ]:
            self.handle_comparison_operation(node, domain, operation)
        else:
            print(f"⚠️ Unhandled binary operation: {operation.type}")

    def handle_arithmetic_operation(self, domain: IntervalDomain, operation: Binary):
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
            domain.state.info[variable_name] = IntervalInfo(
                upper_bound=upper_bound, lower_bound=lower_bound, var_type=None
            )
        else:
            logger.error(f"lvalue is not a variable for operation: {operation}")
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

    def handle_comparison_operation(self, node: Node, domain: IntervalDomain, operation: Binary):
        print(f"Comparison operation: {operation}")

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
                # Handle undefined variables - return safe default
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

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):

        if operation.lvalue is None:
            logger.warning(f"left_var is None for operation: {operation}")
            return

        written_variable = operation.lvalue
        right_value = operation.rvalue

        writing_variable_name = self.get_variable_name(written_variable)

        if isinstance(right_value, Constant):
            # Use Decimal for precise constant values
            value = Decimal(str(right_value.value))
            domain.state.info[writing_variable_name] = IntervalInfo(
                upper_bound=value, lower_bound=value, var_type=None
            )
        elif isinstance(right_value, TemporaryVariable):
            temp_var_name = right_value.name
            # get range for temp var
            temp_var_range = domain.state.info[temp_var_name]

            # update range for left var
            domain.state.info[writing_variable_name] = temp_var_range.deep_copy()
