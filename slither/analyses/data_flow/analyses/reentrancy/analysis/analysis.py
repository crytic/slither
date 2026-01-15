from typing import Optional, Set, Union

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

    def transfer_function(self, node: Node, domain: ReentrancyDomain, operation: Operation):
        self.transfer_function_helper(node, domain, operation, private_functions_seen=set())

    def transfer_function_helper(
        self,
        node: Node,
        domain: ReentrancyDomain,
        operation: Operation,
        private_functions_seen: Optional[Set[Function]] = None,
    ):
        if private_functions_seen is None:
            private_functions_seen = set()

        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = State()

        self._analyze_operation_by_type(operation, domain, node, private_functions_seen)

    def _analyze_operation_by_type(
        self,
        operation: Operation,
        domain: ReentrancyDomain,
        node: Node,
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
        # Track state reads
        for var in node.state_variables_read:
            if isinstance(var, StateVariable) and var.is_stored:
                domain.state.add_read(var, node)
        # Track state writes
        for var in node.state_variables_written:
            if isinstance(var, StateVariable) and var.is_stored:
                domain.state.add_written(var, node)

    def _update_writes_after_calls(self, domain: ReentrancyDomain, node: Node):
        # Writes after any external call
        if node in domain.state.calls:
            for var_name, write_nodes in domain.state.written.items():
                for wn in write_nodes:
                    domain.state.add_write_after_call(var_name, wn)
        # Writes after ETH-sending calls
        if node in domain.state.send_eth:
            for var_name, write_nodes in domain.state.written.items():
                for wn in write_nodes:
                    domain.state.add_write_after_call(var_name, wn)

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
                    private_functions_seen,
                )
        # Mark cross-function reentrancy for written variables
        for var_name in domain.state.written.keys():
            domain.state.add_cross_function(var_name, function)

    def _handle_abi_call_contract_operation(
        self,
        operation: Union[LowLevelCall, HighLevelCall, Send, Transfer],
        domain: ReentrancyDomain,
        node: Node,
    ):
        # Track all external calls - avoid duplicates
        if operation.node not in domain.state.calls.get(node, set()):
            domain.state.add_call(node, operation.node)

        # Track variables read prior to this call
        for var_name in domain.state.reads.keys():
            domain.state.add_reads_prior_calls(node, var_name)

        # Track external calls that send ETH - avoid duplicates
        if operation.can_send_eth:
            if operation.node not in domain.state.send_eth.get(node, set()):
                domain.state.add_send_eth(node, operation.node)

    def _handle_event_call_operation(self, operation: EventCall, domain: ReentrancyDomain):
        # Track events and propagate previous external calls
        # Only propagate calls that haven't already been propagated to this event node
        existing_calls = domain.state.calls.get(operation.node, set())

        # Collect all calls to add before modifying the dictionary
        calls_to_add = []
        for calls_set in domain.state.calls.values():
            for call_node in calls_set:
                if call_node not in existing_calls:
                    calls_to_add.append(call_node)

        # Add all collected calls
        for call_node in calls_to_add:
            domain.state.add_call(operation.node, call_node)

        domain.state.add_event(operation, operation.node)
