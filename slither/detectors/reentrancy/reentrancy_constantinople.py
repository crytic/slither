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
                                        LibraryCall, Index, Balance, NewContract,
                                        Send, Transfer, OperationWithLValue)

from slither.core.variables.state_variable import StateVariable
from slither.slithir.variables import ReferenceVariable
from slither.analyses.data_dependency.data_dependency import is_tainted

class ReentrancyConstantinople(AbstractDetector):
    ARGUMENT = 'reentrancy-sstore'
    HELP = 'Reentrancy vulnerabilities (constantinople)'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#reentrancy-vulnerabilities'

    key = 'REENTRANCY-ETHERS'

    @staticmethod
    def _can_callback(node):
        """
            Detect if the node contains a call that can
            be used to re-entrance

            Consider as valid target Send and Transfer operations

            Do not consider Send/Transfer as there is not enough gas
        """
        for ir in node.irs:
            if isinstance(ir, (Send, Transfer)):
                if is_tainted(ir.destination, node.function.contract, node.function.slither, True):
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
        # calls returns the list of calls that can callback
        # read returns the variable read
        fathers_context = {'calls':[], 'read':[], 'read_prior_calls':[]}

        for father in node.fathers:
            if self.key in father.context:
                fathers_context['calls'] += [c for c in father.context[self.key]['calls'] if c!=skip_father]
                fathers_context['read'] += father.context[self.key]['read']
                fathers_context['read_prior_calls'] += father.context[self.key]['read_prior_calls']

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if all(call in self.visited_all_paths[node]['calls'] for call in fathers_context['calls']):
                if all(read in self.visited_all_paths[node]['read'] for read in fathers_context['read']):
                    if all(read in self.visited_all_paths[node]['read_prior_calls'] for read in fathers_context['read_prior_calls']):
                        return
        else:
            self.visited_all_paths[node] = {'calls':[], 'read':[], 'read_prior_calls':[]}

        self.visited_all_paths[node]['calls'] = list(set(self.visited_all_paths[node]['calls'] + fathers_context['calls']))
        self.visited_all_paths[node]['read'] = list(set(self.visited_all_paths[node]['read'] + fathers_context['read']))
        self.visited_all_paths[node]['read_prior_calls'] = list(set(self.visited_all_paths[node]['read_prior_calls'] + fathers_context['read_prior_calls']))

        node.context[self.key] = fathers_context

        state_vars_read = node.state_variables_read

        # All the state variables written
        state_vars_written = node.state_variables_written
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                state_vars_written += internal_call.all_state_variables_written()
                state_vars_read += internal_call.all_state_variables_read()

        contains_call = False
        if self._can_callback(node):
            node.context[self.key]['calls'] = list(set(node.context[self.key]['calls'] + [node]))

            node.context[self.key]['read_prior_calls'] = list(set(node.context[self.key]['read_prior_calls'] + node.context[self.key]['read'] + state_vars_read))
            node.context[self.key]['read'] = []
            contains_call = True

        read_then_written = [(v, node) for v in state_vars_written + state_vars_read if v in self.variables_written and v in node.context[self.key]['read_prior_calls']]

        node.context[self.key]['read'] = list(set(node.context[self.key]['read'] + state_vars_read))
        # If a state variables was read and is then written, there is a dangerous call and
        # ether were sent
        # We found a potential re-entrancy bug
        if (read_then_written and node.context[self.key]['calls']):
            # calls are ordered
            finding_key = (node.function,
                           tuple(set(node.context[self.key]['calls'])),
                           tuple(set(node.context[self.key]['calls'])))
            finding_vars = read_then_written
            if finding_key not in self.result:
                self.result[finding_key] = []
            self.result[finding_key] = list(set(self.result[finding_key] + finding_vars))

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
        for function in contract.functions:
            if function.is_implemented:
                self._explore(function.entry_point, [])

    @staticmethod
    def filter(function):
        gas_cost = 0
        if not function.visibility in ['public', 'external']:
            return False
        if function.is_protected():
            return False
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, NewContract):
                    return False
                if isinstance(ir, Index):
                    continue
                if isinstance(ir, OperationWithLValue):
                    lvalue = ir.lvalue
                    if isinstance(lvalue, ReferenceVariable):
                        lvalue = lvalue.points_to_origin
                    if isinstance(lvalue, StateVariable):
                        gas_cost += 200
                if isinstance(ir, (LowLevelCall, Send, Transfer, HighLevelCall)):
                    return False
                  #  gas_cost += 700
                if isinstance(ir, (Balance)):
                    gas_cost += 400
                for read in ir.read:
                    if isinstance(read, ReferenceVariable):
                        read = read.points_to_origin
                    if isinstance(read, StateVariable):
                        gas_cost += 200
        return gas_cost < 1600

    def _get_variables_written_by_other_functions(self, contract):
        all_functions = contract.all_functions_called
    

        self.map_var_to_func = {}
        variables_written = []
        for function in all_functions:
            if self.filter(function):
                var = function.state_variables_written
                if var:
                    for v in var:
                        if not v in self.map_var_to_func:
                            self.map_var_to_func[v] = []
                        self.map_var_to_func[v].append(function)
                    variables_written += var
        self.variables_written = list(set(variables_written))
        
    def detect(self):
        """
        """
        self.result = {}

        self.variables_written = []

        # if a node was already visited by another path
        # we will only explore it if the traversal brings
        # new variables written
        # This speedup the exploration through a light fixpoint
        # Its particular useful on 'complex' functions with several loops and conditions
        self.visited_all_paths = {}

        for c in self.contracts:
            self._get_variables_written_by_other_functions(c)
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

            info += '\tState variables read/written after the call(s):\n'
            for (v, node) in varsWritten:
                if v in self.map_var_to_func:
                    info +=  '\t- {} ({}) ({})\n'.format(v, node.source_mapping_str, ','.join([source.name for source in self.map_var_to_func[v]]))
            self.log(info)

            sending_eth_json = []
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
