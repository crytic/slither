import copy
from collections import defaultdict
from typing import Dict, Set

from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.event_call import EventCall


class State:
    def __init__(self):
        self._send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self._safe_send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self._calls: Dict[Node, Set[Node]] = defaultdict(set)
        self._reads: Dict[str, Set[Node]] = defaultdict(set)
        self._reads_prior_calls: Dict[Node, Set[str]] = defaultdict(set)
        self._events: Dict[EventCall, Set[Node]] = defaultdict(set)
        self._written: Dict[str, Set[Node]] = defaultdict(set)
        self.writes_after_calls: Dict[str, Set[Node]] = defaultdict(set)
        self.cross_function: Dict[StateVariable, Set[Function]] = defaultdict(set)

    # -------------------- Add methods --------------------
    def add_call(self, node: Node, call_node: Node):
        self._calls[node].add(call_node)

    def add_send_eth(self, node: Node, call_node: Node):
        self._send_eth[node].add(call_node)

    def add_safe_send_eth(self, node: Node, call_node: Node):
        self._safe_send_eth[node].add(call_node)

    def add_written(self, var: StateVariable, node: Node):
        self._written[var.canonical_name].add(node)

    def add_read(self, var: StateVariable, node: Node):
        self._reads[var.canonical_name].add(node)

    def add_reads_prior_calls(self, node: Node, var_name: str):
        self._reads_prior_calls[node].add(var_name)

    def add_write_after_call(self, var_name: str, node: Node):
        self.writes_after_calls[var_name].add(node)

    def add_cross_function(self, var: StateVariable, function: Function):
        self.cross_function[var].add(function)

    def add_event(self, event: EventCall, node: Node):
        self._events[event].add(node)

    # -------------------- Properties --------------------
    @property
    def send_eth(self) -> Dict[Node, Set[Node]]:
        return self._send_eth

    @property
    def safe_send_eth(self) -> Dict[Node, Set[Node]]:
        return self._safe_send_eth

    @property
    def all_eth_calls(self) -> Dict[Node, Set[Node]]:
        result = defaultdict(set)
        for node, calls in self._send_eth.items():
            result[node].update(calls)
        for node, calls in self._safe_send_eth.items():
            result[node].update(calls)
        return result

    @property
    def calls(self) -> Dict[Node, Set[Node]]:
        return self._calls

    @property
    def reads(self) -> Dict[str, Set[Node]]:
        return self._reads

    @property
    def written(self) -> Dict[str, Set[Node]]:
        return self._written

    @property
    def reads_prior_calls(self) -> Dict[Node, Set[str]]:
        return self._reads_prior_calls

    @property
    def events(self) -> Dict[EventCall, Set[Node]]:
        return self._events

    # -------------------- Utilities --------------------
    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return (
            self._send_eth == other._send_eth
            and self._safe_send_eth == other._safe_send_eth
            and self._calls == other._calls
            and self._reads == other._reads
            and self._reads_prior_calls == other._reads_prior_calls
            and self._events == other._events
            and self._written == other._written
            and self.writes_after_calls == other.writes_after_calls
            and self.cross_function == other.cross_function
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
                frozenset((k, frozenset(v)) for k, v in self.writes_after_calls.items()),
                frozenset((k, frozenset(v)) for k, v in self.cross_function.items()),
            )
        )

    def __str__(self):
        return (
            f"State(\n"
            f"  send_eth: {len(self._send_eth)} items,\n"
            f"  safe_send_eth: {len(self._safe_send_eth)} items,\n"
            f"  calls: {len(self._calls)} items,\n"
            f"  reads: {len(self._reads)} items,\n"
            f"  reads_prior_calls: {len(self._reads_prior_calls)} items,\n"
            f"  events: {len(self._events)} items,\n"
            f"  written: {len(self._written)} items,\n"
            f"  writes_after_calls: {len(self.writes_after_calls)} items,\n"
            f"  cross_function: {len(self.cross_function)} items,\n"
            f")"
        )

    def deep_copy(self) -> "State":
        new_state = State()
        new_state._send_eth = copy.deepcopy(self._send_eth)
        new_state._safe_send_eth = copy.deepcopy(self._safe_send_eth)
        new_state._calls = copy.deepcopy(self._calls)
        new_state._reads = copy.deepcopy(self._reads)
        new_state._reads_prior_calls = copy.deepcopy(self._reads_prior_calls)
        new_state._events = copy.deepcopy(self._events)
        new_state._written = copy.deepcopy(self._written)
        new_state.writes_after_calls = copy.deepcopy(self.writes_after_calls)
        new_state.cross_function = copy.deepcopy(self.cross_function)
        return new_state

