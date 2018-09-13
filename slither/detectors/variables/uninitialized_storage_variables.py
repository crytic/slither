"""
    Module detecting state uninitialized variables
    Recursively check the called functions

    The heuristic chekcs that:
    - state variables are read or called
    - the variables does not call push (avoid too many FP)

    Only analyze "leaf" contracts (contracts that are not inherited by another contract)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

from slither.visitors.expression.findPush import FindPush


class UninitializedStorageVars(AbstractDetector):
    """
    """

    ARGUMENT = 'uninitialized-storage'
    HELP = 'Uninitialized storage variables'
    CLASSIFICATION = DetectorClassification.HIGH


    key = "UNINITIALIZEDSTORAGE"

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
        for uninitialized_storage_variable in fathers_context:
            if uninitialized_storage_variable in variables_read:
                self.results.append((function, uninitialized_storage_variable))

        # Only save the storage variables that are not yet written
        uninitialized_storage_variables = list(set(fathers_context) - set(node.variables_written))
        node.context[self.key] = uninitialized_storage_variables

        for son in node.sons:
            self._detect_uninitialized(function, son, visited)


    def detect(self):
        """ Detect uninitialized state variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(state variable uninitialized)
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
            var_name = uninitialized_storage_variable.name

            info = "Uninitialized storage variables in %s, " % self.filename + \
                   "Contract: %s, Function: %s, Variable %s" % (function.contract.name,
                                                                function.name,
                                                                var_name)
            self.log(info)

            source = [function.source_mapping, uninitialized_storage_variable.source_mapping]

            results.append({'vuln': 'UninitializedStorageVars',
                            'sourceMapping': source,
                            'filename': self.filename,
                            'contract': function.contract.name,
                            'function': function.name,
                            'variable': var_name})

        return results
