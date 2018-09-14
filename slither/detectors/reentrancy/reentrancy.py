""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""

from slither.core.declarations.function import Function
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.visitors.expression.export_values import ExportValues


class Reentrancy(AbstractDetector):
    ARGUMENT = 'reentrancy'
    HELP = 'Re-entrancy'
    # High impact 
    # Medium confidence
    CLASSIFICATION = DetectorClassification.HIGH

    @staticmethod
    def _is_legit_call(call_name):
        """
            Detect if the call seems legit
            Slither has no taint analysis, and do not make yet the link
            to the libraries. As a result, we look for any low-level calls
        """
        call_str = str(call_name)
        return not ('.call(' in call_str or
                    '.call.' in call_str or
                    'delegatecall' in call_str or
                    'callcode' in call_str or
                    '.value(' in call_str)

    key = 'REENTRANCY'

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
        if node.type == NodeType.IF:
            external_calls = node.external_calls
            if any(not self._is_legit_call(call) for call in external_calls):
                return isinstance(node.expression, UnaryOperation)\
                       and node.expression.type == UnaryOperationType.BANG
        return False

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
        node.context[self.key] = []

        fathers_context = []

        for father in node.fathers:
            if self.key in father.context:
                fathers_context += father.context[self.key]

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if all(f_c in self.visited_all_paths[node] for f_c in fathers_context):
                return
        else:
            self.visited_all_paths[node] = []

        self.visited_all_paths[node] = list(set(self.visited_all_paths[node] + fathers_context))

        node.context[self.key] = fathers_context

        # Get all the new external calls
        for call in node.external_calls:
            if self._is_legit_call(call):
                continue
            node.context[self.key] += [str(call)]

        # All the state variables written
        state_vars_written = node.state_variables_written
        # Add the state variables written in internal calls
        for internal_call in node.internal_calls:
            # Filter to Function, as internal_call can be a solidity call
            if isinstance(internal_call, Function):
                state_vars_written += internal_call.all_state_variables_written()


        # If a state variables is written, and there was an external call
        # We found a potential re-entrancy bug
        if state_vars_written and node.context[self.key]:
            # we save the result wth (contract, func, calls) as key
            # calls are ordered
            finding_key = (node.function.contract.name,
                           node.function.full_name,
                           tuple(set(node.context[self.key])))
            finding_vars = state_vars_written
            if finding_key not in self.result:
                self.result[finding_key] = []
            self.result[finding_key] = list(set(self.result[finding_key] + finding_vars))

        sons = node.sons
        if self._check_on_call_returned(node):
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

        for (contract, func, calls), varsWritten in self.result.items():
            varsWritten_str = list(set([str(x) for x in list(varsWritten)]))
            calls = list(set([str(x) for x in list(calls)]))
            info = 'Reentrancy in %s, Contract: %s, ' % (self.filename, contract) + \
                   'Func: %s, Call: %s, ' % (func, calls) + \
                   'Vars Written:%s' % (str(varsWritten_str))
            self.log(info)

            source = [v.source_mapping for v in varsWritten]
            # The source mapping could be kept during the analysis
            # So we sould not have to re-iterate over the contracts and functions
            contract_instance = self.slither.get_contract_from_name(contract)
            function_instance = contract_instance.get_function_from_signature(func)
            source += [function_instance.source_mapping]

            results.append({'vuln': 'Reentrancy',
                            'sourceMapping': source,
                            'filename': self.filename,
                            'contract': contract,
                            'function_name': func,
                            'call': calls,
                            'varsWritten': varsWritten_str})

        return results
