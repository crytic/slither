"""
    Module detecting uninitialized local variables

    Recursively explore the CFG to only report uninitialized local variables that are
    read before being written
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
from slither.visitors.expression.find_push import FindPush


class UninitializedLocalVars(AbstractDetector):
    """
    """

    ARGUMENT = 'uninitialized-local'
    HELP = 'Uninitialized local variables'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-local-variables'


    WIKI_TITLE = 'Uninitialized local variables'
    WIKI_DESCRIPTION = 'Uninitialized local variables.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Uninitialized is Owner{
    function withdraw() payable public onlyOwner{
        address to;
        to.transfer(this.balance)
    }
}
```
Bob calls `transfer`. As a result, the ethers are sent to the address 0x0 and are lost.'''

    WIKI_RECOMMENDATION = 'Initialize all the variables. If a variable is meant to be initialized to zero, explicitly set it to zero.'

    key = "UNINITIALIZEDLOCAL"

    def _detect_uninitialized(self, function, node, visited):
        if node in visited:
            return

        visited = visited + [node]

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

        if self.key in node.context:
            fathers_context += node.context[self.key]

        variables_read = node.variables_read
        for uninitialized_local_variable in fathers_context:
            if uninitialized_local_variable in variables_read:
                self.results.append((function, uninitialized_local_variable))

        # Only save the local variables that are not yet written
        uninitialized_local_variables = list(set(fathers_context) - set(node.variables_written))
        node.context[self.key] = uninitialized_local_variables

        for son in node.sons:
            self._detect_uninitialized(function, son, visited)


    def _detect(self):
        """ Detect uninitialized local variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(local variable uninitialized)
        """
        results = []

        self.results = []
        self.visited_all_paths = {}

        for contract in self.slither.contracts:
            for function in contract.functions:
                if function.is_implemented and function.contract == contract:
                    if function.contains_assembly:
                        continue
                    # dont consider storage variable, as they are detected by another detector
                    uninitialized_local_variables = [v for v in function.local_variables if not v.is_storage and v.uninitialized]
                    function.entry_point.context[self.key] = uninitialized_local_variables
                    self._detect_uninitialized(function, function.entry_point, [])
        all_results = list(set(self.results))
        for(function, uninitialized_local_variable) in all_results:
            var_name = uninitialized_local_variable.name

            info = "{} in {}.{} ({}) is a local variable never initialiazed\n"
            info = info.format(var_name,
                               function.contract.name,
                               function.name,
                               uninitialized_local_variable.source_mapping_str)


            json = self.generate_json_result(info)
            self.add_variable_to_json(uninitialized_local_variable, json)
            self.add_function_to_json(function, json)
            results.append(json)

        return results
