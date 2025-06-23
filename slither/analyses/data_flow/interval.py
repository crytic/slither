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

    def __eq__(self, other):
        return self.upper_bound == other.upper_bound and self.lower_bound == other.lower_bound

    def __hash__(self):
        return hash((self.upper_bound, self.lower_bound))

    def deep_copy(self) -> "IntervalInfo":
        return IntervalInfo(self.upper_bound, self.lower_bound)

    def join(self, other: "IntervalInfo") -> None:
        self.lower_bound = min(self.lower_bound, other.lower_bound)
        self.upper_bound = max(self.upper_bound, other.upper_bound)

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
        # Always ensure state is not None
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
        # Return an empty STATE domain instead of BOTTOM for the initial state
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
        if isinstance(operation, Binary):
            self.handle_binary(node, domain, operation)
        if isinstance(operation, Assignment):
            self.handle_assignment(node, domain, operation)

    def handle_binary(self, node: Node, domain: IntervalDomain, operation: Binary):
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
            if isinstance(operation.lvalue, Union[StateVariable, LocalVariable]):
                domain.state.info[operation.lvalue.canonical_name] = IntervalInfo(
                    upper_bound=upper_bound, lower_bound=lower_bound
                )
            else:
                name = operation.lvalue.name
                if name is not None:
                    domain.state.info[name] = IntervalInfo(
                        upper_bound=upper_bound, lower_bound=lower_bound
                    )

    def retrieve_interval_info(
        self, var: RVALUE | Function, domain: IntervalDomain, operation: Binary
    ) -> IntervalInfo:

        if isinstance(var, Constant):
            # Use Decimal for precise constant values
            value = Decimal(str(var.value))
            left_interval_info = IntervalInfo(upper_bound=value, lower_bound=value)

        elif isinstance(var, Variable):

            if isinstance(var, (StateVariable, LocalVariable)):
                left_var_name = var.canonical_name
            else:
                left_var_name = var.name

            if left_var_name is None:
                logger.error(f"left_var_name is None for operation: {operation}")
                return IntervalInfo()

            left_interval_info = domain.state.info[left_var_name]

        return left_interval_info

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

        if isinstance(written_variable, (StateVariable, LocalVariable)):
            name = written_variable.canonical_name
        else:
            name = written_variable.name

        if name is None:
            logger.warning(f"name is None for operation: {operation}")
            return

        if isinstance(right_value, Constant):
            # Use Decimal for precise constant values
            value = Decimal(str(right_value.value))
            domain.state.info[name] = IntervalInfo(upper_bound=value, lower_bound=value)
        elif isinstance(right_value, TemporaryVariable):
            temp_var_name = right_value.name
            # get range for temp var
            temp_var_range = domain.state.info[temp_var_name]

            # update range for left var
            domain.state.info[name] = temp_var_range
