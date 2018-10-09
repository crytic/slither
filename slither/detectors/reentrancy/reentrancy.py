""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""

from slither.core.cfg.node import NodeType
from slither.core.declarations import Function, SolidityFunction
from slither.core.expressions import UnaryOperation, UnaryOperationType
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.visitors.expression.export_values import ExportValues
from slither.slithir.operations import (HighLevelCall, LowLevelCall,
                                        Send, Transfer)

class Reentrancy(AbstractDetector):
    ARGUMENT = 'reentrancy'
    HELP = 'reentrancy vulnerabilities'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    key = 'REENTRANCY'

    @staticmethod
    def _can_callback(node):
        """
            Detect if the node contains a call that can
            be used to re-entrance

            Consider as valid target:
            - low level call
            - high level call

            Do not consider Send/Transfer as there is not enough gas
        """
        for ir in node.irs:
            if isinstance(ir, LowLevelCall):
                return True
            if isinstance(ir, HighLevelCall):
                return True
        return False

    @staticmethod
    def _can_send_eth(node):
        """
            Detect if the node can send eth
        """
        for ir in node.irs:
            if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
                if ir.call_value:
                    return True
        return False

    def _check_on_call_returned(self, node):
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

    def _explore(self, node, visited):
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
        fathers_context = {'send_eth':[], 'calls':[], 'read':[]}

        for father in node.fathers:
            if self.key in father.context:
                fathers_context['send_eth'] += father.context[self.key]['send_eth']
                fathers_context['calls'] += father.context[self.key]['calls']
                fathers_context['read'] += father.context[self.key]['read']

        # Exclude path that dont bring further information
        if self.key in self.visited_all_paths:
            if all(f_c['calls'] in self.visited_all_paths[node]['calls'] for f_c in fathers_context):
                if all(f_c['send_eth'] in self.visited_all_paths[node]['send_eth'] for f_c in fathers_context):
                    if all(f_c['read'] in self.visited_all_paths[node]['read'] for f_c in fathers_context):
                        return
        else:
            self.visited_all_paths[node] = {'send_eth':[], 'calls':[], 'read':[]}

        self.visited_all_paths[node]['send_eth'] = list(set(self.visited_all_paths[node]['send_eth'] + fathers_context['send_eth']))
        self.visited_all_paths[node]['calls'] = list(set(self.visited_all_paths[node]['calls'] + fathers_context['calls']))
        self.visited_all_paths[node]['read'] = list(set(self.visited_all_paths[node]['read'] + fathers_context['read']))

        node.context[self.key] = fathers_context

        contains_call = False
        if self._can_callback(node):
            node.context[self.key]['calls'] = list(set(node.context[self.key]['calls'] + [node]))
            contains_call = True
        if self._can_send_eth(node):
            node.context[self.key]['send_eth'] = list(set(node.context[self.key]['send_eth'] + [node]))


        # All the state variables written
        state_vars_written = node.state_variables_written
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                state_vars_written += internal_call.all_state_variables_written()

        read_then_written = [v for v in state_vars_written if v in node.context[self.key]['read']]

        node.context[self.key]['read'] = list(set(node.context[self.key]['read'] + node.state_variables_read))
        # If a state variables was read and is then written, there is a dangerous call and
        # ether were sent
        # We found a potential re-entrancy bug
        if (read_then_written and
                node.context[self.key]['calls'] and
                node.context[self.key]['send_eth']):
            # calls are ordered
            finding_key = (node.function.contract.name,
                           node.function.full_name,
                           tuple(set(node.context[self.key]['calls'])),
                           tuple(set(node.context[self.key]['send_eth'])))
            finding_vars = read_then_written
            if finding_key not in self.result:
                self.result[finding_key] = []
            self.result[finding_key] = list(set(self.result[finding_key] + finding_vars))

        sons = node.sons
        if contains_call and self._check_on_call_returned(node):
            sons = sons[1:]

        for son in sons:
            self._explore(son, visited)

    def detect_reentrancy(self, contract):
        """
        """
        for function in contract.functions:
            if function.is_implemented:
                self._explore(function.entry_point, [])

    def detect(self):
        """
        """
        self.result = {}

        # if a node was already visited by another path
        # we will only explore it if the traversal brings
        # new variables written
        # This speedup the exploration through a light fixpoint
        # Its particular useful on 'complex' functions with several loops and conditions
        self.visited_all_paths = {}

        for c in self.contracts:
            self.detect_reentrancy(c)

        results = []

        for (contract, func, calls, send_eth), varsWritten in self.result.items():
            varsWritten_str = list(set([str(x) for x in list(varsWritten)]))
            calls_str = list(set([str(x.expression) for x in list(calls)]))
            send_eth_str = list(set([str(x.expression) for x in list(send_eth)]))

            if calls == send_eth:
                call_info = 'Call: {},'.format(calls_str)
            else:
                call_info = 'Call: {}, Ether sent: {},'.format(calls_str, send_eth_str)
            info = 'Reentrancy in {}, Contract: {}, '.format(self.filename, contract) + \
                   'Func: {}, '.format(func) + \
                   '{}'.format(call_info) + \
                   'Vars Written: {}'.format(str(varsWritten_str))
            self.log(info)

            source = [v.source_mapping for v in varsWritten]
            source += [node.source_mapping for node in calls]
            source += [node.source_mapping for node in send_eth]

            results.append({'vuln': 'Reentrancy',
                            'sourceMapping': source,
                            'filename': self.filename,
                            'contract': contract,
                            'function_name': func,
                            'calls': calls_str,
                            'send_eth': send_eth_str,
                            'varsWritten': varsWritten_str})

        return results
