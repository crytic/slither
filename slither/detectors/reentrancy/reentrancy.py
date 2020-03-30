""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""
from typing import Set, Dict

from slither.core.cfg.node import NodeType, Node
from slither.core.declarations import Function
from slither.core.expressions import UnaryOperation, UnaryOperationType
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import Call, EventCall, Operation


def union_dict(d1, d2):
    d3 = {k: d1.get(k, set()) | d2.get(k, set()) for k in set(list(d1.keys()) + list(d2.keys()))}
    return d3


def dict_are_equal(d1, d2):
    if set(list(d1.keys())) != set(list(d2.keys())):
        return False
    return all(set(d1[k]) == set(d2[k]) for k in d1.keys())



class AbstractState:
    KEY = 'REENTRANCY'

    def __init__(self):
        # send_eth returns the list of calls sending value
        # calls returns the list of calls that can callback
        # read returns the variable read
        # read_prior_calls returns the variable read prior a call
        self._send_eth: Set[Call] = set()
        self._calls: Set[Call] = set()
        self._reads: Set[Variable] = set()
        self._reads_prior_calls: Dict[Node, Set[Variable]] = dict()
        self._events: Set[EventCall] = set()
        self._written: Set[Variable] = set()

    @property
    def send_eth(self) -> Set[Call]:
        """
        Return the list of calls sending value
        :return:
        """
        return self._send_eth

    @property
    def calls(self) -> Set[Call]:
        """
        Return the list of calls that can callback
        :return:
        """
        return self._calls

    @property
    def reads(self) -> Set[Variable]:
        """
        Return of variables that are read
        :return:
        """
        return self._reads

    @property
    def written(self) -> Set[Variable]:
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
    def events(self) -> Set[EventCall]:
        """
        Return the list of events
        :return:
        """
        return self._events

    def merge_fathers(self, node, skip_father):
        for father in node.fathers:
            if self.KEY in father.context:
                self._send_eth |= set([s for s in father.context[self.KEY].send_eth if s != skip_father])
                self._calls |= set([c for c in father.context[self.KEY].calls if c != skip_father])
                self._reads |= set(father.context[self.KEY].reads)
                self._reads_prior_calls = union_dict(self.reads_prior_calls,
                                                     father.context[self.KEY].reads_prior_calls)

    def analyze_node(self, node, detector):
        state_vars_read = set(node.state_variables_read)

        # All the state variables written
        state_vars_written = set(node.state_variables_written)
        slithir_operations = []
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                state_vars_written |= set(internal_call.all_state_variables_written())
                state_vars_read |= set(internal_call.all_state_variables_read())
                slithir_operations += internal_call.all_slithir_operations()

        contains_call = False

        self._written = set(state_vars_written)
        if detector._can_callback(node.irs + slithir_operations):
            self._calls |= {node}
            self._reads_prior_calls[node] = set(self._reads_prior_calls.get(node, set()) |
                                                node.context[self.KEY].reads |
                                                state_vars_read)
            contains_call = True
        if detector._can_send_eth(node.irs + slithir_operations):
            self._send_eth |= {node}

        self._reads |= state_vars_read

        self._events = set([ir for ir in node.irs if isinstance(ir, EventCall)])

        return contains_call

    def add(self, fathers):
        self._send_eth |= fathers.send_eth
        self._calls |= fathers.calls
        self._reads |= fathers.reads
        self._reads_prior_calls = union_dict(self._reads_prior_calls, fathers.reads_prior_calls)

def does_not_bring_new_info(new_info: AbstractState, old_info: AbstractState) -> bool:
    if new_info.calls.issubset(old_info.calls):
        if new_info.send_eth.issubset(old_info.send_eth):
            if new_info.reads.issubset(old_info.reads):
                if dict_are_equal(new_info.reads_prior_calls,
                                  old_info.reads_prior_calls):
                    return True
    return False


class Reentrancy(AbstractDetector):
    KEY = 'REENTRANCY'

    # can_callback and can_send_eth are static method
    # allowing inherited classes to define different behaviors
    # For example reentrancy_no_gas consider Send and Transfer as reentrant functions
    @staticmethod
    def _can_callback(irs):
        """
            Detect if the node contains a call that can
            be used to re-entrance

            Consider as valid target:
            - low level call
            - high level call


        """
        for ir in irs:
            if isinstance(ir, Call) and ir.can_reenter():
                return True
        return False

    @staticmethod
    def _can_send_eth(irs):
        """
            Detect if the node can send eth
        """
        for ir in irs:
            if isinstance(ir, Call) and ir.can_send_eth():
                return True
        return False

    def _filter_if(self, node):
        """
            Check if the node is a condtional node where
            there is an external call checked
            Heuristic:
                - The call is a IF node
                - It contains a, external call
                - The condition is the negation (!)

            This will work only on naive implementation
        """
        return isinstance(node.expression, UnaryOperation) and node.expression.type == UnaryOperationType.BANG

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

        # First we add the external calls executed in previous nodes
        # send_eth returns the list of calls sending value
        # calls returns the list of calls that can callback
        # read returns the variable read
        # read_prior_calls returns the variable read prior a call
        fathers_context = AbstractState() #{'send_eth': set(), 'calls': set(), 'read': set(), 'read_prior_calls': {}}

        fathers_context.merge_fathers(node, skip_father)
        # for father in node.fathers:
        #     if self.KEY in father.context:
        #         fathers_context['send_eth'] |= set(
        #             [s for s in father.context[self.KEY]['send_eth'] if s != skip_father])
        #         fathers_context['calls'] |= set([c for c in father.context[self.KEY]['calls'] if c != skip_father])
        #         fathers_context['read'] |= set(father.context[self.KEY]['read'])
        #         fathers_context['read_prior_calls'] = union_dict(fathers_context['read_prior_calls'],
        #                                                          father.context[self.KEY]['read_prior_calls'])

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if does_not_bring_new_info(fathers_context, self.visited_all_paths[node]):
                return
        # if node in self.visited_all_paths:
        #     if fathers_context['calls'].issubset(self.visited_all_paths[node]['calls']):
        #         if fathers_context['send_eth'].issubset(self.visited_all_paths[node]['send_eth']):
        #             if fathers_context['read'].issubset(self.visited_all_paths[node]['read']):
        #                 if dict_are_equal(self.visited_all_paths[node]['read_prior_calls'],
        #                                   fathers_context['read_prior_calls']):
        #                     return
        else:
            self.visited_all_paths[node] = AbstractState()
            # self.visited_all_paths[node] = {'send_eth': set(), 'calls': set(), 'read': set(),
            #                                 'read_prior_calls': {}, 'events': set()}


        self.visited_all_paths[node].add(fathers_context)

        node.context[self.KEY] = fathers_context

        contains_call = fathers_context.analyze_node(node, self)
        node.context[self.KEY] = fathers_context

        # state_vars_read = set(node.state_variables_read)
        #
        # # All the state variables written
        # state_vars_written = set(node.state_variables_written)
        # slithir_operations = []
        # # Add the state variables written in internal calls
        # for internal_call in node.internal_calls:
        #     # Filter to Function, as internal_call can be a solidity call
        #     if isinstance(internal_call, Function):
        #         state_vars_written |= set(internal_call.all_state_variables_written())
        #         state_vars_read |= set(internal_call.all_state_variables_read())
        #         slithir_operations += internal_call.all_slithir_operations()
        #
        # contains_call = False
        # node.context[self.KEY]['written'] = set(state_vars_written)
        # if _can_callback(node.irs + slithir_operations):
        #     node.context[self.KEY]['calls'] |= {node}
        #     node.context[self.KEY]['read_prior_calls'][node] = set(
        #         node.context[self.KEY]['read_prior_calls'].get(node, set()) | node.context[self.KEY][
        #             'read'] | state_vars_read)
        #     contains_call = True
        # if _can_send_eth(node.irs + slithir_operations):
        #     node.context[self.KEY]['send_eth'] |= {node}
        #
        # node.context[self.KEY]['read'] |= state_vars_read
        #
        # node.context[self.KEY]['events'] = set([ir for ir in node.irs if isinstance(ir, EventCall)])

        sons = node.sons
        if contains_call and node.type in [NodeType.IF, NodeType.IFLOOP]:
            if self._filter_if(node):
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
        """
        """
        for function in contract.functions_and_modifiers_declared:
            if function.is_implemented:
                if self.KEY in function.context:
                    continue
                self._explore(function.entry_point, [])
                function.context[self.KEY] = True

    def _detect(self):
        """
        """
        # if a node was already visited by another path
        # we will only explore it if the traversal brings
        # new variables written
        # This speedup the exploration through a light fixpoint
        # Its particular useful on 'complex' functions with several loops and conditions
        self.visited_all_paths = {}

        for c in self.contracts:
            self.detect_reentrancy(c)

        return []
