"""
    Module detecting uninitialized storage variables

    Recursively explore the CFG to only report uninitialized storage variables that are
    written before being read
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class UninitializedStorageVars(AbstractDetector):
    """
    """

    ARGUMENT = 'uninitialized-storage'
    HELP = 'Uninitialized storage variables'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#uninitialized-storage-variables'

    WIKI_TITLE = 'Uninitialized storage variables'
    WIKI_DESCRIPTION = 'An uinitialized storage variable will act as a reference to the first state variable, and can override a critical variable.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Uninitialized{
    address owner = msg.sender;

    struct St{
        uint a;
    }

    function func() {
        St st;
        st.a = 0x0;
    }
}
```
Bob calls `func`. As a result, `owner` is override to 0.
'''

    WIKI_RECOMMENDATION = 'Initialize all the storage variables.'

    # node.context[self.key] contains the uninitialized storage variables
    key = "UNINITIALIZEDSTORAGE"

    def _detect_uninitialized(self, function, node, visited):
        if node in visited:
            return

        visited = visited + [node]

        fathers_context = []

        for father in node.fathers:
            if self.key in father.context:
                fathers_context += father.context[self.key]

        # Exclude paths that dont bring further information
        if node in self.visited_all_paths:
            if all(f_c in self.visited_all_paths[node] for f_c in fathers_context):
                return
        else:
            self.visited_all_paths[node] = []

        self.visited_all_paths[node] = list(set(self.visited_all_paths[node] + fathers_context))

        if self.key in node.context:
            fathers_context += node.context[self.key]

        variables_read = node.variables_read
        for uninitialized_storage_variable in fathers_context:
            if uninitialized_storage_variable in variables_read:
                self.results.append((function, uninitialized_storage_variable))

        # Only save the storage variables that are not yet written
        uninitialized_storage_variables = list(set(fathers_context) - set(node.variables_written))
        node.context[self.key] = uninitialized_storage_variables

        for son in node.sons:
            self._detect_uninitialized(function, son, visited)


    def _detect(self):
        """ Detect uninitialized storage variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(storage variable uninitialized)
        """
        results = []

        self.results = []
        self.visited_all_paths = {}

        for contract in self.slither.contracts:
            for function in contract.functions:
                if function.is_implemented:
                    uninitialized_storage_variables = [v for v in function.local_variables if v.is_storage and v.uninitialized]
                    function.entry_point.context[self.key] = uninitialized_storage_variables
                    self._detect_uninitialized(function, function.entry_point, [])

        for(function, uninitialized_storage_variable) in self.results:
            info = [uninitialized_storage_variable, " is a storage variable never initialiazed\n"]
            json = self.generate_result(info)
            results.append(json)

        return results
