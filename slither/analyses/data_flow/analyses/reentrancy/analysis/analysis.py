from typing import List, Optional, Set, Union
from slither.analyses.data_flow.analyses.reentrancy.analysis.domain import (
    DomainVariant,
    ReentrancyDomain,
)
from slither.analyses.data_flow.analyses.reentrancy.core.state import State
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.event_call import EventCall
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.low_level_call import LowLevelCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.send import Send
from slither.slithir.operations.transfer import Transfer


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
            domain.state = State()
            self._analyze_operation_by_type(
                operation, domain, node, functions, private_functions_seen
            )
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
        if isinstance(operation, EventCall):
            self._handle_event_call_operation(operation, domain)
        elif isinstance(operation, InternalCall):
            self._handle_internal_call_operation(operation, domain, private_functions_seen)
        elif isinstance(operation, (HighLevelCall, LowLevelCall, Transfer, Send)):
            self._handle_abi_call_contract_operation(operation, domain, node)

        self._handle_storage(domain, node)
        self._update_writes_after_calls(domain, node)

    def _handle_storage(self, domain: ReentrancyDomain, node: Node):
        for var in node.state_variables_read:
            if isinstance(var, StateVariable):
                domain.state.reads[var.canonical_name].add(node)
        for var in node.state_variables_written:
            if isinstance(var, StateVariable) and var.is_stored:
                domain.state.written[var.canonical_name].add(node)

    def _update_writes_after_calls(self, domain: ReentrancyDomain, node: Node):
        # Track state writes after external calls
        if node in domain.state.calls:
            for var_name, write_nodes in domain.state.written.items():
                if write_nodes:
                    domain.state.writes_after_calls[var_name].update(write_nodes)

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
        # Mark cross-function reentrancy
        for var_name in domain.state.written.keys():
            domain.state.cross_function[var_name].add(function)

    def _handle_abi_call_contract_operation(
        self,
        operation: Union[LowLevelCall, HighLevelCall, Send, Transfer],
        domain: ReentrancyDomain,
        node: Node,
    ):
        domain.state.calls[node].add(operation.node)
        vars_read_before_call = set(domain.state.reads.keys())
        domain.state.reads_prior_calls[node] = vars_read_before_call

        if operation.can_send_eth:
            if isinstance(operation, (Send, Transfer)):
                domain.state.safe_send_eth[node].add(operation.node)
            else:
                domain.state.send_eth[node].add(operation.node)

    def _handle_event_call_operation(self, operation: EventCall, domain: ReentrancyDomain):
        calls_before_events = set()
        for calls_set in domain.state.calls.values():
            calls_before_events.update(calls_set)
        domain.state.events[operation].add(operation.node)
        for call_node in calls_before_events:
            domain.state.calls[operation.node].add(call_node)
