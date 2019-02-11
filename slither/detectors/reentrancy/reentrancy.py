""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""

from slither.core.cfg.node import NodeType
from slither.core.declarations import Function, SolidityFunction, SolidityVariable
from slither.core.expressions import UnaryOperation, UnaryOperationType
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, LowLevelCall,
                                        LibraryCall,
                                        Send, Transfer)
from slither.core.variables.variable import Variable

def union_dict(d1, d2):
    d3 = {k: d1.get(k, set()) | d2.get(k, set()) for k in set(list(d1.keys()) + list(d2.keys()))}
    return d3

def dict_are_equal(d1, d2):
    if set(list(d1.keys())) != set(list(d2.keys())):
        return False
    return all(set(d1[k]) == set(d2[k]) for k in d1.keys())

class Reentrancy(AbstractDetector):
# This detector is not meant to be registered
# It is inherited by reentrancy variantsœ
#    ARGUMENT = 'reentrancy'
#    HELP = 'Reentrancy vulnerabilities'
#    IMPACT = DetectorClassification.HIGH
#    CONFIDENCE = DetectorClassification.HIGH

    KEY = 'REENTRANCY'

    def _can_callback(self, irs):
        """
            Detect if the node contains a call that can
            be used to re-entrance

            Consider as valid target:
            - low level call
            - high level call

            Do not consider Send/Transfer as there is not enough gas
        """
        for ir in irs:
            if isinstance(ir, LowLevelCall):
                return True
            if isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
                # If solidity >0.5, STATICCALL is used
                if self.slither.solc_version and self.slither.solc_version.startswith('0.5.'):
                    if isinstance(ir.function, Function) and (ir.function.view or ir.function.pure):
                        continue
                    if isinstance(ir.function, Variable):
                        continue
                # If there is a call to itself
                # We can check that the function called is
                # reentrancy-safe
                if ir.destination == SolidityVariable('this'):
                    if not ir.function.all_high_level_calls():
                        if not ir.function.all_low_level_calls():
                            continue
                return True
        return False

    @staticmethod
    def _can_send_eth(irs):
        """
            Detect if the node can send eth
        """
        for ir in irs:
            if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
                if ir.call_value:
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
        return isinstance(node.expression, UnaryOperation)\
            and node.expression.type == UnaryOperationType.BANG

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
        fathers_context = {'send_eth':set(), 'calls':set(), 'read':set(), 'read_prior_calls':{}}

        for father in node.fathers:
            if self.KEY in father.context:
                fathers_context['send_eth'] |= set([s for s in father.context[self.KEY]['send_eth'] if s!=skip_father])
                fathers_context['calls'] |= set([c for c in father.context[self.KEY]['calls'] if c!=skip_father])
                fathers_context['read'] |= set(father.context[self.KEY]['read'])
                fathers_context['read_prior_calls'] = union_dict(fathers_context['read_prior_calls'], father.context[self.KEY]['read_prior_calls'])

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if all(call in self.visited_all_paths[node]['calls'] for call in fathers_context['calls']):
                if all(send in self.visited_all_paths[node]['send_eth'] for send in fathers_context['send_eth']):
                    if all(read in self.visited_all_paths[node]['read'] for read in fathers_context['read']):
                        if dict_are_equal(self.visited_all_paths[node]['read_prior_calls'], fathers_context['read_prior_calls']):
                            return
        else:
            self.visited_all_paths[node] = {'send_eth':set(), 'calls':set(), 'read':set(), 'read_prior_calls':{}}

        self.visited_all_paths[node]['send_eth'] = set(self.visited_all_paths[node]['send_eth'] | fathers_context['send_eth'])
        self.visited_all_paths[node]['calls'] = set(self.visited_all_paths[node]['calls'] | fathers_context['calls'])
        self.visited_all_paths[node]['read'] = set(self.visited_all_paths[node]['read'] | fathers_context['read'])
        self.visited_all_paths[node]['read_prior_calls'] = union_dict(self.visited_all_paths[node]['read_prior_calls'], fathers_context['read_prior_calls'])

        node.context[self.KEY] = fathers_context

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
        node.context[self.KEY]['written'] = set(state_vars_written)
        if self._can_callback(node.irs + slithir_operations):
            node.context[self.KEY]['calls'] = set(node.context[self.KEY]['calls'] | {node})
            node.context[self.KEY]['read_prior_calls'][node] = set(node.context[self.KEY]['read_prior_calls'].get(node, set()) | node.context[self.KEY]['read'] |state_vars_read)
            contains_call = True
        if self._can_send_eth(node.irs + slithir_operations):
            node.context[self.KEY]['send_eth'] = set(node.context[self.KEY]['send_eth'] | {node})

        node.context[self.KEY]['read'] = set(node.context[self.KEY]['read'] | state_vars_read)

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
        for function in contract.functions_and_modifiers_not_inherited:
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
