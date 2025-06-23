from enum import Enum, auto
import math

from typing import List, Mapping, Optional, Union

from loguru import logger

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class IntervalInfo:
    def __init__(self, upper_bound: float = math.inf, lower_bound: float = -math.inf):
        self.upper_bound = upper_bound
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
        return f"[{self.lower_bound}, {self.upper_bound}]"


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
            self._analyze_operation_by_type(operation, domain, node)

        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

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
            # create interval info for the left var
            left_interval_info = IntervalInfo(
                upper_bound=float(var.value), lower_bound=float(var.value)
            )

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
        self, a: float, b: float, c: float, d: float, operation_type: BinaryType
    ) -> tuple[float, float]:
        operations = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y,
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

            domain.state.info[name] = IntervalInfo(
                upper_bound=float(right_value.value), lower_bound=float(right_value.value)
            )
        elif isinstance(right_value, TemporaryVariable):
            temp_var_name = right_value.name
            # get range for temp var
            temp_var_range = domain.state.info[temp_var_name]

            # update range for left var
            domain.state.info[name] = temp_var_range
