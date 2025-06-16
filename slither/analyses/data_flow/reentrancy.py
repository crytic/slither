from enum import Enum, auto
from typing import Dict, List, Optional, Set
from collections import defaultdict

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
        storage_variables_written_before_calls: Optional[Set[Variable]] = None,
        events: Optional[Set[EventCall]] = None,
        calls_emitted_after_events: Optional[Set[Call]] = None,
    ):
        self.external_calls = external_calls or set()
        self.storage_variables_read = storage_variables_read or set()
        self.storage_variables_written = storage_variables_written or set()
        self.storage_variables_read_before_calls = storage_variables_read_before_calls or set()
        self.storage_variables_written_before_calls = (
            storage_variables_written_before_calls or set()
        )
        self.events = events or set()
        self.calls_emitted_after_events = calls_emitted_after_events or set()
        self.events_with_later_calls = defaultdict(set)
        self.send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self.internal_calls: Dict[Node, Set[Node]] = defaultdict(set)
        self.internal_variables_written: Dict[Node, Set[Variable]] = defaultdict(
            set
        )  # Track variables written in internal calls

    def __eq__(self, other):
        if not isinstance(other, ReentrancyInfo):
            return False

        return (
            self.external_calls == other.external_calls
            and self.storage_variables_read == other.storage_variables_read
            and self.storage_variables_written == other.storage_variables_written
            and self.storage_variables_read_before_calls
            == other.storage_variables_read_before_calls
            and self.storage_variables_written_before_calls
            == other.storage_variables_written_before_calls
            and self.events == other.events
        )

    def __hash__(self):
        return hash(
            (
                frozenset(self.external_calls),
                frozenset(self.storage_variables_read),
                frozenset(self.storage_variables_written),
                frozenset(self.storage_variables_read_before_calls),
                frozenset(self.storage_variables_written_before_calls),
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
            f"  storage_variables_written_before_calls: {len(self.storage_variables_written_before_calls)} items,\n"
            f"  events: {len(self.events)} item,\n"
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
        self.events = set()
        self.events_with_later_calls = defaultdict(set)

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
            self.state.storage_variables_written_before_calls.update(
                other.state.storage_variables_written_before_calls
            )
            self.state.send_eth.update(other.state.send_eth)

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
            # domain.state.events.add(operation)
            self._handle_event_call_operation(operation, domain)

        # internal calls -- third case in caracal
        if isinstance(operation, InternalCall):
            self._handle_internal_call_operation(operation, domain, private_functions_seen)

        # abi calls -- fourth case in caracal
        if isinstance(operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
            self._handle_abi_call_contract_operation(operation, domain, node)

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

        if not isinstance(function, Function) or function in private_functions_seen:
            return

        private_functions_seen.add(function)
        current_node = operation.node

        # Process operations in internal function
        for node in function.nodes:
            # Track all variables written in this internal call
            for var in node.state_variables_written:
                if isinstance(var, StateVariable):
                    domain.state.internal_variables_written[current_node].add(var)
                    domain.state.storage_variables_written.add(var)

            for var in node.local_variables_written:
                domain.state.internal_variables_written[current_node].add(var)

            for internal_operation in node.irs:
                # Track external calls found in internal functions
                if isinstance(internal_operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
                    domain.state.internal_calls[internal_operation.node].add(current_node)
                    domain.state.external_calls.add(internal_operation)

                self.transfer_function_helper(
                    node,
                    domain,
                    internal_operation,
                    [function],
                    private_functions_seen,
                )

    def _handle_abi_call_contract_operation(
        self, operation: Operation, domain: ReentrancyDomain, node: Node
    ):
        # Add the call to external calls
        if isinstance(operation, Call):
            domain.state.external_calls.add(operation)

        # Track variables written before this call
        for var in domain.state.storage_variables_written:
            if var not in domain.state.storage_variables_written_before_calls:
                domain.state.storage_variables_written_before_calls.add(var)

        # Track variables read before this call
        for var in domain.state.storage_variables_read:
            if var not in domain.state.storage_variables_read_before_calls:
                domain.state.storage_variables_read_before_calls.add(var)

        # Check if the call sends ETH
        if isinstance(operation, (Send, Transfer, HighLevelCall, LowLevelCall)):
            if operation.call_value is not None and operation.call_value != 0:
                domain.state.send_eth[node].add(node)

    def _handle_event_call_operation(self, operation: EventCall, domain: ReentrancyDomain):
        calls_before_events = domain.state.external_calls
        domain.state.events.add(operation)

        if calls_before_events:
            domain.state.calls_emitted_after_events.update(calls_before_events)
