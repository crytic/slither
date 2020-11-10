""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""
from collections import defaultdict
from typing import Set, Dict, Union

from slither.core.cfg.node import NodeType, Node
from slither.core.declarations import Function
from slither.core.expressions import UnaryOperation, UnaryOperationType
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import Call, EventCall


def union_dict(d1, d2):
    d3 = {k: d1.get(k, set()) | d2.get(k, set()) for k in set(list(d1.keys()) + list(d2.keys()))}
    return defaultdict(set, d3)


def dict_are_equal(d1, d2):
    if set(list(d1.keys())) != set(list(d2.keys())):
        return False
    return all(set(d1[k]) == set(d2[k]) for k in d1.keys())


def is_subset(
    new_info: Dict[Union[Variable, Node], Set[Node]],
    old_info: Dict[Union[Variable, Node], Set[Node]],
):
    for k in new_info.keys():
        if k not in old_info:
            return False
        if not new_info[k].issubset(old_info[k]):
            return False
    return True


def to_hashable(d: Dict[Node, Set[Node]]):
    list_tuple = list(
        tuple((k, tuple(sorted(values, key=lambda x: x.node_id)))) for k, values in d.items()
    )
    return tuple(sorted(list_tuple, key=lambda x: x[0].node_id))


class AbstractState:
    def __init__(self):
        # send_eth returns the list of calls sending value
        # calls returns the list of calls that can callback
        # read returns the variable read
        # read_prior_calls returns the variable read prior a call
        self._send_eth: Dict[Node, Set[Node]] = defaultdict(set)
        self._calls: Dict[Node, Set[Node]] = defaultdict(set)
        self._reads: Dict[Variable, Set[Node]] = defaultdict(set)
        self._reads_prior_calls: Dict[Node, Set[Variable]] = defaultdict(set)
        self._events: Dict[EventCall, Set[Node]] = defaultdict(set)
        self._written: Dict[Variable, Set[Node]] = defaultdict(set)

    @property
    def send_eth(self) -> Dict[Node, Set[Node]]:
        """
        Return the list of calls sending value
        :return:
        """
        return self._send_eth

    @property
    def calls(self) -> Dict[Node, Set[Node]]:
        """
        Return the list of calls that can callback
        :return:
        """
        return self._calls

    @property
    def reads(self) -> Dict[Variable, Set[Node]]:
        """
        Return of variables that are read
        :return:
        """
        return self._reads

    @property
    def written(self) -> Dict[Variable, Set[Node]]:
        """
        Return of variables that are written
        :return:
        """
        return self._written

    @property
    def reads_prior_calls(self) -> Dict[Node, Set[Variable]]:
        """
        Return the dictionary node -> variables read before any call
        :return:
        """
        return self._reads_prior_calls

    @property
    def events(self) -> Dict[EventCall, Set[Node]]:
        """
        Return the list of events
        :return:
        """
        return self._events

    def merge_fathers(self, node, skip_father, detector):
        for father in node.fathers:
            if detector.KEY in father.context:
                self._send_eth = union_dict(
                    self._send_eth,
                    {
                        key: values
                        for key, values in father.context[detector.KEY].send_eth.items()
                        if key != skip_father
                    },
                )
                self._calls = union_dict(
                    self._calls,
                    {
                        key: values
                        for key, values in father.context[detector.KEY].calls.items()
                        if key != skip_father
                    },
                )
                self._reads = union_dict(self._reads, father.context[detector.KEY].reads)
                self._reads_prior_calls = union_dict(
                    self.reads_prior_calls, father.context[detector.KEY].reads_prior_calls,
                )

    def analyze_node(self, node, detector):
        state_vars_read: Dict[Variable, Set[Node]] = defaultdict(
            set, {v: {node} for v in node.state_variables_read}
        )

        # All the state variables written
        state_vars_written: Dict[Variable, Set[Node]] = defaultdict(
            set, {v: {node} for v in node.state_variables_written}
        )
        slithir_operations = []
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                for internal_node in internal_call.all_nodes():
                    for read in internal_node.state_variables_read:
                        state_vars_read[read].add(internal_node)
                    for write in internal_node.state_variables_written:
                        state_vars_written[write].add(internal_node)
                slithir_operations += internal_call.all_slithir_operations()

        contains_call = False

        self._written = state_vars_written
        for ir in node.irs + slithir_operations:
            if detector.can_callback(ir):
                self._calls[node] |= {ir.node}
                self._reads_prior_calls[node] = set(
                    self._reads_prior_calls.get(node, set())
                    | set(node.context[detector.KEY].reads.keys())
                    | set(state_vars_read.keys())
                )
                contains_call = True

            if detector.can_send_eth(ir):
                self._send_eth[node] |= {ir.node}

            if isinstance(ir, EventCall):
                self._events[ir] |= {ir.node, node}

        self._reads = union_dict(self._reads, state_vars_read)

        return contains_call

    def add(self, fathers):
        self._send_eth = union_dict(self._send_eth, fathers.send_eth)
        self._calls = union_dict(self._calls, fathers.calls)
        self._reads = union_dict(self._reads, fathers.reads)
        self._reads_prior_calls = union_dict(self._reads_prior_calls, fathers.reads_prior_calls)

    def does_not_bring_new_info(self, new_info):
        if is_subset(new_info.calls, self.calls):
            if is_subset(new_info.send_eth, self.send_eth):
                if is_subset(new_info.reads, self.reads):
                    if dict_are_equal(new_info.reads_prior_calls, self.reads_prior_calls):
                        return True
        return False


def _filter_if(node):
    """
    Check if the node is a condtional node where
    there is an external call checked
    Heuristic:
        - The call is a IF node
        - It contains a, external call
        - The condition is the negation (!)

    This will work only on naive implementation
    """
    return (
        isinstance(node.expression, UnaryOperation)
        and node.expression.type == UnaryOperationType.BANG
    )


class Reentrancy(AbstractDetector):
    KEY = "REENTRANCY"

    # can_callback and can_send_eth are static method
    # allowing inherited classes to define different behaviors
    # For example reentrancy_no_gas consider Send and Transfer as reentrant functions
    @staticmethod
    def can_callback(ir):
        """
        Detect if the node contains a call that can
        be used to re-entrance

        Consider as valid target:
        - low level call
        - high level call


        """
        return isinstance(ir, Call) and ir.can_reenter()

    @staticmethod
    def can_send_eth(ir):
        """
        Detect if the node can send eth
        """
        return isinstance(ir, Call) and ir.can_send_eth()

    def _explore(self, node, visited, skip_father=None):
        """
        Explore the CFG and look for re-entrancy
        Heuristic: There is a re-entrancy if a state variable is written
                    after an external call

        node.context will contains the external calls executed
        It contains the calls executed in father nodes

        if node.context is not empty, and variables are written, a re-entrancy is possible
        """
        if node in visited:
            return

        visited = visited + [node]

        fathers_context = AbstractState()
        fathers_context.merge_fathers(node, skip_father, self)

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if self.visited_all_paths[node].does_not_bring_new_info(fathers_context):
                return
        else:
            self.visited_all_paths[node] = AbstractState()

        self.visited_all_paths[node].add(fathers_context)

        node.context[self.KEY] = fathers_context

        contains_call = fathers_context.analyze_node(node, self)
        node.context[self.KEY] = fathers_context

        sons = node.sons
        if contains_call and node.type in [NodeType.IF, NodeType.IFLOOP]:
            if _filter_if(node):
                son = sons[0]
                self._explore(son, visited, node)
                sons = sons[1:]
            else:
                son = sons[1]
                self._explore(son, visited, node)
                sons = [sons[0]]

        for son in sons:
            self._explore(son, visited)

    def detect_reentrancy(self, contract):
        for function in contract.functions_and_modifiers_declared:
            if function.is_implemented:
                if self.KEY in function.context:
                    continue
                self._explore(function.entry_point, [])
                function.context[self.KEY] = True

    def _detect(self):
        """"""
        # if a node was already visited by another path
        # we will only explore it if the traversal brings
        # new variables written
        # This speedup the exploration through a light fixpoint
        # Its particular useful on 'complex' functions with several loops and conditions
        self.visited_all_paths = {}  # pylint: disable=attribute-defined-outside-init

        for c in self.contracts:
            self.detect_reentrancy(c)

        return []
