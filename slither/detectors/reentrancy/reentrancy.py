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
from slither.slithir.operations import (HighLevelCall, LowLevelCall,
                                        LibraryCall,
                                        Send, Transfer)

from slither.analyses.dataflow.generic import Dataflow


class ReentrancyDataflow(Dataflow):

    KEY = 'REENTRANCY'
    def __init__(self):
        self._visited_all_paths = {}
        self._result = {}

    def _merge_fathers(self, node):
        # First we add the external calls executed in previous nodes
        # send_eth returns the list of calls sending value
        # calls returns the list of calls that can callback
        # read returns the variable read
        fathers_values = {'send_eth':[], 'calls':[], 'read':[]}

        for father in node.fathers:
            if self.KEY in father.context:
                fathers_values['send_eth'] += father.context[self.KEY]['send_eth']
                fathers_values['calls'] += father.context[self.KEY]['calls']
                fathers_values['read'] += father.context[self.KEY]['read']

        fathers_values['send_eth'] = list(set(fathers_values['send_eth']))
        fathers_values['calls'] = list(set(fathers_values['calls']))
        fathers_values['read'] = list(set(fathers_values['read']))
        return fathers_values


    def _is_fix_point(self, node, values):
        # Exclude path that dont bring further information
        if node in self._visited_all_paths:
            if all(call in self._visited_all_paths[node]['calls'] for call in values['calls']):
                if all(send in self._visited_all_paths[node]['send_eth'] for send in values['send_eth']):
                    if all(read in self._visited_all_paths[node]['read'] for read in values['read']):
                        return True
        return False

    def _store_values(self, node, values):

        if not node in self._visited_all_paths:
            self._visited_all_paths[node] = {'send_eth':[], 'calls':[], 'read':[]}
        self._visited_all_paths[node]['send_eth'] = list(set(self._visited_all_paths[node]['send_eth'] + values['send_eth']))
        self._visited_all_paths[node]['calls'] = list(set(self._visited_all_paths[node]['calls'] + values['calls']))
        self._visited_all_paths[node]['read'] = list(set(self._visited_all_paths[node]['read'] + values['read']))

    @staticmethod
    def _contains_call(ir):
        return isinstance(ir, LowLevelCall) or (isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall))

    @staticmethod
    def _contains_send(ir):
        if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
            if ir.call_value:
                return True
        return False

    def _transfer_function(self, node, values):
        for ir in node.irs:
            if self._contains_call(ir):
                values['calls'] = list(set(values['calls'] + [ir.node]))
            if self._contains_send(ir):
                values['send_eth'] = list(set(values['send_eth'] + [ir.node]))
        node.context[self.KEY] = values

        # All the state variables written
        state_vars_written = node.state_variables_written
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                state_vars_written += internal_call.all_state_variables_written()

        read_then_written = [(v, node.source_mapping_str) for v in state_vars_written if v in values['read']]

        # Add read valures after read_then_written, to not consider variables read within the node
        values['read'] = list(set(values['read'] + node.state_variables_read))

        # If a state variables was read and is then written, there is a dangerous call and
        # ether were sent
        # We found a potential re-entrancy bug
        if (read_then_written and
                values['calls'] and
                values['send_eth']):
            # calls are ordered
            finding_key = (node.function,
                           tuple(set(values['calls'])),
                           tuple(set(values['send_eth'])))
            finding_vars = read_then_written
            if finding_key not in self._result:
                self._result[finding_key] = []
            self._result[finding_key] = list(set(self._result[finding_key] + finding_vars))

        return values

    @staticmethod
    def _check_on_call_returned(node):
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

    def _filter_sons(self, node):
        sons = node.sons
        contains_call = any(self._contains_call(ir) for ir in node.irs)
        if contains_call and self._check_on_call_returned(node):
            sons = sons[1:]
        return sons

    def _update_result(self, node, values):
        pass

    @property
    def result(self):
        return [(func, calls, send_eth, var_written) for ((func, calls, send_eth), var_written) in self._result.items()]

class Reentrancy(AbstractDetector):
    ARGUMENT = 'reentrancy'
    HELP = 'Reentrancy vulnerabilities'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities'

    def detect_reentrancy(self, contract):
        """
        """
        results = []
        for function in contract.functions:
            if function.contract != contract:
                continue
            if function.is_implemented:
                dataflow = ReentrancyDataflow()
                dataflow.explore(function.entry_point, [])
                result = dataflow.result
                if result:
                    results = results + result
        return results

    def detect(self):
        """
        """
        results = []
        for c in self.contracts:
            for (func, calls, send_eth, varsWritten) in self.detect_reentrancy(c):
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
                for (v, mapping) in varsWritten:
                    info +=  '\t- {} ({})\n'.format(v, mapping)
                self.log(info)

                source = [v.source_mapping for (v,_) in varsWritten]
                source += [node.source_mapping for node in calls]
                source += [node.source_mapping for node in send_eth]

                results.append({'vuln': 'Reentrancy',
                                'sourceMapping': source,
                                'filename': self.filename,
                                'contract': func.contract.name,
                                'function': func.name,
                                'calls': [str(x.expression) for x in calls],
                                'send_eth': [str(x.expression) for x in send_eth],
                                'varsWritten': [str(x) for (x,_) in varsWritten]})

        return results
