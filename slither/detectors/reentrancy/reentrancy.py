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
                                        LibraryCall,
                                        Send, Transfer)

class Reentrancy(AbstractDetector):
    ARGUMENT = 'reentrancy'
    HELP = 'Reentrancy vulnerabilities'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities'

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
            if isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
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
        if node in self.visited_all_paths:
            if all(call in self.visited_all_paths[node]['calls'] for call in fathers_context['calls']):
                if all(send in self.visited_all_paths[node]['send_eth'] for send in fathers_context['send_eth']):
                    if all(read in self.visited_all_paths[node]['read'] for read in fathers_context['read']):
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

        read_then_written = [(v, node) for v in state_vars_written if v in node.context[self.key]['read']]

        node.context[self.key]['read'] = list(set(node.context[self.key]['read'] + node.state_variables_read))
        # If a state variables was read and is then written, there is a dangerous call and
        # ether were sent
        # We found a potential re-entrancy bug
        if (read_then_written and
                node.context[self.key]['calls'] and
                node.context[self.key]['send_eth']):
            # calls are ordered
            finding_key = (node.function,
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

        result_sorted = sorted(list(self.result.items()), key=lambda x:x[0][0].name)
        for (func, calls, send_eth), varsWritten in result_sorted:
            calls = list(set(calls))
            send_eth = list(set(send_eth))
#            if calls == send_eth:
#                calls_info = 'Call: {},'.format(calls_str)
#            else:
#                calls_info = 'Call: {}, Ether sent: {},'.format(calls_str, send_eth_str)
            info = 'Reentrancy in {}.{} ({}):\n'
            info = info.format(func.contract.name, func.name, func.source_mapping_str)
            info += '\tExternal calls:\n'
            for call_info in calls:
                info += '\t- {} ({})\n'.format(call_info.expression, call_info.source_mapping_str)
            if calls != send_eth:
                info += '\tExternal calls sending eth:\n'
                for call_info in send_eth:
                    info += '\t- {} ({})\n'.format(call_info.expression, call_info.source_mapping_str)
            info += '\tState variables written after the call(s):\n'
            for (v, node) in varsWritten:
                info +=  '\t- {} ({})\n'.format(v, node.source_mapping_str)
            self.log(info)

            sending_eth_json = []
            if calls != send_eth:
                sending_eth_json = [{'type' : 'external_calls_sending_eth',
                                     'expression': str(call_info.expression),
                                     'source_mapping': call_info.source_mapping}
                                    for call_info in calls]

            json = self.generate_json_result(info)
            self.add_function_to_json(func, json)
            json['elements'] += [{'type': 'external_calls',
                                  'expression': str(call_info.expression),
                                  'source_mapping': call_info.source_mapping}
                                 for call_info in calls]
            json['elements'] += sending_eth_json
            json['elements'] += [{'type':'variables_written',
                                   'name': v.name,
                                   'expression': str(node.expression),
                                   'source_mapping': node.source_mapping}
                                  for (v, node) in varsWritten]
            results.append(json)

        return results
