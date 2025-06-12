from enum import Enum, auto
from typing import List, Optional, Set

from loguru import logger
from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations import (
    Call,
    EventCall,
    HighLevelCall,
    InternalCall,
    LowLevelCall,
    Operation,
    Send,
    Transfer,
)


class ReentrancyInfo:
    def __init__(
        self,
        external_calls: Optional[Set[Call]] = None,
        storage_variables_read: Optional[Set[Variable]] = None,
        storage_variables_written: Optional[Set[Variable]] = None,
        storage_variables_read_before_calls: Optional[Set[Variable]] = None,
        events: Optional[Set[EventCall]] = None,
    ):
        self.external_calls = external_calls or set()
        self.storage_variables_read = storage_variables_read or set()
        self.storage_variables_written = storage_variables_written or set()
        self.storage_variables_read_before_calls = storage_variables_read_before_calls or set()
        self.events = events or set()

    def __eq__(self, other):
        if not isinstance(other, ReentrancyInfo):
            return False

        return (
            self.external_calls == other.external_calls
            and self.storage_variables_read == other.storage_variables_read
            and self.storage_variables_written == other.storage_variables_written
            and self.storage_variables_read_before_calls
            == other.storage_variables_read_before_calls
            and self.events == other.events
        )

    def __hash__(self):

        return hash(
            (
                frozenset(self.external_calls),
                frozenset(self.storage_variables_read),
                frozenset(self.storage_variables_written),
                frozenset(self.storage_variables_read_before_calls),
                frozenset(self.events),
            )
        )

    def __str__(self):

        return (
            f"ReentrancyInfo(\n"
            f"  external_calls: {len(self.external_calls)} items,\n"
            f"  storage_variables_read: {len(self.storage_variables_read)} items,\n"
            f"  storage_variables_written: {len(self.storage_variables_written)} items,\n"
            f"  storage_variables_read_before_calls: {len(self.storage_variables_read_before_calls)} items,\n"
            f"  events: {len(self.events)} items\n"
            f")"
        )


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class ReentrancyDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[ReentrancyInfo] = None):
        self.variant = variant
        self.state = state or ReentrancyInfo()

    @classmethod
    def bottom(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.TOP)

    @classmethod
    def with_state(cls, info: ReentrancyInfo) -> "ReentrancyDomain":
        return cls(DomainVariant.STATE, info)

    def join(self, other: "ReentrancyDomain") -> bool:
        # TOP || BOTTOM
        if self.variant == DomainVariant.TOP or other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            self.state.external_calls.update(other.state.external_calls)
            self.state.storage_variables_read.update(other.state.storage_variables_read)
            self.state.storage_variables_read_before_calls.update(
                other.state.storage_variables_read_before_calls
            )
        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.state = other.state
        else:
            self.variant = DomainVariant.TOP

        return True


class ReentrancyAnalysis(Analysis):
    def __init__(self):
        self._direction = Forward()

    def domain(self) -> Domain:
        return ReentrancyDomain.bottom()

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return ReentrancyDomain.bottom()

    def transfer_function(
        self, node: Node, domain: ReentrancyDomain, operation: Operation, functions: List[Function]
    ):
        self.transfer_function_helper(node, domain, operation, functions)

    def transfer_function_helper(
        self,
        node: Node,
        domain: ReentrancyDomain,
        operation: Operation,
        functions: List[Function],
        private_functions_seen: Optional[Set[Function]] = None,
    ):
        if private_functions_seen is None:
            private_functions_seen = set()

        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = ReentrancyInfo()
            self._analyze_operation_by_type(
                operation, domain, node, functions, private_functions_seen
            )
            return
        elif domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(
                operation, domain, node, functions, private_functions_seen
            )

    def _analyze_operation_by_type(
        self,
        operation: Operation,
        domain: ReentrancyDomain,
        node: Node,
        functions: List[Function],
        private_functions_seen: Set[Function],
    ):
        # storage -- first case in caracal
        self._handle_storage(domain, node)

        # events -- second case in caracal
        if isinstance(operation, EventCall):
            domain.state.events.add(operation)

        # internal calls -- third case in caracal
        if isinstance(operation, InternalCall):
            self._handle_internal_call_operation(operation, domain, private_functions_seen)

        # abi calls -- fourth case in caracal
        if isinstance(operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
            self._handle_abi_call_contract_operation(operation, domain)

    def _handle_storage(self, domain: ReentrancyDomain, node: Node):
        for var in node.state_variables_read:
            if isinstance(var, StateVariable):
                domain.state.storage_variables_read.add(var)
        for var in node.state_variables_written:
            if isinstance(var, StateVariable) and var.is_stored:
                domain.state.storage_variables_written.add(var)

    def _handle_internal_call_operation(
        self,
        operation: InternalCall,
        domain: ReentrancyDomain,
        private_functions_seen: Set[Function],
    ):
        function = operation.function

        if not isinstance(function, Function):
            return

        if function in private_functions_seen:
            return

        private_functions_seen.add(function)

        # process operatins in internal function
        for internal_node in function.all_nodes():
            for internal_operation in internal_node.irs:
                self.transfer_function_helper(
                    internal_node,
                    domain,
                    internal_operation,
                    [function],
                    private_functions_seen,
                )

    def _handle_abi_call_contract_operation(self, operation: Operation, domain: ReentrancyDomain):

        if not isinstance(operation, Call):
            return
        # get vars before call
        storage_reads_before_call = domain.state.storage_variables_read

        # Track this external call
        domain.state.external_calls.add(operation)

        # track var if we read before call
        if storage_reads_before_call:
            domain.state.storage_variables_read_before_calls = storage_reads_before_call
