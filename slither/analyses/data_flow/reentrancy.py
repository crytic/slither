from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union
from collections import defaultdict
import copy

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
    Assignment,
    Index,
)


class ReentrancyInfo:
    def __init__(self):
        self._send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self._safe_send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self._calls: Dict[Node, Set[Node]] = defaultdict(set)
        self._reads: Dict[Variable, Set[Node]] = defaultdict(set)
        self._reads_prior_calls: Dict[Node, Set[Variable]] = defaultdict(set)
        self._events: Dict[EventCall, Set[Node]] = defaultdict(set)
        self._written: Dict[Variable, Set[Node]] = defaultdict(set)

    @property
    def send_eth(self) -> Dict[Node, Set[Node]]:
        """Return the list of calls sending value (unsafe calls only)"""
        return self._send_eth

    @property
    def safe_send_eth(self) -> Dict[Node, Set[Node]]:
        """Return the list of safe ETH transfers (Send/Transfer operations)"""
        return self._safe_send_eth

    @property
    def all_eth_calls(self) -> Dict[Node, Set[Node]]:
        """Return all ETH-sending calls (both safe and unsafe) - for other analyses"""
        result = defaultdict(set)
        for node, calls in self._send_eth.items():
            result[node].update(calls)
        for node, calls in self._safe_send_eth.items():
            result[node].update(calls)
        return result

    @property
    def calls(self) -> Dict[Node, Set[Node]]:
        """Return the list of calls that can callback"""
        return self._calls

    @property
    def reads(self) -> Dict[Variable, Set[Node]]:
        """Return of variables that are read"""
        return self._reads

    @property
    def written(self) -> Dict[Variable, Set[Node]]:
        """Return of variables that are written"""
        return self._written

    @property
    def reads_prior_calls(self) -> Dict[Node, Set[Variable]]:
        """Return the dictionary node -> variables read before any call"""
        return self._reads_prior_calls

    @property
    def events(self) -> Dict[EventCall, Set[Node]]:
        """Return the list of events"""
        return self._events

    def __eq__(self, other):
        if not isinstance(other, ReentrancyInfo):
            return False

        return (
            self._send_eth == other._send_eth
            and self._safe_send_eth == other._safe_send_eth
            and self._calls == other._calls
            and self._reads == other._reads
            and self._reads_prior_calls == other._reads_prior_calls
            and self._events == other._events
            and self._written == other._written
        )

    def __hash__(self):
        return hash(
            (
                frozenset(self._send_eth.items()),
                frozenset(self._safe_send_eth.items()),
                frozenset(self._calls.items()),
                frozenset(self._reads.items()),
                frozenset(self._reads_prior_calls.items()),
                frozenset(self._events.items()),
                frozenset(self._written.items()),
            )
        )

    def __str__(self):
        return (
            f"ReentrancyInfo(\n"
            f"  send_eth: {len(self._send_eth)} items,\n"
            f"  safe_send_eth: {len(self._safe_send_eth)} items,\n"
            f"  calls: {len(self._calls)} items,\n"
            f"  reads: {len(self._reads)} items,\n"
            f"  reads_prior_calls: {len(self._reads_prior_calls)} items,\n"
            f"  events: {len(self._events)} items,\n"
            f"  written: {len(self._written)} items,\n"
            f")"
        )

    def deep_copy(self) -> "ReentrancyInfo":
        """Create a deep copy of this ReentrancyInfo object"""
        new_info = ReentrancyInfo()
        new_info._send_eth = copy.deepcopy(self._send_eth)
        new_info._safe_send_eth = copy.deepcopy(self._safe_send_eth)
        new_info._calls = copy.deepcopy(self._calls)
        new_info._reads = copy.deepcopy(self._reads)
        new_info._reads_prior_calls = copy.deepcopy(self._reads_prior_calls)
        new_info._events = copy.deepcopy(self._events)
        new_info._written = copy.deepcopy(self._written)
        return new_info


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
            self.state = other.state.deep_copy()
            self.state.written.clear()
            self.state.events.clear()

            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            self.state.send_eth.update(other.state.send_eth)
            self.state.calls.update(other.state.calls)
            self.state.reads.update(other.state.reads)
            self.state.reads_prior_calls.update(other.state.reads_prior_calls)
            self.state.safe_send_eth.update(other.state.safe_send_eth)

            return True

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

        # events -- second case in caracal
        if isinstance(operation, EventCall):
            self._handle_event_call_operation(operation, domain)

        # internal calls -- third case in caracal
        elif isinstance(operation, InternalCall):
            self._handle_internal_call_operation(operation, domain, private_functions_seen)

        # abi calls -- fourth case in caracal
        elif isinstance(operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
            self._handle_abi_call_contract_operation(operation, domain, node)

        self._handle_storage(domain, node)

        # print("--------------------------------")
        # print(node.expression)
        # print(domain.state)
        # print("--------------------------------")

    def _handle_storage(self, domain: ReentrancyDomain, node: Node):
        for var in node.state_variables_read:
            if isinstance(var, StateVariable):
                domain.state.reads[var].add(node)
        for var in node.state_variables_written:
            if isinstance(var, StateVariable) and var.is_stored:
                domain.state.written[var].add(node)

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

        for node in function.nodes:
            for internal_operation in node.irs:
                if isinstance(internal_operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
                    continue

                self.transfer_function_helper(
                    node,
                    domain,
                    internal_operation,
                    [function],
                    private_functions_seen,
                )

    def _handle_abi_call_contract_operation(
        self,
        operation: Union[LowLevelCall, HighLevelCall, Send, Transfer],
        domain: ReentrancyDomain,
        node: Node,
    ):

        domain.state.calls[node].add(operation.node)

        # Track variables read before this specific call
        vars_read_before_call = set()
        for var in domain.state.reads.keys():
            vars_read_before_call.add(var)

        domain.state.reads_prior_calls[node] = vars_read_before_call

        # Check if the call sends ETH
        if operation.can_send_eth():
            if operation.call_value is not None and operation.call_value != 0:
                if isinstance(operation, (Send, Transfer)):
                    domain.state.safe_send_eth[node].add(operation.node)
                else:
                    domain.state.send_eth[node].add(operation.node)

    def _handle_event_call_operation(self, operation: EventCall, domain: ReentrancyDomain):
        calls_before_events = set()
        for calls_set in domain.state.calls.values():
            calls_before_events.update(calls_set)
        domain.state.events[operation].add(operation.node)

        if calls_before_events:
            for call_node in calls_before_events:
                domain.state.calls[operation.node].add(call_node)
