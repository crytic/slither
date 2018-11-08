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

from slither.analyses.dataflow.generic import explore

KEY = 'REENTRANCY'

def merge_fathers(node):
    # First we add the external calls executed in previous nodes
    # send_eth returns the list of calls sending value
    # calls returns the list of calls that can callback
    # read returns the variable read
    fathers_values = {'send_eth':[], 'calls':[], 'read':[]}

    for father in node.fathers:
        if KEY in father.context:
            fathers_values['send_eth'] += father.values[KEY]['send_eth']
            fathers_values['calls'] += father.values[KEY]['calls']
            fathers_values['read'] += father.values[KEY]['read']

    fathers_values['send_eth'] = list(set(father.values[KEY]['send_eth']))
    fathers_values['calls'] = list(set(father.values[KEY]['calls']))
    fathers_values['read'] = list(set(father.values[KEY]['read']))
    return fathers_values

def visited_all_paths(node):
    return node.slither.context[KEY]['visited_all_paths']

def is_fix_point(node, values):
    # Exclude path that dont bring further information
    if node in visited_all_paths(node):
        if all(call in visited_all_paths(node)[node]['visited_all_paths']['calls'] for call in fathers_context['calls']):
            if all(send in visited_all_paths(node)[node]['send_eth'] for send in fathers_context['send_eth']):
                if all(read in visited_all_paths(node)[node]['read'] for read in fathers_context['read']):
                    return True
    return False

def contains_call(ir):
    return isinstance(ir, LowLevelCall) or (isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall))

def contains_send(ir):
    if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
        if ir.call_value:
            return True
    return False

def transfer_function_ir(ir, values):
    if contains_call(ir):
        values['calls'] = list(set(values['calls'] + [node]))
    if contains_send(ir):
        values['send_eth'] = list(set(values['send_eth'] + [node]))

#    if isinstance(ir, InternalCall):
#        values['calls'] = list(set(values['calls'] + i

def transfer_function_pre_node(node, values):
    values['read'] = list(set(values['read'] + node.state_variables_read))

def transfer_function_post_node(node, values):
    return values

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

def explore_sons(node, visited):
    sons = node.sons
    contains_call = any(contains_call(ir) for ir in node.irs)
    if contains_call and _check_on_call_returned(node):
        sons = sons[1:]

    for son in sons:
        explore(son, visited)



class Reentrancy(AbstractDetector):
    ARGUMENT = 'reentrancy'
    HELP = 'Reentrancy vulnerabilities'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities'


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
#        if node in visited:
#            return
#
#        visited = visited + [node]
#
#
#        else:
#            self.visited_all_paths[node] = {'send_eth':[], 'calls':[], 'read':[]}
#
#        self.visited_all_paths[node]['send_eth'] = list(set(self.visited_all_paths[node]['send_eth'] + fathers_context['send_eth']))
#        self.visited_all_paths[node]['calls'] = list(set(self.visited_all_paths[node]['calls'] + fathers_context['calls']))
#        self.visited_all_paths[node]['read'] = list(set(self.visited_all_paths[node]['read'] + fathers_context['read']))
#
#        node.context[KEY] = fathers_context

#        contains_call = False
#        if self._can_callback(node):
#            node.context[KEY]['calls'] = list(set(node.context[KEY]['calls'] + [node]))
#            contains_call = True
#        if self._can_send_eth(node):
#            node.context[KEY]['send_eth'] = list(set(node.context[KEY]['send_eth'] + [node]))


#        # All the state variables written
#        state_vars_written = node.state_variables_written
#        # Add the state variables written in internal calls
#        for internal_call in node.internal_calls:
#            # Filter to Function, as internal_call can be a solidity call
#            if isinstance(internal_call, Function):
#                state_vars_written += internal_call.all_state_variables_written()

#        read_then_written = [(v, node.source_mapping_str) for v in state_vars_written if v in node.context[KEY]['read']]

#        node.context[KEY]['read'] = list(set(node.context[KEY]['read'] + node.state_variables_read))
        # If a state variables was read and is then written, there is a dangerous call and
        # ether were sent
        # We found a potential re-entrancy bug
        if (read_then_written and
                node.context[KEY]['calls'] and
                node.context[KEY]['send_eth']):
            # calls are ordered
            finding_key = (node.function,
                           tuple(set(node.context[KEY]['calls'])),
                           tuple(set(node.context[KEY]['send_eth'])))
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

        for (func, calls, send_eth), varsWritten in self.result.items():
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
